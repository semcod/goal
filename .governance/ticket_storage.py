#!/usr/bin/env python3
"""Bridge managed ID reservation to a digest-pinned local Registry writer."""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from ticket_input import database_rows, no_links, primary_database, read_file

# Versioned Registry ticket CLI integration: these are its complete relative
# module dependencies. A source update needs a newly acquired independent pin.
RUNTIME_FILES = ("storage-common.mjs", "ticket-store-cli.mjs", "ticket-store.mjs")


def runtime_digest(root):
    root = Path(root).absolute()
    no_links(root)
    hashes = {}
    for name in RUNTIME_FILES:
        file = root / name
        no_links(file)
        if not file.is_file() or file.stat().st_size > 1024 * 1024:
            raise ValueError("bounded complete Registry runtime required")
        hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_runtime(root, expected):
    if not isinstance(expected, str) or re.fullmatch(r"[a-f0-9]{64}", expected) is None:
        raise ValueError("independent Registry runtime pin required")
    if runtime_digest(root) != expected:
        raise ValueError("Registry runtime digest mismatch")


def invoke(root, pin, *args, content=None):
    verify_runtime(root, pin)
    node = shutil.which("node")
    if node is None:
        raise ValueError("Node runtime required")
    result = subprocess.run([node, str(Path(root) / "ticket-store-cli.mjs"), *args],
        input=content, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError("Registry ticket operation failed")
    return json.loads(result.stdout)


def create(args):
    ticket = args.ticket
    if re.fullmatch(r"ticket-[0-9]{3,}", ticket or "") is None:
        raise ValueError("reserved ticket identity required")
    if not args.title or "\n" in args.title or "\r" in args.title:
        raise ValueError("single-line title required")
    intent = {"schema": "new-project.intent/v3", "ticket": ticket, "summary": args.title,
        "workstream": args.workstream,
        "classification": {"kind": args.kind, "priority": args.priority, "origin": args.origin},
        # Allocation reserves identity, not source scope. The caller fills its
        # bounded implementation intent in SQLite before changing source.
        "allowedPaths": [f"project/{ticket}/**"], "forbiddenPaths": ["project/ticket-*/user-*.md"],
        "stacks": [], "dependsOn": [], "conflictsWith": [], "integrationTicket": None}
    readme = (f"# {args.title}\n\n- **Status**: IN_PROGRESS\n- **Workflow state**: EDIT\n\n"
        "## Goal and scope\n\nComplete the bounded intent in SQLite before implementation.\n")
    content = json.dumps({"README.md": readme, "intent.json": json.dumps(intent, indent=2) + "\n"})
    invoke(args.runtime_root, args.runtime_sha256, "init", "--repository", str(args.root))
    receipt = invoke(args.runtime_root, args.runtime_sha256, "create", "--repository", str(args.root),
        "--ticket", ticket, "--allocation-key", args.allocation_key, content=content)
    return {**receipt, "runtime_sha256": args.runtime_sha256, "storage": "sqlite"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["digest", "verify", "highest", "create", "active"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-root")
    parser.add_argument("--runtime-sha256")
    parser.add_argument("--active-status", action="append", default=[])
    for name in ("ticket", "title", "workstream", "kind", "priority", "origin", "allocation-key"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    try:
        if args.command == "active":
            from ticket_activity import resolve
            text = read_file(args.root, args.ticket, "README.md").decode("utf-8")
            match = re.search(r"(?mi)^-[ \t]+\*\*Status\*\*:[ \t]*([A-Z_]+)[ \t]*$", text)
            if match is None:
                raise ValueError("ticket status required")
            result = resolve(args.root, args.root / "project" / args.ticket, set(args.active_status), status_override=match.group(1))
            raise SystemExit(0 if result.active else 1)
        elif args.command == "highest":
            database = primary_database(args.root)
            rows = database_rows(args.root, database) if database.exists() else []
            print(max((int(row[0].removeprefix("ticket-")) for row in rows), default=0))
        elif args.command == "digest":
            print(runtime_digest(args.runtime_root))
        elif args.command == "verify":
            verify_runtime(args.runtime_root, args.runtime_sha256)
        else:
            print(json.dumps(create(args)))
    except Exception:
        # Do not echo command input, ticket contents or child stderr.
        parser.exit(2 if args.command == "active" else 1, "GOV-TICKET-ALLOCATION-003: SQLite storage or pinned runtime validation failed.\n")


if __name__ == "__main__":
    main()
