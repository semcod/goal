#!/usr/bin/env python3
"""Validate multi-agent repository change leases without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

LEASE_SCHEMA = "wellmanifest.change-lease/v1"
REQUEST_SCHEMA = "wellmanifest.change-lease-transition/v1"
RECEIPT_SCHEMA = "wellmanifest.change-lease-receipt/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
PHASES = {"claimed", "editing", "validating", "publication_frozen", "dispatching", "approved", "merged", "closed", "cancelled", "expired", "released"}
FROZEN_PHASES = {"publication_frozen", "dispatching", "approved"}
TERMINAL_REPLACEMENT_PHASES = {"merged", "closed", "cancelled", "released"}
TRANSITIONS = {
    "heartbeat": {phase: phase for phase in PHASES - {"released"}},
    "begin-edit": {"claimed": "editing"},
    "begin-validation": {"editing": "validating"},
    "freeze-publication": {"validating": "publication_frozen"},
    "dispatch-validation": {"publication_frozen": "dispatching"},
    "approve": {"dispatching": "approved"},
    "record-merge": {"approved": "merged"},
    "close": {"merged": "closed"},
    "cancel": {phase: "cancelled" for phase in PHASES - {"merged", "closed", "cancelled", "expired", "released"}},
    "expire": {phase: "expired" for phase in PHASES - {"merged", "closed", "cancelled", "expired", "released"}},
    "release": {"closed": "released", "cancelled": "released", "expired": "released"},
    "supersede": {"claimed": "cancelled", "editing": "cancelled", "validating": "cancelled"},
}
LEASE_FIELDS = {"schema", "leaseId", "repositoryRef", "targetBranch", "ticketId", "workstream", "scopeHash", "branchRef", "worktreeId", "ownerActor", "ownerSession", "phase", "leaseRevision", "fencingToken", "issuedAt", "expiresAt", "heartbeatAt", "headSha", "pullRequest", "validatorRunId", "publicationFrozen", "planHash", "previousReceiptRef", "eventSequence"}
REQUEST_FIELDS = {"schema", "requestId", "leaseId", "action", "expectedRevision", "expectedFencingToken", "expectedPhase", "requestedBy", "idempotencyKey", "targetHeadSha", "replacementReceiptRef", "authorityRef", "requestedAt"}
RECEIPT_FIELDS = {"schema", "requestId", "leaseId", "previousRevision", "leaseRevision", "previousFencingToken", "fencingToken", "action", "outcome", "code", "phaseBefore", "phaseAfter", "headSha", "pullRequest", "receiptRef", "occurredAt"}


def finding(code: str, message: str, **evidence: Any) -> dict[str, Any]:
    return {"code": code, "message": message, "evidence": evidence}


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [finding("GOV-CHANGE-LEASE-001", f"Cannot read JSON document: {error}", path=str(path))]
    if not isinstance(value, dict):
        return None, [finding("GOV-CHANGE-LEASE-001", "Document root must be an object.", path=str(path))]
    return value, []


def closed_object(value: dict[str, Any], expected: set[str], label: str) -> list[dict[str, Any]]:
    missing, extra = sorted(expected - set(value)), sorted(set(value) - expected)
    return [] if not missing and not extra else [finding("GOV-CHANGE-LEASE-001", f"{label} is not a closed object.", missing=missing, extra=extra)]


def valid_time(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_lease(value: dict[str, Any]) -> list[dict[str, Any]]:
    errors = closed_object(value, LEASE_FIELDS, "lease")
    if errors:
        return errors
    strings = ["leaseId", "repositoryRef", "targetBranch", "ticketId", "workstream", "branchRef", "worktreeId", "ownerActor", "ownerSession"]
    if value.get("schema") != LEASE_SCHEMA or any(not isinstance(value.get(k), str) or not value[k] for k in strings):
        errors.append(finding("GOV-CHANGE-LEASE-001", "Lease identity fields are invalid."))
    if not SHA256_RE.fullmatch(str(value.get("scopeHash", ""))) or not SHA256_RE.fullmatch(str(value.get("planHash", ""))):
        errors.append(finding("GOV-CHANGE-LEASE-001", "Lease hashes must be lowercase SHA-256 values."))
    phase = value.get("phase")
    if phase not in PHASES:
        errors.append(finding("GOV-CHANGE-LEASE-001", "Lease phase is invalid.", phase=phase))
    for key in ("leaseRevision", "fencingToken", "eventSequence"):
        if not isinstance(value.get(key), int) or value[key] < 1:
            errors.append(finding("GOV-CHANGE-LEASE-001", f"{key} must be a positive integer."))
    for key in ("issuedAt", "expiresAt", "heartbeatAt"):
        if not valid_time(value.get(key)):
            errors.append(finding("GOV-CHANGE-LEASE-001", f"{key} must be an RFC 3339 timestamp."))
    head, pr = value.get("headSha"), value.get("pullRequest")
    if head is not None and (not isinstance(head, str) or not GIT_SHA_RE.fullmatch(head)):
        errors.append(finding("GOV-CHANGE-LEASE-001", "headSha must be null or an exact Git SHA."))
    if pr is not None and (not isinstance(pr, int) or pr < 1):
        errors.append(finding("GOV-CHANGE-LEASE-001", "pullRequest must be null or a positive integer."))
    frozen = value.get("publicationFrozen")
    if not isinstance(frozen, bool) or frozen != (phase in FROZEN_PHASES):
        errors.append(finding("GOV-CHANGE-LEASE-003", "publicationFrozen must match frozen phases.", phase=phase, publicationFrozen=frozen))
    if phase in FROZEN_PHASES | {"merged", "closed", "released"} and head is None:
        errors.append(finding("GOV-CHANGE-LEASE-003", "Publication and merge terminal phases require headSha.", phase=phase))
    return errors


def validate_request(value: dict[str, Any]) -> list[dict[str, Any]]:
    errors = closed_object(value, REQUEST_FIELDS, "transition request")
    if errors:
        return errors
    if value.get("schema") != REQUEST_SCHEMA or value.get("action") not in TRANSITIONS:
        errors.append(finding("GOV-CHANGE-LEASE-001", "Transition schema or action is invalid."))
    for key in ("requestId", "leaseId", "requestedBy", "idempotencyKey", "authorityRef"):
        if not isinstance(value.get(key), str) or not value[key]:
            errors.append(finding("GOV-CHANGE-LEASE-001", f"{key} must be a non-empty string."))
    for key in ("expectedRevision", "expectedFencingToken"):
        if not isinstance(value.get(key), int) or value[key] < 1:
            errors.append(finding("GOV-CHANGE-LEASE-001", f"{key} must be a positive integer."))
    if value.get("expectedPhase") not in PHASES or not valid_time(value.get("requestedAt")):
        errors.append(finding("GOV-CHANGE-LEASE-001", "Expected phase or timestamp is invalid."))
    head = value.get("targetHeadSha")
    if head is not None and (not isinstance(head, str) or not GIT_SHA_RE.fullmatch(head)):
        errors.append(finding("GOV-CHANGE-LEASE-001", "targetHeadSha must be null or an exact Git SHA."))
    return errors


def validate_receipt(value: dict[str, Any]) -> list[dict[str, Any]]:
    errors = closed_object(value, RECEIPT_FIELDS, "transition receipt")
    if errors:
        return errors
    if value.get("schema") != RECEIPT_SCHEMA or value.get("action") not in TRANSITIONS or value.get("outcome") not in {"accepted", "rejected", "idempotent"}:
        errors.append(finding("GOV-CHANGE-LEASE-001", "Receipt schema, action or outcome is invalid."))
    if value.get("phaseBefore") not in PHASES or value.get("phaseAfter") not in PHASES:
        errors.append(finding("GOV-CHANGE-LEASE-001", "Receipt phase is invalid."))
    for key in ("previousRevision", "leaseRevision", "previousFencingToken", "fencingToken"):
        if not isinstance(value.get(key), int) or value[key] < 1:
            errors.append(finding("GOV-CHANGE-LEASE-001", f"{key} must be a positive integer."))
    if value.get("outcome") == "accepted" and (value["leaseRevision"] != value["previousRevision"] + 1 or value["fencingToken"] != value["previousFencingToken"] + 1):
        errors.append(finding("GOV-CHANGE-LEASE-002", "Accepted receipt must increment revision and fencing token exactly once."))
    if not valid_time(value.get("occurredAt")):
        errors.append(finding("GOV-CHANGE-LEASE-001", "Receipt timestamp is invalid."))
    return errors


def evaluate_transition(lease: dict[str, Any], request: dict[str, Any], replacement: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    errors = validate_lease(lease) + validate_request(request)
    code = message = None
    phase, action = str(lease.get("phase", "claimed")), request.get("action")
    if not errors and request["leaseId"] != lease["leaseId"]:
        code, message = "GOV-CHANGE-LEASE-002", "Request targets another lease."
    if not errors and (request["expectedRevision"] != lease["leaseRevision"] or request["expectedFencingToken"] != lease["fencingToken"] or request["expectedPhase"] != phase):
        code, message = "GOV-CHANGE-LEASE-002", "Compare-and-swap authority is stale."
    next_phase = TRANSITIONS.get(str(action), {}).get(phase)
    if not errors and code is None and next_phase is None:
        code, message = "GOV-CHANGE-LEASE-003", "Transition is not allowed from the current phase."
    target_head = request.get("targetHeadSha")
    if not errors and code is None and action == "freeze-publication" and target_head is None:
        code, message = "GOV-CHANGE-LEASE-003", "Freeze requires an exact targetHeadSha."
    if not errors and code is None and phase in FROZEN_PHASES and target_head not in (None, lease.get("headSha")):
        code, message = "GOV-CHANGE-LEASE-003", "Frozen publication head cannot be changed."
    if not errors and code is None and action in {"dispatch-validation", "approve", "record-merge"} and target_head != lease.get("headSha"):
        code, message = "GOV-CHANGE-LEASE-003", "Transition requires the exact frozen head."
    if not errors and code is None and action == "supersede":
        invalid = replacement is None or bool(validate_receipt(replacement)) or replacement.get("phaseAfter") not in TERMINAL_REPLACEMENT_PHASES or replacement.get("outcome") != "accepted"
        if invalid:
            code, message = "GOV-CHANGE-LEASE-004", "Supersede requires an accepted terminal replacement receipt."
        elif request.get("replacementReceiptRef") != replacement.get("receiptRef"):
            code, message = "GOV-CHANGE-LEASE-004", "Replacement receipt reference does not match."
    if errors:
        code, message = errors[0]["code"], errors[0]["message"]
    accepted = code is None
    receipt = {
        "schema": RECEIPT_SCHEMA, "requestId": request.get("requestId", "invalid"), "leaseId": lease.get("leaseId", "invalid"),
        "previousRevision": lease.get("leaseRevision", 1), "leaseRevision": lease.get("leaseRevision", 1) + int(accepted),
        "previousFencingToken": lease.get("fencingToken", 1), "fencingToken": lease.get("fencingToken", 1) + int(accepted),
        "action": action if action in TRANSITIONS else "heartbeat", "outcome": "accepted" if accepted else "rejected", "code": code,
        "phaseBefore": phase if phase in PHASES else "claimed", "phaseAfter": next_phase if accepted and next_phase else (phase if phase in PHASES else "claimed"),
        "headSha": target_head if accepted and action == "freeze-publication" else lease.get("headSha"), "pullRequest": lease.get("pullRequest"),
        "receiptRef": f"receipt://change-lease/{lease.get('leaseId', 'invalid')}/{request.get('requestId', 'invalid')}", "occurredAt": request.get("requestedAt", "1970-01-01T00:00:00Z"),
    }
    return receipt, errors or ([] if accepted else [finding(str(code), str(message), phase=phase, action=action)])


def validate_trace(path: Path) -> list[dict[str, Any]]:
    findings, previous = [], None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [finding("GOV-CHANGE-LEASE-001", f"Cannot read receipt trace: {error}", path=str(path))]
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            receipt = json.loads(line)
        except json.JSONDecodeError as error:
            findings.append(finding("GOV-CHANGE-LEASE-001", f"Invalid receipt JSON: {error}", line=number)); continue
        if not isinstance(receipt, dict):
            findings.append(finding("GOV-CHANGE-LEASE-001", "Receipt must be an object.", line=number)); continue
        findings.extend(validate_receipt(receipt))
        if previous is not None and receipt.get("outcome") == "accepted" and (receipt.get("leaseId") != previous.get("leaseId") or receipt.get("previousRevision") != previous.get("leaseRevision") or receipt.get("previousFencingToken") != previous.get("fencingToken") or receipt.get("phaseBefore") != previous.get("phaseAfter")):
            findings.append(finding("GOV-CHANGE-LEASE-002", "Receipt trace is not monotonic.", line=number))
        if receipt.get("outcome") == "accepted":
            previous = receipt
    return findings


def validate_document(path: Path) -> list[dict[str, Any]]:
    value, errors = load_json(path)
    if value is None:
        return errors
    validators = {LEASE_SCHEMA: validate_lease, REQUEST_SCHEMA: validate_request, RECEIPT_SCHEMA: validate_receipt}
    validator = validators.get(value.get("schema"))
    return validator(value) if validator else [finding("GOV-CHANGE-LEASE-001", "Unknown change-lease schema.", schema=value.get("schema"))]


def validate_repository(root: Path) -> list[dict[str, Any]]:
    findings = []
    lease, trace = root / ".governance/change-lease.json", root / ".governance/change-lease-events.jsonl"
    if lease.exists(): findings.extend(validate_document(lease))
    if trace.exists(): findings.extend(validate_trace(trace))
    return findings


def print_findings(findings: list[dict[str, Any]], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps({"status": "failed" if findings else "passed", "findings": findings}, indent=2, sort_keys=True)); return
    if not findings:
        print("GOV-CHANGE-LEASE-PASS"); return
    for item in findings: print(f"{item['code']} ERROR: {item['message']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("document", type=Path)
    transition = sub.add_parser("transition"); transition.add_argument("--lease", type=Path, required=True); transition.add_argument("--request", type=Path, required=True); transition.add_argument("--replacement-receipt", type=Path)
    trace = sub.add_parser("trace"); trace.add_argument("document", type=Path)
    repository = sub.add_parser("repository"); repository.add_argument("root", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "validate": findings = validate_document(args.document)
    elif args.command == "trace": findings = validate_trace(args.document)
    elif args.command == "repository": findings = validate_repository(args.root.resolve())
    else:
        lease, left = load_json(args.lease); request, right = load_json(args.request); replacement, repl = None, []
        if args.replacement_receipt: replacement, repl = load_json(args.replacement_receipt)
        if lease is None or request is None or repl:
            print_findings(left + right + repl, args.format); return 1
        receipt, findings = evaluate_transition(lease, request, replacement)
        print(json.dumps(receipt, indent=2, sort_keys=True)); return 1 if findings else 0
    print_findings(findings, args.format); return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
