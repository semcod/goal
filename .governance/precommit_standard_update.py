#!/usr/bin/env python3
"""Delegate pre-commit standard freshness to Goal's trusted adopter."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


DIAGNOSTIC = "GOV-STANDARD-UPDATE-001"
MANAGED_LOCK = ".governance/manifest.lock.json"
DEFAULT_UPDATE_POLICY = {
    "enabled": True,
    "trigger": "pre-commit",
    "action": "prepare-and-abort",
    "executor": "goal",
}


def _refuse(message: str, *, returncode: int = 2) -> int:
    print(f"{DIAGNOSTIC}: {message}", file=sys.stderr)
    print(
        "  Install compatible Goal or repair the active standard-adoption "
        "ticket; never bypass the hook.",
        file=sys.stderr,
    )
    return returncode


def _staged_blobs(target: Path, paths: list[str]) -> dict[str, bytes] | None:
    """Read the exact staged content of several paths in one Git process.

    A commit is judged on what is staged, never on the worktree. A repository
    can carry close to a hundred managed files and this runs on every commit,
    so the reads are batched instead of one ``git show`` per entry.
    """
    request = "".join(f":{path}\n" for path in paths).encode("utf-8")
    try:
        completed = subprocess.run(
            ["git", "-C", str(target), "cat-file", "--batch"],
            input=request, capture_output=True, check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    staged: dict[str, bytes] = {}
    stream, offset = completed.stdout, 0
    for path in paths:
        end = stream.find(b"\n", offset)
        if end < 0:
            return None
        header = stream[offset:end].decode("utf-8", "replace").split()
        if len(header) != 3 or not header[2].isdigit():
            # "<object> missing": the path is absent from the index entirely.
            offset = end + 1
            continue
        size = int(header[2])
        staged[path] = stream[end + 1:end + 1 + size]
        offset = end + 1 + size + 1
    return staged


def staged_managed_drift(target: Path) -> tuple[str, ...] | None:
    """Report which standard-managed files this commit would leave inconsistent.

    Staleness and drift are different facts. Staleness means the world moved:
    a newer standard revision was published. Drift means this repository moved:
    a managed file no longer matches the digest recorded in its own pinned
    lock. Only drift is this repository's doing, and only drift is something a
    commit can cause or repair.

    Returns the drifted paths, an empty tuple when the staged tree is
    internally consistent with its own pin, or ``None`` when the answer cannot
    be established — and an unestablished answer never relaxes anything.
    """
    lock = _staged_blobs(target, [MANAGED_LOCK])
    if not lock or MANAGED_LOCK not in lock:
        return None
    try:
        managed = json.loads(lock[MANAGED_LOCK].decode("utf-8"))["managedFiles"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(managed, dict) or not managed:
        return None
    paths = sorted(managed)
    staged = _staged_blobs(target, paths)
    if staged is None:
        return None
    drifted = []
    for path in paths:
        digest, content = managed[path], staged.get(path)
        if content is None or not isinstance(digest, str):
            drifted.append(path)
        elif hashlib.sha256(content).hexdigest() != digest:
            drifted.append(path)
    return tuple(drifted)


def _load_update_policy(path: Path) -> dict[str, object]:
    try:
        adoption = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("standard-adoption.json is unreadable or invalid") from error
    if not isinstance(adoption, dict):
        raise ValueError("standard-adoption.json must contain an object")
    updates = adoption.get("updates")
    if updates is None:
        return dict(DEFAULT_UPDATE_POLICY)
    if not isinstance(updates, dict) or set(updates) != set(DEFAULT_UPDATE_POLICY):
        raise ValueError("standard update policy has missing or unknown fields")
    if (
        not isinstance(updates.get("enabled"), bool)
        or updates.get("trigger") != "pre-commit"
        or updates.get("action") != "prepare-and-abort"
        or updates.get("executor") not in {"goal", "koru-goal"}
    ):
        raise ValueError("standard update policy contains unsupported values")
    return updates


def run(
    root: Path,
    ticket: str,
    *,
    goal_executable: str = "goal",
    koru_executable: str = "koru",
) -> int:
    """Run the Goal-owned protocol when this repository has a standard pin."""
    target = root.resolve()
    adoption_path = target / ".governance" / "standard-adoption.json"
    if not adoption_path.is_file():
        return 0
    try:
        policy = _load_update_policy(adoption_path)
    except ValueError as error:
        return _refuse(str(error))
    if not policy["enabled"]:
        return 0

    goal = shutil.which(goal_executable)
    if goal is None:
        return _refuse("Goal is unavailable, so standard freshness cannot be verified")
    goal_arguments = [
        "governance",
        "adopt",
        "--latest",
        "--pre-commit",
        "--target-root",
        str(target),
        "--ticket",
        ticket,
    ]
    if policy["executor"] == "koru-goal":
        koru = shutil.which(koru_executable)
        if koru is None:
            return _refuse(
                "Koru is the configured standard update executor but is unavailable"
            )
        command = [
            koru,
            "goal",
            "--project",
            str(target),
            "--goal-executable",
            goal,
            "--",
            *goal_arguments,
        ]
    else:
        command = [goal, *goal_arguments]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError:
        return _refuse("Goal could not execute the standard update protocol")
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(
            completed.stderr,
            end="" if completed.stderr.endswith("\n") else "\n",
            file=sys.stderr,
        )
    if completed.returncode != 0:
        if _staleness_only(completed, target):
            print(
                f"{DIAGNOSTIC}: the pinned standard is behind the published "
                "revision, but no managed file drifted in this commit; "
                "adopt the new revision in a governance ticket.",
                file=sys.stderr,
            )
            return 0
        return _refuse(
            "Goal refused or prepared a standard update; review its evidence before retrying",
            returncode=completed.returncode,
        )
    return 0


def _staleness_only(
    completed: subprocess.CompletedProcess[str], target: Path,
) -> bool:
    """Decide whether Goal's refusal is staleness that this commit cannot fix.

    Goal refuses a stale pin unless the committing ticket is itself a
    governance adoption ticket binding the exact old and new revisions. An
    implementation ticket can never be that, so on a standard that publishes
    several revisions a day the gate stops every unrelated commit in the
    repository for a reason none of those commits caused. Measured on
    2026-09-08: seven published revisions in one day, and five pull-request
    repairs in one adopter blocked for a full day with zero drift.

    Both conditions must hold before the commit proceeds: Goal's own stable
    diagnostic identifies the refusal as adoption authorization, and the staged
    tree still matches every digest its pinned lock records. Any other refusal
    keeps the commit closed, and so does drift or evidence that cannot be read
    at all — an unestablished answer never relaxes the gate.
    """
    if DIAGNOSTIC not in f"{completed.stderr or ''}\n{completed.stdout or ''}":
        return False
    return staged_managed_drift(target) == ()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--goal-executable", default="goal")
    parser.add_argument("--koru-executable", default="koru")
    args = parser.parse_args()
    return run(
        args.root,
        args.ticket,
        goal_executable=args.goal_executable,
        koru_executable=args.koru_executable,
    )


if __name__ == "__main__":
    raise SystemExit(main())
