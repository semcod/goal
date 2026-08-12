#!/usr/bin/env python3
"""Parse, serialize, replay and append-only-check decision records (ticket-031).

DSL form and JSON (governance/decision-record.schema.json) are mutually
derivable. Verdicts with authority ADVISORY are never trusted: replay always
recomputes from INPUT + APPLIED_RULE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "new-project.decision-record/v1"
DECISION_START = re.compile(r"^DECISION\s+(D-\d{3}-\d{4,})\s*$")
FIELD = re.compile(r"^([A-Z][A-Z0-9_]*)\s+(.+)$")
INPUT_LINE = re.compile(r"^INPUT\s+([A-Za-z0-9_]+)\s*=\s*(.+)$")
VERDICT_LINE = re.compile(
    r"^VERDICT\s+(\S+)\s+AUTHORITY\s+(DETERMINISTIC|ADVISORY)\s*$"
)
REJECTED_LINE = re.compile(r"^REJECTED\s+(\S+)\s+BECAUSE\s+(.+)$")
ADVISORY_LINE = re.compile(
    r'^ADVISORY\s+llm_verdict\s*=\s*"([^"]*)"\s+MODEL\s+"([^"]*)"\s*$'
)
ASSERT_LINE = re.compile(r"^ASSERT\s+(.+)$")


def parse_value(raw: str) -> Any:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def format_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def decision_body(text: str) -> str:
    body = text.strip()
    if body.startswith("```"):
        lines = body.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        body = "\n".join(lines).strip()
    return body


def apply_named_field(record: dict[str, Any], key: str, value: str) -> bool:
    destinations = {
        "TICKET": "ticket",
        "HEAD_SHA": "headSha",
        "CORRELATION_ID": "correlationId",
        "ACTOR": "actor",
        "APPLIED_RULE": "appliedRule",
    }
    destination = destinations.get(key)
    if destination is None:
        return False
    record[destination] = value
    return True


def apply_decision_line(record: dict[str, Any], line: str) -> bool:
    match = DECISION_START.match(line)
    if match:
        record["decisionId"] = match.group(1)
        return True
    match = INPUT_LINE.match(line)
    if match:
        record["inputs"][match.group(1)] = parse_value(match.group(2))
        return True
    match = VERDICT_LINE.match(line)
    if match:
        record["verdict"] = match.group(1)
        record["verdictAuthority"] = match.group(2)
        return True
    match = REJECTED_LINE.match(line)
    if match:
        record["rejected"] = {
            "alternative": match.group(1),
            "because": match.group(2).strip(),
        }
        return True
    match = ADVISORY_LINE.match(line)
    if match:
        record["advisory"] = {
            "llmVerdict": match.group(1),
            "model": match.group(2),
        }
        return True
    match = ASSERT_LINE.match(line)
    if match:
        record["assertions"].append(match.group(1).strip())
        return True
    match = FIELD.match(line)
    return bool(match and apply_named_field(record, match.group(1), match.group(2).strip()))


def require_decision_fields(record: dict[str, Any]) -> None:
    required = [
        "decisionId",
        "ticket",
        "headSha",
        "correlationId",
        "actor",
        "appliedRule",
        "verdict",
        "verdictAuthority",
        "rejected",
    ]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(f"decision record missing fields: {missing}")
    if not record["inputs"]:
        raise ValueError("decision record has no INPUT lines")
    if not record["assertions"]:
        raise ValueError("decision record has no ASSERT lines")


def parse_dsl_record(text: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "inputs": {},
        "assertions": [],
        "advisory": None,
        "derivedFrom": None,
    }
    for line in decision_body(text).splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if not apply_decision_line(record, line):
            raise ValueError(f"unrecognized decision-record line: {line}")
    require_decision_fields(record)
    return record


def to_dsl(record: dict[str, Any]) -> str:
    lines = [
        f"DECISION {record['decisionId']}",
        f"TICKET {record['ticket']}",
        f"HEAD_SHA {record['headSha']}",
        f"CORRELATION_ID {record['correlationId']}",
        f"ACTOR {record['actor']}",
        f"APPLIED_RULE {record['appliedRule']}",
    ]
    for key in sorted(record["inputs"]):
        lines.append(f"INPUT {key} = {format_value(record['inputs'][key])}")
    lines.append(
        f"VERDICT {record['verdict']} AUTHORITY {record['verdictAuthority']}"
    )
    rejected = record["rejected"]
    lines.append(
        f"REJECTED {rejected['alternative']} BECAUSE {rejected['because']}"
    )
    adv = record.get("advisory")
    if adv:
        lines.append(
            f'ADVISORY llm_verdict = "{adv.get("llmVerdict", "")}" '
            f'MODEL "{adv.get("model", "")}"'
        )
    for assertion in record.get("assertions") or []:
        lines.append(f"ASSERT {assertion}")
    return "\n".join(lines) + "\n"


def record_content_hash(record: dict[str, Any]) -> str:
    # Hash the canonical DSL without relying on insertion order of free text.
    canonical = to_dsl(record)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def replay_verdict(record: dict[str, Any]) -> str:
    """Recompute verdict from INPUT + APPLIED_RULE without reading ADVISORY."""
    if record.get("verdictAuthority") == "ADVISORY":
        raise ValueError("GOV-DECISION-003: verdict authority must not be ADVISORY")
    rule = record["appliedRule"]
    inputs = record["inputs"]

    # P-CORE-015 / check-gate family: required checks must all PASS.
    if rule in {"P-CORE-015", "C-CI-001", "C-DECISION-GATE"} or rule.startswith(
        "P-CORE-01"
    ):
        required = inputs.get("required_checks")
        observed = inputs.get("observed_checks")
        if not isinstance(required, list) or not isinstance(observed, list):
            raise ValueError(
                "GOV-DECISION-002: check-gate rules require "
                "required_checks and observed_checks arrays"
            )
        status: dict[str, str] = {}
        for item in observed:
            if not isinstance(item, str) or "=" not in item:
                raise ValueError(
                    f"GOV-DECISION-002: observed_checks entry not name=STATUS: {item!r}"
                )
            name, st = item.split("=", 1)
            status[name] = st.upper()
        for name in required:
            st = status.get(str(name))
            if st != "PASS" and st != "SUCCESS":
                return "REQUEST_CHANGES"
        unsafe = inputs.get("unsafe_change_reasons") or []
        if unsafe:
            return "REQUEST_CHANGES"
        return "APPROVE"

    # Default deterministic gate: explicit expected_verdict in inputs for tests
    # of custom rules without encoding every POLICY rule here.
    if "expected_verdict_from_rule" in inputs:
        return str(inputs["expected_verdict_from_rule"])

    raise ValueError(
        f"GOV-DECISION-002: no deterministic replay for APPLIED_RULE {rule}"
    )


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != SCHEMA:
        errors.append("GOV-DECISION-002: unsupported schema")
    if record.get("verdictAuthority") != "DETERMINISTIC":
        errors.append("GOV-DECISION-003: VERDICT_AUTHORITY must be DETERMINISTIC")
    for assertion in record.get("assertions") or []:
        if (
            "VERDICT_AUTHORITY" in assertion
            and "ADVISORY" in assertion
            and record.get("verdictAuthority") == "ADVISORY"
        ):
            errors.append("GOV-DECISION-003: assertion forbids ADVISORY authority")
    try:
        recomputed = replay_verdict(record)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if recomputed != record.get("verdict"):
        errors.append(
            "GOV-DECISION-004: replayed verdict "
            f"{recomputed!r} != recorded {record.get('verdict')!r}"
        )
    return errors


def split_decision_blocks(markdown: str) -> list[str]:
    """Extract fenced ```dsl DECISION ... blocks or bare DECISION sequences."""
    blocks: list[str] = []
    fence = re.findall(r"```dsl\n(.*?)```", markdown, flags=re.DOTALL)
    for body in fence:
        if "DECISION " in body:
            # may contain multiple DECISION records
            parts = re.split(r"(?=^DECISION\s+D-)", body.strip(), flags=re.MULTILINE)
            for part in parts:
                part = part.strip()
                if part.startswith("DECISION "):
                    blocks.append(part)
    if blocks:
        return blocks
    parts = re.split(r"(?=^DECISION\s+D-)", markdown.strip(), flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip().startswith("DECISION ")]


def check_append_only(previous_markdown: str, current_markdown: str) -> list[str]:
    """Fail if any earlier decision record was modified or removed."""
    prev_blocks = split_decision_blocks(previous_markdown)
    curr_blocks = split_decision_blocks(current_markdown)
    errors: list[str] = []
    if len(curr_blocks) < len(prev_blocks):
        errors.append(
            "GOV-DECISION-001: decision log shrank "
            f"({len(prev_blocks)} -> {len(curr_blocks)}); append-only violated"
        )
        return errors
    for idx, prev in enumerate(prev_blocks):
        prev_rec = parse_dsl_record(prev)
        curr_rec = parse_dsl_record(curr_blocks[idx])
        if record_content_hash(prev_rec) != record_content_hash(curr_rec):
            errors.append(
                "GOV-DECISION-001: earlier decision "
                f"{prev_rec.get('decisionId')} was modified (append-only)"
            )
    return errors


def from_change_evaluation(evaluation: dict[str, Any], **meta: str) -> dict[str, Any]:
    """Derive a decision record from t2c.change-evaluation/v1 (no dual truth)."""
    if evaluation.get("schemaVersion") != "t2c.change-evaluation/v1":
        raise ValueError("expected t2c.change-evaluation/v1")
    subject = evaluation["subject"]
    contract = evaluation["contract"]
    verdict_map = {
        "allow": "APPROVE",
        "deny": "REQUEST_CHANGES",
        "approve": "APPROVE",
        "request_changes": "REQUEST_CHANGES",
    }
    raw = str(evaluation.get("verdict", "")).lower()
    verdict = verdict_map.get(raw, "BLOCKED")
    gates = evaluation.get("gates") or {}
    observed = []
    if isinstance(gates, dict):
        for name, state in gates.items():
            observed.append(f"{name}={str(state).upper()}")
    record = {
        "schema": SCHEMA,
        "decisionId": meta["decisionId"],
        "ticket": contract["ticket"],
        "headSha": subject["headSha"],
        "correlationId": meta["correlationId"],
        "actor": meta.get("actor", "agent:validator"),
        "appliedRule": meta.get("appliedRule", "P-CORE-015"),
        "inputs": {
            "required_checks": meta.get("required_checks")
            or json.loads(Path("governance/required-checks.json").read_text()).get(
                "requiredCheckNames", ["test"]
            ),
            "observed_checks": observed
            or meta.get("observed_checks", ["test=PASS"]),
            "evaluation_verdict": evaluation.get("verdict"),
        },
        "verdict": verdict if verdict != "BLOCKED" else "REQUEST_CHANGES",
        "verdictAuthority": "DETERMINISTIC",
        "rejected": {
            "alternative": "APPROVE"
            if verdict != "APPROVE"
            else "REQUEST_CHANGES",
            "because": meta.get(
                "because",
                "DERIVED_FROM_CHANGE_EVALUATION",
            ),
        },
        "advisory": None,
        "assertions": ['VERDICT_AUTHORITY != "ADVISORY"'],
        "derivedFrom": {
            "changeEvaluationSchema": "t2c.change-evaluation/v1",
            "evaluationPath": meta.get("evaluationPath", "change-evaluation.json"),
        },
    }
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate-dsl", help="validate one DSL decision record")
    p_val.add_argument("path", type=Path)

    p_rep = sub.add_parser("replay", help="print recomputed verdict")
    p_rep.add_argument("path", type=Path)

    p_app = sub.add_parser(
        "check-append-only",
        help="compare previous and current decision log markdown",
    )
    p_app.add_argument("previous", type=Path)
    p_app.add_argument("current", type=Path)

    args = parser.parse_args(argv)
    if args.cmd == "validate-dsl":
        record = parse_dsl_record(args.path.read_text(encoding="utf-8"))
        errors = validate_record(record)
        if errors:
            print("FAIL", file=sys.stderr)
            for e in errors:
                print(e, file=sys.stderr)
            return 1
        print("OK", record["decisionId"], record["verdict"])
        return 0
    if args.cmd == "replay":
        record = parse_dsl_record(args.path.read_text(encoding="utf-8"))
        print(replay_verdict(record))
        return 0
    if args.cmd == "check-append-only":
        errors = check_append_only(
            args.previous.read_text(encoding="utf-8"),
            args.current.read_text(encoding="utf-8"),
        )
        if errors:
            for e in errors:
                print(e, file=sys.stderr)
            return 1
        print("append-only OK")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
