#!/usr/bin/env python3
"""Derive a repository's required-checks declaration from its own workflows.

Every adopter currently ships the hub's copy verbatim: repository
`wellmanifest/new-project`, workflowFile `.github/workflows/ci.yml`, checks
`test` and `windows-governance`. Twenty of them do not have that workflow at
all, so the declared single source of truth for check names is false almost
everywhere, and `GOV-SYNC-001` blocks adoption until it is corrected by hand.

The truth is already in the repository: the job names its pull-request
workflows publish. This derives the declaration from them.

Read-only unless --write is given.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "new-project.required-checks/v1"
JOB_LINE = re.compile(r"^  ([A-Za-z0-9][A-Za-z0-9_-]*):\s*(?:#.*)?$")
JOB_NAME_LINE = re.compile(r"^    name:\s*(.+?)\s*$")
TOP_LEVEL_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:")
REUSABLE_CALL = re.compile(r"^    uses:\s*\S+/\S+/\.github/workflows/")
DECLARATION_CANDIDATES = (
    Path(".governance/required-checks.json"),
    Path("governance/required-checks.json"),
)
IGNORED_FIELD = "circularGovernanceChecksIgnoredByValidator"
HUB_REPOSITORY = "wellmanifest/new-project"


def scalar(raw: str) -> str:
    value = raw.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        return value[1:-1]
    return value


def published_checks_text(text: str, callers: list[str]) -> list[str]:
    """Job display names, mirroring how GitHub names a check context.

    A job that calls a reusable workflow is collected into ``callers`` instead of
    the returned names: it publishes one context per job of the called workflow,
    named "<caller> / <callee job>", and the callee lives in another repository.
    """
    if "pull_request" not in text:
        return []  # A workflow that never runs on a PR cannot gate one.
    names: list[str] = []
    current: str | None = None
    calls_reusable = False
    in_jobs = False

    def flush() -> None:
        if current is None:
            return
        (callers if calls_reusable else names).append(current)

    for line in text.splitlines():
        if TOP_LEVEL_KEY.match(line):
            # Only the jobs mapping publishes check contexts; on:, env: and the
            # rest use the same two-space indentation for their own keys.
            flush()
            current, calls_reusable = None, False
            in_jobs = line.startswith("jobs:")
            continue
        if not in_jobs:
            continue
        job = JOB_LINE.match(line)
        if job:
            flush()
            current, calls_reusable = job.group(1), False
            continue
        if current is None:
            continue
        display = JOB_NAME_LINE.match(line)
        if display:
            current = scalar(display.group(1))
            continue
        if REUSABLE_CALL.match(line):
            calls_reusable = True
    flush()
    return names


def published_checks(workflow: Path, callers: list[str]) -> list[str]:
    return published_checks_text(workflow.read_text(encoding="utf-8"), callers)


def repository_name(root: Path) -> str | None:
    try:
        url = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=False, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


def declaration_for(
    root: Path,
    ignored: tuple[str, ...] = (),
    workflow_payloads: dict[str, bytes] | None = None,
) -> dict[str, Any] | None:
    repository = repository_name(root)
    if repository is None:
        return None
    directory = root / ".github/workflows"
    overlays = workflow_payloads or {}
    workflows: dict[str, tuple[Path, bytes | None]] = {}
    if directory.is_dir():
        for workflow in sorted(directory.glob("*.y*ml")):
            relative = workflow.relative_to(root).as_posix()
            workflows[relative] = (workflow, None)
    for relative, content in overlays.items():
        if not relative.startswith(".github/workflows/") or not relative.endswith((".yml", ".yaml")):
            continue
        workflows[relative] = (root / relative, content)
    if not workflows:
        return None
    checks: list[dict[str, str]] = []
    callers: list[str] = []
    for relative, (workflow, content) in sorted(workflows.items()):
        names = (
            published_checks_text(content.decode("utf-8"), callers)
            if content is not None
            else published_checks(workflow, callers)
        )
        for name in names:
            checks.append({"name": name, "workflowFile": relative})
    if not checks and not callers:
        return None
    document: dict[str, Any] = {
        "schema": SCHEMA,
        "version": 1,
        "repository": repository,
        "requiredChecks": checks,
    }
    if callers:
        document["reusableWorkflowCallers"] = sorted(set(callers))
    return document


def declaration_path(root: Path) -> Path:
    """The hub keeps its instance in governance/, adopters in .governance/."""
    for candidate in DECLARATION_CANDIDATES:
        if (root / candidate).is_file():
            return root / candidate
    return root / DECLARATION_CANDIDATES[0]


def current_declaration(root: Path) -> dict[str, Any] | None:
    path = declaration_path(root)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def declared_names(document: dict[str, Any] | None) -> list[str]:
    if not document:
        return []
    names = document.get("requiredCheckNames")
    if names is None:
        names = [item.get("name") for item in document.get("requiredChecks", [])]
    return sorted(str(name) for name in names or [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", help="Repository roots to inspect")
    parser.add_argument("--write", action="store_true", help="Rewrite each declaration in place")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv or sys.argv[1:])

    report: list[dict[str, Any]] = []
    for raw in args.roots:
        root = Path(raw).resolve()
        current = current_declaration(root)
        inherited_hub_declaration = (current or {}).get("repository") == HUB_REPOSITORY
        ignored = () if inherited_hub_declaration else tuple((current or {}).get(IGNORED_FIELD, ()) or ())
        derived = declaration_for(root)
        if derived is not None and ignored:
            derived[IGNORED_FIELD] = list(ignored)
        entry = {
            "repository": root.name,
            "derived": derived,
            "currentRepository": (current or {}).get("repository"),
            "currentNames": declared_names(current),
            "derivedNames": declared_names(derived),
        }
        entry["agrees"] = (
            derived is not None
            and entry["currentRepository"] == derived["repository"]
            and entry["currentNames"] == entry["derivedNames"]
        )
        entry["reusableWorkflowCallers"] = (derived or {}).get("reusableWorkflowCallers", [])
        if args.write and derived is not None and not entry["agrees"]:
            if entry["reusableWorkflowCallers"]:
                entry["written"] = False  # A caller's context name cannot be derived here.
            else:
                declaration_path(root).write_text(
                    json.dumps(derived, indent=2) + "\n", encoding="utf-8"
                )
                entry["written"] = True
        report.append(entry)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        for entry in report:
            state = "agrees" if entry["agrees"] else "DIFFERS"
            print(f"{entry['repository']:<24} {state}")
            if not entry["agrees"]:
                print(f"  declared {entry['currentRepository']} {entry['currentNames']}")
                derived_repo = (entry["derived"] or {}).get("repository")
                print(f"  derived  {derived_repo} {entry['derivedNames']}")
                if entry["reusableWorkflowCallers"]:
                    print(
                        "  callers  "
                        f"{entry['reusableWorkflowCallers']} publish "
                        "<caller> / <callee job>; confirm those names by hand"
                    )
        print(f"\n{sum(1 for e in report if e['agrees'])} of {len(report)} agree")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
