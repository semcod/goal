"""Execute a separately trusted, adopted reconciliation checker without mutation.

The expected lock digest must come from the protected caller, never from the
author's report. This boundary verifies integrity, not receipt authenticity or
the completeness of the caller's criterion inventory.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import click


CHECKER = ".governance/branch_intent_reconciliation.py"
LOCK = ".governance/manifest.lock.json"
OUTCOMES = {0: "ready-for-owner-review", 1: "needs-review", 2: "invalid"}


class BranchIntentError(click.ClickException):
    """Invalid preflight or execution is distinct from unresolved criteria."""

    exit_code = 2


def _json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=pairs)


def _regular_file(root, relative):
    path = root
    for component in Path(relative).parts:
        path = path / component
        if path.is_symlink():
            raise ValueError(f"symlinked managed path: {relative}")
    if not path.is_file():
        raise ValueError(
            f"adopted artifact is missing: {relative}; "
            "adopt a published standard package containing branch intent reconciliation"
        )
    return path.read_bytes()


def run_check(target, report, observation, evidence_root, expected_lock_sha256, timeout):
    """Return a checked child result; no path can authorize branch deletion."""
    try:
        root = Path(target).resolve(strict=True)
        if not re.fullmatch(r"[0-9a-f]{64}", expected_lock_sha256):
            raise ValueError("expected lock SHA-256 must be 64 lowercase hex digits")
        lock_bytes = _regular_file(root, LOCK)
        if hashlib.sha256(lock_bytes).hexdigest() != expected_lock_sha256:
            raise ValueError("adoption lock differs from the independently supplied digest")
        lock = _json(lock_bytes)
        standard = lock["standard"]
        if (lock["schema"] != "new-project.lock/v1"
                or standard["id"] != "wellmanifest/new-project"
                or standard["publicationStatus"] != "published"
                or not re.fullmatch(r"[0-9a-f]{40}", standard["sourceRevision"])):
            raise ValueError("published immutable new-project adoption is required")
        expected = lock["managedFiles"].get(CHECKER)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("adopt a published standard package containing branch intent reconciliation")
        code = _regular_file(root, CHECKER)
        if hashlib.sha256(code).hexdigest() != expected:
            raise ValueError("managed reconciliation checker digest mismatch")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        raise BranchIntentError(f"branch intent preflight refused: {error}") from error

    # Execute the bytes just hashed, not a path another process could replace.
    # Isolated Python excludes the target checkout and PYTHONPATH from imports.
    filename = str(root / CHECKER)
    bootstrap = (
        f"import sys; sys.argv[0] = {filename!r}; "
        f"exec(compile(sys.stdin.buffer.read(), {filename!r}, 'exec'), "
        f"{{'__name__': '__main__', '__file__': {filename!r}}})"
    )
    command = [sys.executable, "-I", "-B", "-c", bootstrap,
               "--report", str(Path(report).resolve()),
               "--observation", str(Path(observation).resolve()),
               "--evidence-root", str(Path(evidence_root).resolve())]
    try:
        result = subprocess.run(command, cwd=root, input=code.decode("utf-8"), capture_output=True, text=True,
                                check=False, timeout=timeout)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise BranchIntentError(f"branch intent checker could not complete: {error}") from error
    try:
        payload = _json(result.stdout)
        if (result.returncode not in OUTCOMES
                or payload["status"] != OUTCOMES[result.returncode]
                or payload["authority"] != "none"
                or payload["deletionAuthorized"] is not False):
            raise ValueError("invalid readiness or authority result")
    except (ValueError, TypeError, KeyError) as error:
        raise BranchIntentError(f"branch intent checker returned an invalid result: {error}") from error
    return result
