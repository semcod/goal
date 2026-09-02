#!/usr/bin/env python3
"""Pure planner and validator for wellmanifest.worktrees/v1."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TICKET_RE = re.compile(r"^ticket-([0-9]{3,})$")


def _path_type(style: str):
    if style == "posix":
        return PurePosixPath
    if style == "windows":
        return PureWindowsPath
    raise ValueError("pathStyle must be 'posix' or 'windows'")


def _validate_segment(label: str, value: str) -> None:
    if not NAME_RE.fullmatch(value):
        raise ValueError(f"{label} must contain lowercase ASCII words separated by hyphens")


def plan(
    *,
    repository: str,
    repository_name: str,
    ticket: str,
    slug: str,
    workspace_root: str,
    path_style: str = "posix",
) -> dict[str, str]:
    """Return the one canonical layout record for the supplied delivery unit."""
    _validate_segment("repositoryName", repository_name)
    _validate_segment("slug", slug)
    ticket_match = TICKET_RE.fullmatch(ticket)
    if not ticket_match:
        raise ValueError("ticket must match ticket-NNN with at least three digits")

    path_type = _path_type(path_style)
    root = path_type(workspace_root)
    stem = f"{repository_name}--{ticket}--{slug}"
    worktrees_root = root / ".worktrees"
    return {
        "schema": "wellmanifest.worktrees/v1",
        "kind": "layout-record",
        "repository": repository,
        "repositoryName": repository_name,
        "ticket": ticket,
        "slug": slug,
        "branch": f"ticket/{ticket_match.group(1)}-{slug}",
        "pathStyle": path_style,
        "workspaceRoot": str(root),
        "primaryCheckout": str(root / repository_name),
        "worktreesRoot": str(worktrees_root),
        "worktreePath": str(worktrees_root / stem),
        "leasePath": str(worktrees_root / ".leases" / f"{stem}.json"),
    }


def validate(record: dict[str, Any]) -> list[str]:
    """Return stable error strings; an empty list means the record conforms."""
    required = (
        "repository",
        "repositoryName",
        "ticket",
        "slug",
        "workspaceRoot",
        "pathStyle",
    )
    missing = [name for name in required if not isinstance(record.get(name), str)]
    if missing:
        return [f"missing_or_invalid:{name}" for name in missing]
    try:
        expected = plan(
            repository=record["repository"],
            repository_name=record["repositoryName"],
            ticket=record["ticket"],
            slug=record["slug"],
            workspace_root=record["workspaceRoot"],
            path_style=record["pathStyle"],
        )
    except ValueError as exc:
        return [f"invalid_input:{exc}"]

    errors = []
    for key, expected_value in expected.items():
        if record.get(key) != expected_value:
            errors.append(f"noncanonical:{key}")
    extra = sorted(set(record) - set(expected))
    errors.extend(f"unexpected:{key}" for key in extra)
    return errors


def _read_json(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    planner = subparsers.add_parser("plan")
    planner.add_argument("--repository", required=True)
    planner.add_argument("--repository-name", required=True)
    planner.add_argument("--ticket", required=True)
    planner.add_argument("--slug", required=True)
    planner.add_argument("--workspace-root", required=True)
    planner.add_argument("--path-style", choices=("posix", "windows"), default="posix")
    validator = subparsers.add_parser("validate")
    validator.add_argument("record", help="JSON file or - for stdin")
    args = parser.parse_args()

    if args.command == "plan":
        record = plan(
            repository=args.repository,
            repository_name=args.repository_name,
            ticket=args.ticket,
            slug=args.slug,
            workspace_root=args.workspace_root,
            path_style=args.path_style,
        )
        print(json.dumps(record, indent=2))
        return 0

    errors = validate(_read_json(args.record))
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
