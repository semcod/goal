#!/usr/bin/env python3
"""Compare governance/required-checks.json to jobs published by CI workflow.

Single source of truth for required check *names* is
``governance/required-checks.json``. This gate fails when:

* a required name is missing from the workflow job map, or
* a top-level workflow job is not listed in requiredCheckNames
  (every published job name is part of the protected surface for this hub).

Circular governance checks ignored by the external validator are recorded in
the same file but are not expected as workflow jobs here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SOURCE_REL = Path("governance/required-checks.json")
SCHEMA = "new-project.required-checks/v1"
JOB_LINE = re.compile(r"^  ([A-Za-z0-9][A-Za-z0-9_-]*):\s*(?:#.*)?$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_source(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise SystemExit(f"unsupported required-checks schema in {path}")
    names = data.get("requiredCheckNames")
    if not isinstance(names, list) or not names or not all(isinstance(n, str) and n.strip() for n in names):
        raise SystemExit(f"requiredCheckNames missing or empty in {path}")
    workflow = data.get("workflowFile")
    if not isinstance(workflow, str) or not workflow.strip():
        raise SystemExit(f"workflowFile missing in {path}")
    return data


def workflow_job_names(workflow_path: Path) -> list[str]:
    text = workflow_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_jobs = False
    jobs: list[str] = []
    for line in lines:
        if re.match(r"^jobs:\s*(?:#.*)?$", line):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        # next top-level key ends the jobs block
        if line and not line.startswith(" ") and not line.startswith("\t") and line.strip() and not line.lstrip().startswith("#"):
            break
        match = JOB_LINE.match(line)
        if match:
            jobs.append(match.group(1))
    if not jobs:
        raise SystemExit(f"no jobs parsed from {workflow_path}")
    return jobs


def compare(required: list[str], published: list[str]) -> list[str]:
    errors: list[str] = []
    req_set = set(required)
    pub_set = set(published)
    for name in required:
        if name not in pub_set:
            errors.append(
                f"required check {name!r} is missing from workflow jobs "
                f"(published={sorted(pub_set)})"
            )
    for name in published:
        if name not in req_set:
            errors.append(
                f"workflow job {name!r} is not listed in requiredCheckNames "
                f"(required={required})"
            )
    if list(required) != sorted(required, key=required.index):
        pass  # order preserved as declared; no error
    # stable order check: duplicates
    if len(required) != len(set(required)):
        errors.append(f"requiredCheckNames contains duplicates: {required}")
    if len(published) != len(set(published)):
        errors.append(f"workflow jobs contain duplicates: {published}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="override path to required-checks.json",
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        default=None,
        help="override path to workflow YAML",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else repo_root()
    source_path = args.source if args.source else root / SOURCE_REL
    data = load_source(source_path)
    workflow_path = args.workflow if args.workflow else root / data["workflowFile"]
    if not workflow_path.is_file():
        print(f"workflow file not found: {workflow_path}", file=sys.stderr)
        return 2
    required = list(data["requiredCheckNames"])
    published = workflow_job_names(workflow_path)
    errors = compare(required, published)
    if errors:
        print("required-checks gate FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(
        "required-checks gate OK: "
        f"source={source_path.relative_to(root) if source_path.is_relative_to(root) else source_path} "
        f"required={required} published={published}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
