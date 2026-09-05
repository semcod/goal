#!/usr/bin/env python3
"""Resolve reservations through ancestry or verified rewritten Git patches."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[a-f0-9]{40}$")
TICKET_RE = re.compile(r"^ticket-[0-9]{3}$")
RECEIPT_REF_RE = re.compile(r"^receipt:\S+$")
TARGET_BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
OCCURRED_AT_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
REWRITE_VERIFICATION = "git-ancestry-or-rewritten-patch-series"


class ActivityError(RuntimeError):
    code = "GOV-TICKET-ACTIVITY-001"


class ActivityPolicyMissing(ActivityError):
    """The repository predates adoption of the managed activity contract."""


@dataclass(frozen=True)
class ActivityResolution:
    ticket: str
    active: bool
    projectionStatus: str | None
    authority: str
    receiptRef: str | None = None
    reason: str | None = None


def _git(root: Path, *args: str, check: bool = True) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        check=False, timeout=20, env=env,
    )
    if check and result.returncode:
        raise ActivityError((result.stderr or result.stdout).strip() or "Git verification failed")
    return result.stdout.strip() if result.returncode == 0 else ""


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ActivityError(f"invalid activity document {path}: {error}") from error


def policy_path(root: Path) -> Path:
    for candidate in (root / ".governance/ticket-activity.json", root / "governance/ticket-activity.json"):
        if candidate.is_file():
            return candidate
    raise ActivityPolicyMissing("managed ticket activity policy is missing")


def load_policy(root: Path) -> dict[str, Any]:
    value = _load(policy_path(root))
    required = {"$schema", "schema", "registry", "terminalOutcomes", "unsupportedOutcomePolicy"}
    if not isinstance(value, dict) or set(value) != required or value.get("schema") != "new-project.ticket-activity/v1":
        raise ActivityError("managed ticket activity policy has unsupported fields or schema")
    registry = value.get("registry")
    if not isinstance(registry, dict) or set(registry) != {"location", "path", "missingPolicy"}:
        raise ActivityError("managed ticket activity registry declaration is invalid")
    if registry.get("location") != "git-common-dir" or registry.get("missingPolicy") != "status-projection":
        raise ActivityError("managed ticket activity registry policy is unsupported")
    raw_path = registry.get("path")
    if not isinstance(raw_path, str) or not raw_path or Path(raw_path).is_absolute() or ".." in Path(raw_path).parts:
        raise ActivityError("managed terminal receipt registry path is unsafe")
    outcomes = value.get("terminalOutcomes")
    if not isinstance(outcomes, dict) or not outcomes:
        raise ActivityError("managed terminal outcomes are missing")
    supported_verification = {"git-ancestry", REWRITE_VERIFICATION}
    for name, rule in outcomes.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(rule, dict)
            or set(rule) != {"verification", "releasesReservation"}
            or rule.get("verification") not in supported_verification
            or rule.get("releasesReservation") is not True
        ):
            raise ActivityError("managed terminal outcome rule is unsupported")
    if value.get("unsupportedOutcomePolicy") != "remain-active":
        raise ActivityError("unsupported outcome policy must remain-active")
    return value


def registry_path(root: Path, policy: dict[str, Any] | None = None) -> Path:
    selected = policy or load_policy(root)
    raw_common = _git(root, "rev-parse", "--path-format=absolute", "--git-common-dir", check=False)
    # Scaffolder fixtures and pre-init directories cannot possess terminal Git
    # evidence. An absent synthetic location therefore has the same safe result
    # as an absent optional registry: retain the status projection.
    common = Path(raw_common).resolve() if raw_common else (root / ".git").resolve()
    return common / selected["registry"]["path"]


def repository_ref(root: Path) -> str:
    remote = _git(root, "remote", "get-url", "origin", check=False)
    if remote:
        return remote.strip().removesuffix(".git").rstrip("/").lower()
    common = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    return f"local:{common}"


def projection_status(ticket_dir: Path) -> str | None:
    try:
        text = (ticket_dir / "README.md").read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"(?mi)^-[ \t]+\*\*Status\*\*:[ \t]*([A-Z_]+)[ \t]*$", text)
    return match.group(1).upper() if match else None


def _validate_registry(value: Any, expected_repository: str) -> list[dict[str, str]]:
    if not isinstance(value, dict) or set(value) != {"schema", "repositoryRef", "receipts"}:
        raise ActivityError("terminal receipt registry fields are invalid")
    if value.get("schema") != "new-project.terminal-receipt-registry/v1":
        raise ActivityError("terminal receipt registry schema is unsupported")
    if value.get("repositoryRef") != expected_repository:
        raise ActivityError("terminal receipt registry belongs to another repository")
    receipts = value.get("receipts")
    if not isinstance(receipts, list):
        raise ActivityError("terminal receipt registry receipts must be a list")
    seen: set[str] = set()
    for receipt in receipts:
        fields = {"receiptRef", "ticket", "outcome", "headSha", "terminalSha", "targetBranch", "occurredAt"}
        if not isinstance(receipt, dict) or set(receipt) != fields:
            raise ActivityError("terminal receipt fields are invalid")
        if not isinstance(receipt.get("receiptRef"), str) or RECEIPT_REF_RE.fullmatch(receipt["receiptRef"]) is None:
            raise ActivityError("terminal receipt reference is invalid")
        if receipt["receiptRef"] in seen:
            raise ActivityError("terminal receipt references are not unique")
        seen.add(receipt["receiptRef"])
        if not TICKET_RE.fullmatch(receipt.get("ticket", "")):
            raise ActivityError("terminal receipt ticket is invalid")
        if not SHA_RE.fullmatch(receipt.get("headSha", "")) or not SHA_RE.fullmatch(receipt.get("terminalSha", "")):
            raise ActivityError("terminal receipt SHA binding is invalid")
        if not isinstance(receipt.get("outcome"), str) or not receipt["outcome"]:
            raise ActivityError("terminal receipt value is blank")
        if TARGET_BRANCH_RE.fullmatch(receipt.get("targetBranch", "")) is None:
            raise ActivityError("terminal receipt target branch is invalid")
        if OCCURRED_AT_RE.fullmatch(receipt.get("occurredAt", "")) is None:
            raise ActivityError("terminal receipt timestamp is invalid")
    return receipts


def _ancestor(root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", older, newer],
        capture_output=True, check=False, timeout=20,
        env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
    )
    return result.returncode == 0


def _linear_series(root: Path, base: str, head: str) -> list[str] | None:
    """Return the exact single-parent chain from base to head, or fail closed."""
    raw = _git(root, "rev-list", "--reverse", "--ancestry-path", f"{base}..{head}", check=False)
    commits = raw.splitlines() if raw else []
    if not commits:
        return None
    previous = base
    for commit in commits:
        parents = _git(root, "show", "-s", "--format=%P", commit, check=False).split()
        if parents != [previous]:
            return None
        previous = commit
    return commits if previous == head else None


def _stable_patch_id(payload: bytes, env: dict[str, str]) -> str | None:
    """Return Git's stable patch identity for one non-empty diff payload."""
    identified = subprocess.run(
        ["git", "patch-id", "--stable"],
        input=payload,
        capture_output=True,
        check=False,
        timeout=20,
        env=env,
    )
    if identified.returncode:
        return None
    fields = identified.stdout.decode("utf-8", errors="strict").split()
    return fields[0] if len(fields) >= 2 and SHA_RE.fullmatch(fields[0]) else None


