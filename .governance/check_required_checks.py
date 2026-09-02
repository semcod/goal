#!/usr/bin/env python3
"""Compare required-checks.json to jobs published by CI workflows.

Single source of truth for required check *names* is the repository instance
of required-checks.json (hub: governance/, adopter: .governance/). This gate
fails when a required name is missing from the workflow that publishes it, or
when that workflow publishes a job that is not declared.

Published names are the job ``name:`` field when present, otherwise the job
key. GitHub rulesets require the display name.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = "new-project.required-checks/v1"
JOB_LINE = re.compile(r"^  ([A-Za-z0-9][A-Za-z0-9_-]*):\s*(?:#.*)?$")
JOB_NAME_LINE = re.compile(r"^    name:\s*(.+?)\s*$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def yaml_scalar(raw: str) -> str:
    value = raw.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        return value[1:-1]
    return value


def resolve_source(root: Path, script_path: Path) -> tuple[Path | None, list[Path]]:
    candidates: list[Path] = []
    for raw in (
        script_path.resolve().parent / "required-checks.json",
        root / "governance" / "required-checks.json",
        root / ".governance" / "required-checks.json",
    ):
        resolved = raw.resolve()
        if resolved not in candidates:
            candidates.append(resolved)
    for path in candidates:
        if path.is_file():
            return path, candidates
    return None, candidates


def declared_checks(data: dict) -> list[tuple[str, str]]:
    has_legacy = "workflowFile" in data or "requiredCheckNames" in data
    has_bound = "requiredChecks" in data
    if has_legacy and has_bound:
        raise SystemExit(
            "required-checks must declare exactly one shape: "
            "workflowFile+requiredCheckNames or requiredChecks"
        )
    required_checks = data.get("requiredChecks")
    if isinstance(required_checks, list) and required_checks:
        pairs: list[tuple[str, str]] = []
        for item in required_checks:
            if not isinstance(item, dict):
                raise SystemExit("requiredChecks entries must be objects")
            name = item.get("name")
            workflow = item.get("workflowFile")
            if not isinstance(name, str) or not name.strip():
                raise SystemExit("requiredChecks.name missing or empty")
            if not isinstance(workflow, str) or not workflow.strip():
                raise SystemExit("requiredChecks.workflowFile missing or empty")
            pairs.append((name, workflow))
        return pairs
    names = data.get("requiredCheckNames")
    workflow = data.get("workflowFile")
    if not isinstance(names, list) or not names or not all(isinstance(n, str) and n.strip() for n in names):
        raise SystemExit("requiredCheckNames missing or empty")
    if not isinstance(workflow, str) or not workflow.strip():
        raise SystemExit("workflowFile missing")
    return [(name, workflow) for name in names]


def load_source(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise SystemExit(f"unsupported required-checks schema in {path}")
    declared_checks(data)
    return data


def workflow_job_names(workflow_path: Path) -> list[str]:
    text = workflow_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_jobs = False
    jobs: list[str] = []
    current_key: str | None = None
    current_name: str | None = None

    def flush() -> None:
        nonlocal current_key, current_name
        if current_key is None:
            return
        jobs.append(current_name or current_key)
        current_key = None
        current_name = None

    for line in lines:
        if re.match(r"^jobs:\s*(?:#.*)?$", line):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        if line and not line.startswith(" ") and not line.startswith("\t") and line.strip() and not line.lstrip().startswith("#"):
            break
        match = JOB_LINE.match(line)
        if match:
            flush()
            current_key = match.group(1)
            continue
        name_match = JOB_NAME_LINE.match(line)
        if name_match and current_key is not None and current_name is None:
            current_name = yaml_scalar(name_match.group(1))
    flush()
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
        help="repository root (default: parent of this script)",
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
        help="override path to a single workflow YAML",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else repo_root()
    looked: list[Path] = []
    if args.source is not None:
        source_path = args.source
        if not source_path.is_file():
            print(
                "required-checks gate FAILED: source file not found. looked in:\n"
                f"  - {source_path}",
                file=sys.stderr,
            )
            return 2
    else:
        source_path, looked = resolve_source(root, Path(__file__))
        if source_path is None:
            print(
                "required-checks gate FAILED: source file not found. looked in:",
                file=sys.stderr,
            )
            for path in looked:
                print(f"  - {path}", file=sys.stderr)
            return 2
    data = load_source(source_path)
    pairs = declared_checks(data)
    if args.workflow is not None:
        workflow_path = args.workflow
        if not workflow_path.is_file():
            print(f"workflow file not found: {workflow_path}", file=sys.stderr)
            return 2
        required = [name for name, _workflow in pairs]
        published = workflow_job_names(workflow_path)
        errors = compare(required, published)
        published_names = published
    else:
        by_workflow: dict[str, list[str]] = defaultdict(list)
        for name, workflow in pairs:
            by_workflow[workflow].append(name)
        errors = []
        published_names: list[str] = []
        for workflow, required in by_workflow.items():
            workflow_path = root / workflow
            if not workflow_path.is_file():
                print(f"workflow file not found: {workflow_path}", file=sys.stderr)
                return 2
            published = workflow_job_names(workflow_path)
            published_names.extend(published)
            errors.extend(compare(required, published))
    if errors:
        print("required-checks gate FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    required_names = [name for name, _workflow in pairs]
    if __name__ == "__main__":
        try:
            source_label = source_path.relative_to(root)
        except ValueError:
            source_label = source_path
        print(
            "required-checks gate OK: "
            f"source={source_label} "
            f"required={required_names} published={published_names}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
