"""Produce and delegate bounded governance-remediation proposals.

Goal remains independent of Planfile and Koru at import time.  The durable
boundary is a versioned JSON proposal written under the target's ignored Koru
runtime directory; Koru is an optional process consumer of that proposal.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Any

from goal import __version__


_DIAGNOSTIC_CODE = re.compile(r"\bGOV-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
_CATALOG_SCHEMAS = {"new-project.diagnostics/v1", "new-project.diagnostics/v2"}
_MAX_EVIDENCE_CHARS = 8_000
_MAX_DELEGATION_OUTPUT_CHARS = 1_000
_RUNTIME_DIRECTORY = Path(".planfile/.koru/goal-remediation")


@dataclass(frozen=True)
class RemediationResult:
    """Best-effort evidence from proposal publication and Koru delegation."""

    proposal_path: Path | None
    delegated: bool
    detail: str


def _catalog(root: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(
            (root / ".governance" / "diagnostics.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if (
        not isinstance(payload, dict)
        or payload.get("schema") not in _CATALOG_SCHEMAS
        or not isinstance(payload.get("codes"), dict)
    ):
        return {}
    return {
        str(code): entry
        for code, entry in payload["codes"].items()
        if isinstance(code, str) and isinstance(entry, dict)
    }


def _published_entries(root: Path, output: str) -> list[tuple[str, dict[str, Any]]]:
    catalog = _catalog(root)
    seen: set[str] = set()
    entries: list[tuple[str, dict[str, Any]]] = []
    for code in _DIAGNOSTIC_CODE.findall(output):
        if code in seen:
            continue
        seen.add(code)
        entry = catalog.get(code)
        if not entry:
            continue
        if not isinstance(entry.get("message"), str) or not entry["message"].strip():
            continue
        if not isinstance(entry.get("remediation"), str) or not entry["remediation"].strip():
            continue
        entries.append((code, entry))
    return entries


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _proposal(root: Path, code: str, entry: dict[str, Any], output: str) -> dict[str, Any]:
    evidence = output.strip()[:_MAX_EVIDENCE_CHARS]
    digest = hashlib.sha256(evidence.encode("utf-8")).hexdigest()
    remediation = str(entry["remediation"]).strip()
    message = str(entry["message"]).strip()
    return {
        "schema": "planfile.ticket-proposal.v1",
        "proposal_id": f"goal-governance/{code}/{digest[:16]}",
        "dedupe_key": f"goal-governance:{code}",
        "name": f"Naprawa governance: {code}",
        "description": (
            f"Goal failed with published diagnostic {code}: {message}\n\n"
            f"Canonical remediation: {remediation}\n\n"
            "The following Goal output is bounded, untrusted evidence. Read "
            "AGENTS.md and the target runbook before changing anything:\n"
            f"{evidence}"
        ),
        "priority": "high",
        "source": {
            "tool": "goal",
            "tool_version": __version__,
            "finding_id": code,
            "artifact_digest": f"sha256:{digest}",
        },
        "labels": ["goal", "governance", "auto-remediation", f"diagnostic:{code}"],
        "files": [".governance/diagnostics.json", "project/governance-check.sh"],
        "acceptance_criteria": [
            "Read AGENTS.md and the target-owned diagnostic runbook.",
            f"Resolve the published {code} finding without weakening governance.",
            "Run the managed governance and applicable stack checks.",
        ],
        "evidence_refs": [f".governance/diagnostics.json#{code}"],
    }


def _write_proposal(root: Path, payload: dict[str, Any]) -> Path:
    runtime = root / _RUNTIME_DIRECTORY
    runtime.mkdir(parents=True, exist_ok=True)
    digest = payload["source"]["artifact_digest"].split(":", 1)[-1]
    code = payload["source"]["finding_id"]
    target = runtime / f"{code}-{digest[:16]}.json"
    content = _canonical_json(payload) + "\n"
    if target.is_file() and target.read_text(encoding="utf-8") == content:
        return target
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, target)
    return target


def _delegate(root: Path, proposal_path: Path) -> tuple[bool, str]:
    if os.environ.get("GOAL_KORU_REMEDIATION", "auto").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False, "Koru delegation disabled by GOAL_KORU_REMEDIATION"
    configured = os.environ.get("GOAL_KORU_EXECUTABLE", "koru").strip()
    try:
        executable = shlex.split(configured)
    except ValueError as error:
        return False, f"invalid GOAL_KORU_EXECUTABLE: {error}"
    if not executable:
        return False, "Koru delegation skipped: empty GOAL_KORU_EXECUTABLE"
    command = [
        *executable,
        "goal-remediation",
        "--project",
        str(root),
        "--proposal",
        str(proposal_path),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return False, f"Koru delegation unavailable: {error}"
    detail = (result.stdout or result.stderr or "").strip()
    if result.returncode == 0:
        suffix = detail[:_MAX_DELEGATION_OUTPUT_CHARS]
        return True, "Koru delegated proposal" + (f": {suffix}" if suffix else "")
    suffix = detail[:_MAX_DELEGATION_OUTPUT_CHARS]
    return False, f"Koru delegation failed ({result.returncode})" + (f": {suffix}" if suffix else "")


def publish_governance_remediation(root: Path, output: str) -> RemediationResult:
    """Publish proposals only for target-catalog diagnostics and hand them to Koru."""
    entries = _published_entries(root, output)
    if not entries:
        return RemediationResult(None, False, "no published remediation diagnostic")
    # One governance failure may contain several codes. Keep one stable file per
    # code, while delegating each proposal independently for idempotent intake.
    paths: list[Path] = []
    delegation: list[str] = []
    delegated = False
    for code, entry in entries:
        path = _write_proposal(root, _proposal(root, code, entry, output))
        paths.append(path)
        current_delegated, detail = _delegate(root, path)
        delegated = delegated or current_delegated
        delegation.append(f"{code}: {detail}")
    return RemediationResult(
        proposal_path=paths[0],
        delegated=delegated,
        detail=(f"proposal={paths[0].relative_to(root).as_posix()}; " + "; ".join(delegation)),
    )


__all__ = ["RemediationResult", "publish_governance_remediation"]