def _patch_id(root: Path, commit: str) -> str | None:
    """Return Git's stable patch identity for one non-empty commit."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    shown = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "show",
            "--no-ext-diff",
            "--pretty=format:%H",
            "--binary",
            "--full-index",
            commit,
        ],
        capture_output=True,
        check=False,
        timeout=20,
        env=env,
    )
    if shown.returncode:
        return None
    return _stable_patch_id(shown.stdout, env)


def _range_patch_id(root: Path, base: str, head: str) -> str | None:
    """Return the stable identity of the aggregate tree change in one range."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    diff = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--no-ext-diff",
            "--binary",
            "--full-index",
            base,
            head,
        ],
        capture_output=True,
        check=False,
        timeout=20,
        env=env,
    )
    if diff.returncode:
        return None
    return _stable_patch_id(diff.stdout, env)


def _rebased_patch_series(root: Path, head_sha: str, terminal_sha: str) -> bool:
    """Verify a GitHub-style linear rebase without trusting an asserted method."""
    base = _git(root, "merge-base", head_sha, terminal_sha, check=False)
    if not SHA_RE.fullmatch(base):
        return False
    original = _linear_series(root, base, head_sha)
    if original is None:
        return False
    terminal_base = _git(root, "rev-parse", f"{terminal_sha}~{len(original)}", check=False)
    if not SHA_RE.fullmatch(terminal_base):
        return False
    rebased = _linear_series(root, terminal_base, terminal_sha)
    if rebased is None or len(rebased) != len(original):
        return False
    original_ids = [_patch_id(root, commit) for commit in original]
    rebased_ids = [_patch_id(root, commit) for commit in rebased]
    return None not in original_ids and original_ids == rebased_ids


def _squashed_patch(root: Path, head_sha: str, terminal_sha: str) -> bool:
    """Verify one squash commit against the aggregate protected-head change."""
    base = _git(root, "merge-base", head_sha, terminal_sha, check=False)
    parents = _git(root, "show", "-s", "--format=%P", terminal_sha, check=False).split()
    if not SHA_RE.fullmatch(base) or len(parents) != 1:
        return False
    original_id = _range_patch_id(root, base, head_sha)
    terminal_id = _range_patch_id(root, parents[0], terminal_sha)
    return original_id is not None and original_id == terminal_id


def _rewritten_patch(root: Path, head_sha: str, terminal_sha: str) -> bool:
    return _rebased_patch_series(root, head_sha, terminal_sha) or _squashed_patch(
        root, head_sha, terminal_sha
    )


