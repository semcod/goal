#!/usr/bin/env python3
"""Prove that the host-agnostic agent contract is installed, not just documented.

Instruction files are advisory: any model may ignore them. This validator checks
the parts that execute anyway — the fail-closed git hook, and the packaging
lifecycle hooks that `npm install` and `pytest` run without asking the agent.

Hub reads `governance/agent-hosts.json`; adopters read `.governance/agent-hosts.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "new-project.agent-hosts/v1"
CONTRACT_CANDIDATES = ("governance/agent-hosts.json", ".governance/agent-hosts.json")
LOCK_CANDIDATES = ("governance/manifest.lock.json", ".governance/manifest.lock.json")


@dataclass(order=True)
class Finding:
    code: str
    message: str
    remediation: str
    paths: list[str] = field(default_factory=list)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def first_existing(root: Path, candidates: tuple[str, ...]) -> Path | None:
    for candidate in candidates:
        path = root / candidate
        if path.is_file():
            return path
    return None


def git_config(root: Path, key: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", key],
            capture_output=True, text=True, check=False, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def is_work_tree(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def check_hosts(root: Path, contract: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for host in contract["hosts"]:
        relative = str(host["file"])
        if not (root / relative).is_file():
            findings.append(Finding(
                "GOV-AGENT-HOST-004",
                f"Host instruction file for '{host['id']}' is missing: {relative}",
                "Bootstrap with ./scripts/install-agent-hosts.sh --source <hub> --target <repo>, or adopt the current standard package.",
                [relative],
            ))
    return findings


def check_hook(root: Path, contract: dict[str, Any], actor: str) -> list[Finding]:
    findings: list[Finding] = []
    hook_relative = str(contract["hook"]["path"])
    hook_path = root / hook_relative
    if not hook_path.is_file():
        findings.append(Finding(
            "GOV-AGENT-HOST-005",
            f"Fail-closed pre-commit hook is missing: {hook_relative}",
            "Bootstrap with ./scripts/install-agent-hosts.sh --source <hub> --target <repo>, or adopt the current standard package.",
            [hook_relative],
        ))
    elif os.name != "nt" and not hook_path.stat().st_mode & 0o111:
        findings.append(Finding(
            "GOV-AGENT-HOST-005",
            f"Fail-closed pre-commit hook is not executable: {hook_relative}",
            f"Restore the executable bit with chmod +x {hook_relative}.",
            [hook_relative],
        ))

    # A CI checkout never runs local hooks; only a developer or agent clone can.
    if actor == "ci" or not is_work_tree(root):
        return findings
    expected = str(contract["hook"]["hooksPathConfig"])
    configured = git_config(root, "core.hooksPath")
    if configured != expected:
        findings.append(Finding(
            "GOV-AGENT-HOST-006",
            f"core.hooksPath is {configured or 'unset'}; the managed hook is not active.",
            f"Activate the managed hook: git config core.hooksPath {expected} in this clone.",
            [hook_relative],
        ))
    return findings


def adopted_standard(root: Path) -> dict[str, Any]:
    lock_path = first_existing(root, LOCK_CANDIDATES)
    if lock_path is None:
        return {}
    try:
        lock = load_json(lock_path)
    except (OSError, json.JSONDecodeError):
        return {}
    standard = lock.get("standard")
    return standard if isinstance(standard, dict) else {}


def python_declaration(marker: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        document = tomllib.loads(marker.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None, {}
    declaration = document.get("tool", {}).get("wellmanifest")
    return (declaration if isinstance(declaration, dict) else None), document


def node_declaration(marker: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        document = load_json(marker)
    except (OSError, json.JSONDecodeError):
        return None, {}
    if not isinstance(document, dict):
        return None, {}
    declaration = document.get("wellmanifest")
    return (declaration if isinstance(declaration, dict) else None), document


def lifecycle_value(kind: str, document: dict[str, Any]) -> str:
    if kind == "npm-script":
        scripts = document.get("scripts")
        value = scripts.get("prepare") if isinstance(scripts, dict) else None
    else:
        options = document.get("tool", {}).get("pytest", {}).get("ini_options", {})
        value = options.get("addopts") if isinstance(options, dict) else None
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return value if isinstance(value, str) else ""


def check_packaging(root: Path, contract: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    standard = adopted_standard(root)
    for ecosystem, binding in sorted(contract["packaging"].items()):
        marker_relative = str(binding["marker"])
        marker = root / marker_relative
        if not marker.is_file():
            continue  # The ecosystem is not present in this repository.
        reader = python_declaration if ecosystem == "python" else node_declaration
        declaration, document = reader(marker)
        if declaration is None:
            findings.append(Finding(
                "GOV-PACKAGING-001",
                f"{marker_relative} declares no '{binding['declaration']}' governance block.",
                "Declare the adopted standard version, revision and gate in the package metadata.",
                [marker_relative],
            ))
        else:
            findings.extend(check_declaration(root, marker_relative, declaration, standard))

        lifecycle = binding["lifecycle"]
        if lifecycle["mustContain"] not in lifecycle_value(str(lifecycle["kind"]), document):
            findings.append(Finding(
                "GOV-PACKAGING-003",
                f"{marker_relative} {lifecycle['field']} does not run '{lifecycle['mustContain']}'.",
                "Bind the governance gate to the packaging lifecycle so the tooling runs it unprompted.",
                [marker_relative],
            ))
    return findings


def check_declaration(
    root: Path,
    marker_relative: str,
    declaration: dict[str, Any],
    standard: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    for key in ("standard", "revision", "gate"):
        if not isinstance(declaration.get(key), str) or not declaration[key].strip():
            findings.append(Finding(
                "GOV-PACKAGING-001",
                f"{marker_relative} governance block is missing the '{key}' field.",
                "Declare the adopted standard version, revision and gate in the package metadata.",
                [marker_relative],
            ))
    if not standard:
        return findings
    for key, locked in (("standard", "version"), ("revision", "sourceRevision")):
        expected = standard.get(locked)
        actual = declaration.get(key)
        if isinstance(expected, str) and isinstance(actual, str) and actual != expected:
            findings.append(Finding(
                "GOV-PACKAGING-002",
                f"{marker_relative} declares {key} '{actual}' but the adoption lock pins '{expected}'.",
                "Regenerate the package declaration from .governance/manifest.lock.json.",
                [marker_relative],
            ))
    gate = declaration.get("gate")
    if isinstance(gate, str) and gate.strip():
        gate_path = root / gate
        if not gate_path.is_file():
            findings.append(Finding(
                "GOV-PACKAGING-002",
                f"{marker_relative} declares gate '{gate}', which does not exist.",
                "Point the declaration at the managed governance gate in this repository.",
                [marker_relative, gate],
            ))
    return findings


def load_contract(root: Path, explicit: str | None) -> tuple[dict[str, Any] | None, Finding | None]:
    if explicit is not None:
        path = root / explicit if not Path(explicit).is_absolute() else Path(explicit)
        if not path.is_file():
            return None, Finding(
                "GOV-AGENT-HOST-004", f"Agent host contract is missing: {explicit}",
                "Adopt the current standard package or pass an existing --contract path.", [explicit],
            )
    else:
        found = first_existing(root, CONTRACT_CANDIDATES)
        if found is None:
            # The repository has not received the managed contract yet, so there
            # is nothing to verify. Deleting it later is not an escape hatch:
            # agent-hosts.json is a managed file and GOV-SYNC-001 catches its
            # removal against the adoption lock.
            return None, None
        path = found
    try:
        contract = load_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return None, Finding(
            "GOV-AGENT-HOST-004", f"Agent host contract is unreadable: {error}",
            "Restore the pinned host contract through a standard upgrade.", [str(path.name)],
        )
    if not isinstance(contract, dict) or contract.get("schema") != SCHEMA:
        return None, Finding(
            "GOV-AGENT-HOST-004", f"Agent host contract must declare schema {SCHEMA}.",
            "Restore the pinned host contract through a standard upgrade.", [str(path.name)],
        )
    for key in ("hook", "hosts", "packaging"):
        if key not in contract:
            return None, Finding(
                "GOV-AGENT-HOST-004", f"Agent host contract has no '{key}' section.",
                "Restore the pinned host contract through a standard upgrade.", [str(path.name)],
            )
    return contract, None


def audit(root: Path, actor: str = "agent", contract_path: str | None = None) -> dict[str, Any]:
    contract, failure = load_contract(root, contract_path)
    if contract is None:
        findings = [failure] if failure is not None else []
    else:
        findings = (
            check_hosts(root, contract)
            + check_hook(root, contract, actor)
            + check_packaging(root, contract)
        )
    findings.sort()
    return {
        "schema": "new-project.agent-host-report/v1",
        "actor": actor,
        "findings": [
            {
                "code": item.code,
                "message": item.message,
                "remediation": item.remediation,
                "paths": item.paths,
            }
            for item in findings
        ],
        "ok": not findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(repo_root()))
    parser.add_argument("--contract", default=None, help="Explicit agent-hosts.json path")
    parser.add_argument(
        "--actor", choices=("agent", "human", "ci"), default="agent",
        help="'ci' skips checks that only a developer or agent clone can satisfy",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv or sys.argv[1:])

    report = audit(Path(args.root).resolve(), args.actor, args.contract)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "GOV-AGENT-HOST-PASS" if report["ok"] else "GOV-AGENT-HOST-FAIL"
        print(f"{status}: {len(report['findings'])} findings")
        for finding in report["findings"]:
            print(f"{finding['code']}: {finding['message']}")
            print(f"  -> {finding['remediation']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