def _terminal_verified(
    root: Path,
    receipt: dict[str, str],
    rule: dict[str, Any] | None,
    target: str | None,
) -> bool:
    if rule is None or target is None:
        return False
    head_sha, terminal_sha = receipt["headSha"], receipt["terminalSha"]
    if not _ancestor(root, terminal_sha, target):
        return False
    integrated = _ancestor(root, head_sha, terminal_sha)
    if not integrated and rule.get("verification") == REWRITE_VERIFICATION:
        integrated = _rewritten_patch(root, head_sha, terminal_sha)
    return integrated and not _advanced_ticket_branch(
        root, receipt["ticket"], head_sha, terminal_sha
    )


def _target_ref(root: Path, branch: str) -> str | None:
    for ref in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        if _git(root, "rev-parse", "--verify", ref, check=False):
            return ref
    return None


def _advanced_ticket_branch(root: Path, ticket: str, head_sha: str, terminal_sha: str) -> bool:
    branch = _git(root, "branch", "--show-current", check=False)
    number = str(int(ticket.removeprefix("ticket-")))
    if not branch or re.search(rf"(?:^|[^0-9a-z])ticket[-_/]?0*{number}(?:[^0-9]|$)", branch, re.IGNORECASE) is None:
        return False
    current = _git(root, "rev-parse", "HEAD", check=False)
    return bool(current and current != head_sha and _ancestor(root, head_sha, current) and not _ancestor(root, current, terminal_sha))


def resolve(root: Path, ticket_dir: Path, active_statuses: set[str]) -> ActivityResolution:
    root = root.resolve()
    ticket = ticket_dir.name
    status = projection_status(ticket_dir)
    projected_active = status in active_statuses
    if not projected_active:
        return ActivityResolution(ticket, False, status, "status-projection", reason="projection-not-active")
    try:
        policy = load_policy(root)
    except ActivityPolicyMissing:
        return ActivityResolution(ticket, True, status, "status-projection", reason="policy-not-adopted")
    path = registry_path(root, policy)
    if not path.exists():
        return ActivityResolution(ticket, True, status, "status-projection", reason="registry-absent")
    receipts = _validate_registry(_load(path), repository_ref(root))
    matching = [item for item in receipts if item["ticket"] == ticket]
    for receipt in reversed(matching):
        rule = policy["terminalOutcomes"].get(receipt["outcome"])
        if rule is None:
            continue
        target = _target_ref(root, receipt["targetBranch"])
        if not _terminal_verified(root, receipt, rule, target):
            continue
        return ActivityResolution(ticket, False, status, "terminal-receipt", receipt["receiptRef"], "verified-terminal")
    return ActivityResolution(ticket, True, status, "status-projection", reason="no-verifiable-terminal-receipt")


def record(root: Path, receipt: dict[str, str]) -> Path:
    policy = load_policy(root)
    path = registry_path(root, policy)
    current: dict[str, Any]
    if path.exists():
        current = _load(path)
        _validate_registry(current, repository_ref(root))
    else:
        current = {"schema": "new-project.terminal-receipt-registry/v1", "repositoryRef": repository_ref(root), "receipts": []}
    prior = next(
        (item for item in current["receipts"] if item["receiptRef"] == receipt.get("receiptRef")),
        None,
    )
    if prior is not None and prior != receipt:
        raise ActivityError("terminal receipt reference is append-only and already binds different evidence")
    candidate = dict(current)
    candidate["receipts"] = list(current["receipts"])
    if prior is None:
        candidate["receipts"].append(receipt)
    _validate_registry(candidate, repository_ref(root))
    rule = policy["terminalOutcomes"].get(receipt["outcome"])
    target = _target_ref(root, receipt["targetBranch"])
    if not _terminal_verified(root, receipt, rule, target):
        raise ActivityError("receipt does not verify against the managed outcome policy and current Git ancestry")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="terminal-receipts.", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(candidate, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    resolver = sub.add_parser("resolve")
    resolver.add_argument("--ticket-dir", type=Path, required=True)
    resolver.add_argument("--active-status", action="append", required=True)
    sub.add_parser("validate")
    recorder = sub.add_parser("record")
    recorder.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            result = resolve(args.root, args.ticket_dir, set(args.active_status))
            print(json.dumps(asdict(result), sort_keys=True))
            return 0 if result.active else 1
        if args.command == "validate":
            policy = load_policy(args.root)
            path = registry_path(args.root, policy)
            if path.exists():
                _validate_registry(_load(path), repository_ref(args.root))
            print(json.dumps({"status": "valid", "registry": str(path), "present": path.exists()}))
            return 0
        receipt = _load(args.receipt)
        path = record(args.root.resolve(), receipt)
        print(json.dumps({"status": "recorded", "registry": str(path), "receiptRef": receipt["receiptRef"]}))
        return 0
    except ActivityError as error:
        print(f"{error.code}: {error}", file=sys.stderr)
        print("  remediation: reconcile the clone-external registry from protected evidence; see error/GOV-TICKET-ACTIVITY.md", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
