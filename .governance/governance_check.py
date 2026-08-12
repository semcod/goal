#!/usr/bin/env python3
"""Deterministic policy-as-code validator for new-project target repositories."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

RUNTIME_VERSION = "0.10.0"
ACTIVE_DEFAULT = {"IN_PROGRESS"}
EXECUTABLE_SUFFIXES = {
    ".bat", ".c", ".cc", ".cmd", ".cpp", ".go", ".java", ".js", ".jsx",
    ".mjs", ".php", ".ps1", ".py", ".rb", ".rs", ".sh", ".ts", ".tsx",
}
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|access[_-]?key|client[_-]?secret|password|private[_-]?key|token)"
    r"[ \t]*[:=][ \t]*['\"]?([A-Za-z0-9_./+=-]{12,})"
)
SAFE_SECRET_VALUES = re.compile(r"(?i)^(example|placeholder|changeme|your[_-]|\$\{|<|xxx|test)")
LOCAL_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Documents|Desktop)[\\/]|/(?:home|Users)/[^/\s]+/)")
IMMUTABLE_IMAGE_RE = re.compile(r"^[^@\s]+@sha256:[a-f0-9]{64}$")
COMPOSE_IMAGE_RE = re.compile(
    r"^\s*image\s*:\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s#]+))"
)


@dataclass(order=True)
class Finding:
    code: str
    severity: str
    message: str
    remediation: str
    paths: list[str] = field(default_factory=list, compare=False)
    evidence: dict[str, Any] = field(default_factory=dict, compare=False)


@dataclass
class TicketRecord:
    directory: Path
    status: str | None
    workflow: str | None
    intent: dict[str, Any] | None
    intent_error: str | None


class Report:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[Finding] = []

    def add(
        self,
        code: str,
        message: str,
        remediation: str,
        paths: Iterable[str] = (),
        evidence: dict[str, Any] | None = None,
        severity: str = "error",
    ) -> None:
        self.findings.append(Finding(
            code=code,
            severity=severity,
            message=message,
            remediation=remediation,
            paths=sorted(set(paths)),
            evidence=evidence or {},
        ))

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.findings)

    def payload(self) -> dict[str, Any]:
        findings = sorted(self.findings)
        return {
            "schema": "new-project.governance-report/v1",
            "runtimeVersion": RUNTIME_VERSION,
            "root": ".",
            "status": "passed" if self.errors == 0 else "failed",
            "summary": {
                "errors": self.errors,
                "warnings": sum(item.severity == "warning" for item in findings),
                "findings": len(findings),
            },
            "findings": [asdict(item) for item in findings],
        }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def work_classification_header_error(value: Any) -> str | None:
    fields = {"$schema", "schema", "dimensions", "ordering", "priorityDerivation", "evaluation", "rules"}
    if not isinstance(value, dict) or set(value) != fields:
        return "work classification contract fields are invalid"
    if value.get("$schema") != "./work-classification.schema.json":
        return "work classification schema reference drifted"
    if value.get("schema") != "new-project.work-classification/v1":
        return "unsupported work classification schema"
    if value.get("dimensions") != {
        "kind": ["BUG", "FEATURE", "SERVICE"],
        "priority": ["P0", "P1", "P2", "P3"],
        "origin": ["regression", "requested", "health"],
    }:
        return "work classification dimensions or order drifted"
    ordering = value.get("ordering")
    if ordering != {
        "precedence": ["dependencies", "kind", "priority", "stableId"],
        "kindOrder": ["BUG", "FEATURE", "SERVICE"],
        "priorityOrder": ["P0", "P1", "P2", "P3"],
        "dependencyPolicy": "topological-before-ranking",
        "stableIdPolicy": "lexicographic",
    }:
        return "work classification precedence drifted"
    if value.get("priorityDerivation") != {
        "impact": {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3"},
        "declaredPolicy": "require-valid-priority",
        "serviceDefault": "P2",
    }:
        return "work classification priority derivation drifted"
    evaluation = value.get("evaluation")
    if not isinstance(evaluation, dict) or evaluation != {
        "mode": "first-match", "unmatchedPolicy": "reject", "llmRole": "advisory-only",
    }:
        return "work classification evaluation policy drifted"
    return None


def complexity_rule_assignment(when: dict[str, Any]) -> tuple[tuple[str, str] | None, str | None]:
    if when.get("baseline") == "measured" and (
        when.get("delta") == "increased" or when.get("threshold") == "crossed"
    ):
        return ("BUG", "regression"), "impact"
    if when == {
        "signal": "cyclomatic-complexity",
        "baseline": "pre-existing",
        "delta": "not-increased",
    }:
        return ("SERVICE", "health"), "service-default"
    return None, None


def expected_rule_assignment(when: dict[str, Any]) -> tuple[tuple[str, str] | None, str | None]:
    signal = when.get("signal")
    if signal == "defect" and when.get("impact") in {"outage-or-security", "functional"}:
        return ("BUG", "regression"), "impact"
    if signal == "cyclomatic-complexity":
        return complexity_rule_assignment(when)
    if signal == "work-request" and when.get("request") == "new-behavior":
        return ("FEATURE", "requested"), "declared"
    if signal == "work-request" and when.get("request") == "maintenance":
        return ("SERVICE", "health"), "service-default"
    return None, None


def work_classification_rule_error(rule: dict[str, Any]) -> str | None:
    if set(rule) != {"id", "when", "assign", "prioritySource"}:
        return "work classification rule fields are invalid"
    when = rule.get("when")
    assignment = rule.get("assign")
    if not isinstance(when, dict) or not isinstance(assignment, dict):
        return "work classification rule condition or assignment is invalid"
    expected_when_fields = {
        "defect": [{"signal", "impact"}],
        "cyclomatic-complexity": [
            {"signal", "baseline", "delta"},
            {"signal", "baseline", "threshold"},
        ],
        "work-request": [{"signal", "request"}],
    }.get(when.get("signal"))
    if expected_when_fields is None or set(when) not in expected_when_fields:
        return f"work classification rule {rule['id']} mixes incompatible signal fields"
    expected_assignment, expected_priority_source = expected_rule_assignment(when)
    if expected_assignment is None:
        return f"work classification rule {rule['id']} has invalid condition values"
    if set(assignment) != {"kind", "origin"}:
        return f"work classification rule {rule['id']} has an invalid assignment"
    actual_assignment = assignment.get("kind"), assignment.get("origin")
    if actual_assignment != expected_assignment:
        return f"work classification rule {rule['id']} has an invalid assignment"
    if rule.get("prioritySource") != expected_priority_source:
        return f"work classification rule {rule['id']} has an invalid priority source"
    return None


def work_classification_error(value: Any) -> str | None:
    header_error = work_classification_header_error(value)
    if header_error:
        return header_error
    assert isinstance(value, dict)
    rules = value.get("rules")
    if not isinstance(rules, list) or len(rules) != 7:
        return "work classification must contain exactly seven rules"
    identifiers = [rule.get("id") for rule in rules if isinstance(rule, dict)]
    expected_identifiers = [f"W-CLASS-{index:03d}" for index in range(1, 8)]
    if identifiers != expected_identifiers:
        return "work classification rule identifiers or first-match order drifted"
    for rule in rules:
        assert isinstance(rule, dict)
        rule_error = work_classification_rule_error(rule)
        if rule_error:
            return rule_error
    return None


def load_work_classification(
    root: Path,
    report: Report,
    raw_path: str = ".governance/work-classification.dsl.json",
) -> dict[str, Any] | None:
    try:
        path = safe_repo_path(root, raw_path)
        value = load_json(path)
        error = work_classification_error(value)
        if error:
            raise ValueError(error)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report.add(
            "GOV-MANIFEST-001",
            f"Work classification contract is invalid: {error}",
            "Restore the managed work-classification DSL from the pinned standard release.",
            [raw_path],
        )
        return None
    return value


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def safe_repo_path(root: Path, raw: str) -> Path:
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path escapes repository: {raw}") from error
    return candidate


def string_list(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (not nonempty or bool(value))
        and all(isinstance(item, str) and bool(item) for item in value)
        and len(value) == len(set(value))
    )


def relative_pattern(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return (
        not normalized.startswith("/")
        and not re.match(r"^[A-Za-z]:/", normalized)
        and ".." not in normalized.split("/")
    )


def approval_evidence_config_valid(value: Any) -> bool:
    if value is None:
        return True
    return (
        isinstance(value, dict)
        and set(value) == {
            "schema", "requiredBindings", "reviewVerificationMethod",
            "signedAttestationPredicateType",
        }
        and value.get("schema") == "new-project.approval-evidence/v1"
        and value.get("requiredBindings") == [
            "repository", "pullRequest", "headSha", "ticket", "actor",
        ]
        and value.get("reviewVerificationMethod") == "github-api-allowlist"
        and value.get("signedAttestationPredicateType")
        == "https://wellmanifest.dev/attestations/validator/v1"
    )


def branch_name(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith("/")
        and re.search(r"(?:\.\.|//|@\{|[~^:?*\[\\])", value) is None
    )


def integer_fields_valid(value: dict[str, Any], fields: Iterable[str]) -> bool:
    return all(
        isinstance(value.get(name), int) and not isinstance(value[name], bool)
        for name in fields
    )


def relative_pattern_list(value: Any, *, nonempty: bool = False) -> bool:
    return string_list(value, nonempty=nonempty) and all(relative_pattern(item) for item in value)


def delivery_limits_valid(value: dict[str, Any]) -> bool:
    return all([
        isinstance(value.get("requiredForImplementation"), bool),
        1 <= value["maxActiveMinutes"] <= 30,
        1 <= value["checkpointMinutes"] < value["maxActiveMinutes"],
        value["maxImplementationFiles"] >= 1,
        value["maxAffectedComponents"] >= 1,
        value["maxPublicInterfaceChanges"] >= 0,
        value["maxRuntimeDependencies"] >= 0,
    ])


def delivery_policy_valid(value: Any) -> bool:
    fields = {
        "requiredForImplementation", "maxActiveMinutes", "checkpointMinutes",
        "allowedComplexityClasses", "maxImplementationFiles",
        "maxAffectedComponents", "maxPublicInterfaceChanges",
        "maxRuntimeDependencies", "targetBranches", "publicInterfacePaths",
        "dependencyManifestPaths",
    }
    if not isinstance(value, dict) or set(value) != fields:
        return False
    integer_limits = (
        "maxActiveMinutes", "checkpointMinutes", "maxImplementationFiles",
        "maxAffectedComponents", "maxPublicInterfaceChanges",
        "maxRuntimeDependencies",
    )
    if not integer_fields_valid(value, integer_limits):
        return False
    limits_valid = delivery_limits_valid(value)
    classes_valid = (
        string_list(value.get("allowedComplexityClasses"), nonempty=True)
        and set(value["allowedComplexityClasses"]) <= {"XS", "S"}
    )
    targets_valid = (
        string_list(value.get("targetBranches"), nonempty=True)
        and all(branch_name(item) for item in value["targetBranches"])
    )
    paths_valid = relative_pattern_list(value.get("publicInterfacePaths")) and relative_pattern_list(
        value.get("dependencyManifestPaths")
    )
    return limits_valid and classes_valid and targets_valid and paths_valid


def delivery_header_error(value: dict[str, Any]) -> str | None:
    if not isinstance(value.get("acceptedBaseSha"), str) or re.fullmatch(r"[0-9a-f]{40}", value["acceptedBaseSha"]) is None:
        return "delivery acceptedBaseSha must be a full lowercase commit SHA"
    if not branch_name(value.get("targetBranch")):
        return "delivery targetBranch is invalid"
    if not isinstance(value.get("outcome"), str) or not value["outcome"].strip():
        return "delivery outcome is blank"
    if not string_list(value.get("nonGoals"), nonempty=True):
        return "delivery nonGoals must be an explicit non-empty list"
    if value.get("complexity") not in {"XS", "S"}:
        return "delivery complexity must be XS or S"
    minutes = value.get("estimatedMinutes")
    if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 30:
        return "delivery estimatedMinutes must be between 1 and 30"
    return None


def delivery_budgets_error(budgets: Any) -> str | None:
    fields = {
        "maxImplementationFiles", "maxAffectedComponents",
        "maxPublicInterfaceChanges", "maxRuntimeDependencies",
    }
    if not isinstance(budgets, dict) or set(budgets) != fields:
        return "delivery budgets are incomplete"
    if not integer_fields_valid(budgets, fields):
        return "delivery budgets must be integers"
    if budgets["maxImplementationFiles"] < 1 or budgets["maxAffectedComponents"] < 1:
        return "delivery file and component budgets must be positive"
    if budgets["maxPublicInterfaceChanges"] < 0 or budgets["maxRuntimeDependencies"] < 0:
        return "delivery interface and dependency budgets cannot be negative"
    return None


def delivery_components_error(components: Any) -> str | None:
    if not isinstance(components, list) or not components:
        return "delivery architecture requires at least one component"
    names: list[str] = []
    for component in components:
        if not isinstance(component, dict) or set(component) != {"name", "paths"}:
            return "delivery component must contain name and paths"
        if not isinstance(component.get("name"), str) or not component["name"].strip():
            return "delivery component name is blank"
        if not relative_pattern_list(component.get("paths"), nonempty=True):
            return "delivery component paths must be repository-relative patterns"
        names.append(component["name"])
    return "delivery component names must be unique" if len(names) != len(set(names)) else None


def delivery_ui_error(ui: Any) -> str | None:
    if not isinstance(ui, dict) or set(ui) != {"impact", "states", "evidence"}:
        return "delivery UI decision is incomplete"
    if ui.get("impact") not in {"none", "single-state", "multi-state"}:
        return "delivery UI impact is invalid"
    if not string_list(ui.get("states")) or not set(ui["states"]) <= {"loading", "empty", "error", "success"}:
        return "delivery UI states are invalid"
    if not string_list(ui.get("evidence")):
        return "delivery UI evidence must be a unique string list"
    return delivery_ui_impact_error(ui["impact"], ui["states"], ui["evidence"])


def delivery_ui_impact_error(impact: str, states: list[str], evidence: list[str]) -> str | None:
    if impact == "none" and (states or evidence):
        return "delivery UI states/evidence must be empty when impact is none"
    if impact == "single-state" and (len(states) != 1 or not evidence):
        return "single-state UI work requires one state and planned evidence"
    if impact == "multi-state" and (len(states) < 2 or not evidence):
        return "multi-state UI work requires at least two states and planned evidence"
    return None


def delivery_architecture_error(architecture: Any) -> str | None:
    fields = {
        "status", "decision", "components", "responsibilityChanges",
        "interfaceChanges", "dataChanges", "ui", "rollback",
    }
    if not isinstance(architecture, dict) or set(architecture) != fields:
        return "delivery architecture decision is incomplete"
    if architecture.get("status") != "accepted":
        return "delivery architecture status must be accepted before implementation"
    for name in ("decision", "rollback"):
        if not isinstance(architecture.get(name), str) or not architecture[name].strip():
            return f"delivery architecture {name} is blank"
    if not isinstance(architecture.get("responsibilityChanges"), bool):
        return "delivery responsibilityChanges must be boolean"
    for name in ("interfaceChanges", "dataChanges"):
        if not string_list(architecture.get(name)):
            return f"delivery architecture {name} must be a unique string list"
    return delivery_components_error(architecture.get("components")) or delivery_ui_error(architecture.get("ui"))


def delivery_validation_error(validation: Any) -> str | None:
    if not isinstance(validation, list) or not validation:
        return "delivery validation must map at least one acceptance criterion"
    criteria: list[str] = []
    for item in validation:
        if not isinstance(item, dict) or set(item) != {"criterion", "commands", "evidence"}:
            return "delivery validation entry is incomplete"
        if not isinstance(item.get("criterion"), str) or re.fullmatch(r"AC-[0-9]+", item["criterion"]) is None:
            return "delivery validation criterion is invalid"
        if not string_list(item.get("commands"), nonempty=True):
            return "delivery validation commands cannot be empty"
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            return "delivery validation evidence is blank"
        criteria.append(item["criterion"])
    return "delivery validation criteria must be unique" if len(criteria) != len(set(criteria)) else None


def standard_adoption_error(value: Any) -> str | None:
    fields = {"sourceRepository", "fromRevision", "toRevision"}
    if not isinstance(value, dict) or set(value) != fields:
        return "delivery standardAdoption fields are invalid"
    if value.get("sourceRepository") != "wellmanifest/new-project":
        return "delivery standardAdoption sourceRepository is invalid"
    from_revision = value.get("fromRevision")
    to_revision = value.get("toRevision")
    if from_revision is not None and (
        not isinstance(from_revision, str)
        or re.fullmatch(r"[0-9a-f]{40}", from_revision) is None
    ):
        return "delivery standardAdoption revisions must be full lowercase commit SHAs"
    if not isinstance(to_revision, str) or re.fullmatch(r"[0-9a-f]{40}", to_revision) is None:
        return "delivery standardAdoption revisions must be full lowercase commit SHAs"
    if from_revision == to_revision:
        return "delivery standardAdoption revisions must differ"
    return None


def delivery_intent_error(value: Any) -> str | None:
    required_fields = {
        "acceptedBaseSha", "targetBranch", "outcome", "nonGoals",
        "complexity", "estimatedMinutes", "budgets", "architecture",
        "runtimeDependencies", "validation",
    }
    if not isinstance(value, dict) or set(value) not in {
        frozenset(required_fields), frozenset({*required_fields, "standardAdoption"}),
    }:
        return "delivery must contain exactly the bounded-delivery fields"
    error = delivery_header_error(value) or delivery_budgets_error(value.get("budgets"))
    if error:
        return error
    error = delivery_architecture_error(value.get("architecture"))
    if error:
        return error
    if not string_list(value.get("runtimeDependencies")):
        return "delivery runtimeDependencies must be a unique string list"
    if "standardAdoption" in value:
        error = standard_adoption_error(value["standardAdoption"])
        if error:
            return error
    return delivery_validation_error(value.get("validation"))


def matches(path: str, patterns: Iterable[str]) -> bool:
    path_parts = path.replace("\\", "/").strip("/").split("/")

    def match_pattern(pattern: str) -> bool:
        pattern_parts = pattern.replace("\\", "/").strip("/").split("/")
        memo: dict[tuple[int, int], bool] = {}

        def visit(path_index: int, pattern_index: int) -> bool:
            key = (path_index, pattern_index)
            if key in memo:
                return memo[key]
            if pattern_index == len(pattern_parts):
                result = path_index == len(path_parts)
            elif pattern_parts[pattern_index] == "**":
                result = visit(path_index, pattern_index + 1) or (
                    path_index < len(path_parts) and visit(path_index + 1, pattern_index)
                )
            else:
                result = (
                    path_index < len(path_parts)
                    and fnmatch.fnmatchcase(path_parts[path_index], pattern_parts[pattern_index])
                    and visit(path_index + 1, pattern_index + 1)
                )
            memo[key] = result
            return result

        return visit(0, 0)

    return any(match_pattern(pattern) for pattern in patterns)


def segment_literal_prefix(pattern: str) -> str:
    index = min((pattern.find(char) for char in "*?[" if char in pattern), default=len(pattern))
    return pattern[:index]


def segment_literal_suffix(pattern: str) -> str:
    indexes = [pattern.rfind(char) for char in "*?]" if char in pattern]
    return pattern[max(indexes, default=-1) + 1:]


def segments_may_overlap(first: str, second: str) -> bool:
    first_magic = any(char in first for char in "*?[")
    second_magic = any(char in second for char in "*?[")
    if not first_magic and not second_magic:
        return first == second
    if not first_magic:
        return fnmatch.fnmatchcase(first, second)
    if not second_magic:
        return fnmatch.fnmatchcase(second, first)
    first_prefix = segment_literal_prefix(first)
    second_prefix = segment_literal_prefix(second)
    if first_prefix and second_prefix and not (
        first_prefix.startswith(second_prefix) or second_prefix.startswith(first_prefix)
    ):
        return False
    first_suffix = segment_literal_suffix(first)
    second_suffix = segment_literal_suffix(second)
    return not (
        first_suffix
        and second_suffix
        and not (
            first_suffix.endswith(second_suffix) or second_suffix.endswith(first_suffix)
        )
    )


def patterns_may_overlap(first: str, second: str) -> bool:
    first_parts = first.replace("\\", "/").strip("/").split("/")
    second_parts = second.replace("\\", "/").strip("/").split("/")
    memo: dict[tuple[int, int], bool] = {}

    def remaining_are_globstars(parts: list[str], index: int) -> bool:
        return all(part == "**" for part in parts[index:])

    def visit(first_index: int, second_index: int) -> bool:
        key = (first_index, second_index)
        if key in memo:
            return memo[key]
        if first_index == len(first_parts) and second_index == len(second_parts):
            result = True
        elif first_index == len(first_parts):
            result = remaining_are_globstars(second_parts, second_index)
        elif second_index == len(second_parts):
            result = remaining_are_globstars(first_parts, first_index)
        elif first_parts[first_index] == "**":
            result = visit(first_index + 1, second_index) or visit(first_index, second_index + 1)
        elif second_parts[second_index] == "**":
            result = visit(first_index, second_index + 1) or visit(first_index + 1, second_index)
        else:
            result = segments_may_overlap(first_parts[first_index], second_parts[second_index]) and visit(
                first_index + 1, second_index + 1
            )
        memo[key] = result
        return result

    return visit(0, 0)


def segment_pattern_covered_by(pattern: str, owner_pattern: str) -> bool:
    if pattern == owner_pattern:
        return True
    if not any(char in pattern for char in "*?["):
        return fnmatch.fnmatchcase(pattern, owner_pattern)
    if owner_pattern == "*":
        return True
    if "?" in owner_pattern or "[" in owner_pattern or owner_pattern.count("*") != 1:
        return False
    owner_prefix, owner_suffix = owner_pattern.split("*", 1)
    first_magic = min(
        (pattern.find(char) for char in "*?[" if char in pattern),
        default=len(pattern),
    )
    last_magic = max(pattern.rfind(char) for char in "*?[")
    pattern_prefix = pattern[:first_magic]
    pattern_suffix = pattern[last_magic + 1:]
    return pattern_prefix.startswith(owner_prefix) and pattern_suffix.endswith(owner_suffix)


def pattern_covered_by(pattern: str, owner_pattern: str) -> bool:
    if pattern == owner_pattern:
        return True
    if not any(char in pattern for char in "*?["):
        return matches(pattern, [owner_pattern])
    pattern_parts = pattern.replace("\\", "/").strip("/").split("/")
    owner_parts = owner_pattern.replace("\\", "/").strip("/").split("/")
    if owner_parts and owner_parts[-1] == "**" and len(pattern_parts) >= len(owner_parts) - 1:
        prefix = owner_parts[:-1]
        return all(
            segment_pattern_covered_by(allowed, owned)
            for allowed, owned in zip(pattern_parts, prefix)
        )
    if len(pattern_parts) == len(owner_parts) and "**" not in owner_parts:
        return all(
            segment_pattern_covered_by(allowed, owned)
            for allowed, owned in zip(pattern_parts, owner_parts)
        )
    return False


def git_output(root: Path, args: list[str]) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True,
    ).stdout


def changed_paths(root: Path, base: str | None, head: str, explicit: list[str]) -> list[str]:
    if explicit:
        normalized = sorted({path.replace("\\", "/").removeprefix("./") for path in explicit if path})
        for path in normalized:
            safe_repo_path(root, path)
        return normalized
    try:
        if base:
            raw = git_output(root, ["diff", "--name-only", "-z", f"{base}...{head}"])
            paths = raw.decode("utf-8", "surrogateescape").split("\0")
        else:
            tracked = git_output(root, ["diff", "--name-only", "-z", "HEAD"])
            untracked = git_output(root, ["ls-files", "--others", "--exclude-standard", "-z"])
            paths = (tracked + untracked).decode("utf-8", "surrogateescape").split("\0")
        return sorted({path for path in paths if path})
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        raise RuntimeError("Git could not determine the changed-path set") from error


def check_history_order(
    root: Path,
    base: str | None,
    head: str,
    ticket_name: str,
    ticket_root: str,
    intent_path: str,
    governance_patterns: list[str],
    report: Report,
) -> None:
    if not base:
        return
    try:
        commits = git_output(root, ["rev-list", "--reverse", f"{base}..{head}"]).decode().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        report.add(
            "GOV-DIFF-001", "Git could not enumerate commits for history-order validation.",
            "Fetch the complete base/head history and rerun the governance gate.",
            evidence={"base": base, "head": head},
        )
        return
    first_implementation: tuple[int, str] | None = None
    for index, commit in enumerate(commits):
        try:
            raw = git_output(root, ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "-z", commit])
        except subprocess.CalledProcessError:
            report.add(
                "GOV-DIFF-001", f"Git could not inspect commit {commit}.",
                "Fetch complete commit objects and rerun the governance gate.",
                evidence={"commit": commit},
            )
            return
        paths = [path for path in raw.decode("utf-8", "surrogateescape").split("\0") if path]
        if any(not matches(path, governance_patterns) for path in paths):
            first_implementation = (index, commit)
            break
    if first_implementation is None:
        return
    index, commit = first_implementation
    parent = f"{commit}^" if index > 0 else base
    ticket_intent = f"{ticket_root.rstrip('/')}/{ticket_name}/{intent_path}"
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{parent}:{ticket_intent}"], cwd=root,
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        report.add(
            "GOV-INTENT-003",
            f"{ticket_intent} did not exist before the first implementation commit.",
            "Commit the plan-only ticket and intent first; start implementation in a later commit after review.",
            [ticket_intent], {"firstImplementationCommit": commit},
        )


def standard_policy_valid(standard: Any) -> bool:
    return (
        isinstance(standard, dict)
        and set(standard) == {"id", "version"}
        and standard.get("id") == "wellmanifest/new-project"
        and isinstance(standard.get("version"), str)
        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", standard["version"]) is not None
    )


def ticket_policy_valid(ticket: Any) -> bool:
    base_fields = {
        "root", "directoryPattern", "requiredFiles", "requiredAgentFiles",
        "activeStatuses", "closedStatuses", "implementationStates", "intentFile",
    }
    if not isinstance(ticket, dict) or set(ticket) not in {
        frozenset(base_fields), frozenset({*base_fields, "nonActiveStatuses"}),
    }:
        return False
    values_valid = ticket_scalar_policy_valid(ticket) and ticket_list_policy_valid(ticket)
    if not values_valid:
        return False
    try:
        re.compile(ticket["directoryPattern"])
    except re.error:
        return False
    return True


def ticket_scalar_policy_valid(ticket: dict[str, Any]) -> bool:
    return all([
        isinstance(ticket.get("root"), str) and bool(ticket["root"]) and relative_pattern(ticket["root"]),
        isinstance(ticket.get("directoryPattern"), str) and bool(ticket["directoryPattern"]),
        isinstance(ticket.get("intentFile"), str) and bool(ticket["intentFile"]) and relative_pattern(ticket["intentFile"]),
    ])


def ticket_list_policy_valid(ticket: dict[str, Any]) -> bool:
    status_groups = [
        set(ticket.get(name, []))
        for name in ("activeStatuses", "nonActiveStatuses", "closedStatuses")
    ]
    return all([
        relative_pattern_list(ticket.get("requiredFiles")),
        relative_pattern_list(ticket.get("requiredAgentFiles")),
        string_list(ticket.get("activeStatuses"), nonempty=True),
        "nonActiveStatuses" not in ticket or string_list(ticket.get("nonActiveStatuses"), nonempty=True),
        string_list(ticket.get("closedStatuses"), nonempty=True),
        string_list(ticket.get("implementationStates"), nonempty=True),
        all(
            left.isdisjoint(right)
            for index, left in enumerate(status_groups)
            for right in status_groups[index + 1:]
        ),
    ])


def docker_policy_valid(docker: Any) -> bool:
    return (
        isinstance(docker, dict)
        and set(docker) == {"required", "dockerfiles", "composeFiles"}
        and isinstance(docker.get("required"), bool)
        and relative_pattern_list(docker.get("dockerfiles"), nonempty=True)
        and relative_pattern_list(docker.get("composeFiles"), nonempty=True)
    )


def workstreams_policy_valid(workstreams: Any) -> bool:
    if not isinstance(workstreams, dict) or not workstreams:
        return False
    valid_name = re.compile(r"[a-z0-9][a-z0-9-]*").fullmatch
    return all(
        isinstance(name, str)
        and valid_name(name) is not None
        and isinstance(item, dict)
        and set(item) == {"ownedPaths"}
        and relative_pattern_list(item.get("ownedPaths"), nonempty=True)
        for name, item in workstreams.items()
    )


def integration_policy_valid(integration: Any, workstreams: dict[str, Any]) -> bool:
    return (
        isinstance(integration, dict)
        and set(integration) == {"workstream", "requiredForPaths"}
        and isinstance(integration.get("workstream"), str)
        and relative_pattern_list(integration.get("requiredForPaths"))
        and integration["workstream"] in workstreams
    )


def coordination_policy_valid(coordination: Any) -> bool:
    fields = {
        "mode", "maxActiveTicketsPerWorkstream", "rejectActiveScopeOverlap",
        "workstreams", "integration",
    }
    if not isinstance(coordination, dict) or set(coordination) != fields:
        return False
    limit = coordination.get("maxActiveTicketsPerWorkstream")
    settings_valid = (
        coordination.get("mode") == "workstreams"
        and isinstance(limit, int)
        and not isinstance(limit, bool)
        and limit >= 1
        and isinstance(coordination.get("rejectActiveScopeOverlap"), bool)
    )
    workstreams = coordination.get("workstreams")
    return (
        settings_valid
        and workstreams_policy_valid(workstreams)
        and integration_policy_valid(coordination.get("integration"), workstreams)
    )


def common_manifest_policy_valid(manifest: dict[str, Any]) -> bool:
    approvals = manifest.get("trustedApprovalSources")
    return (
        standard_policy_valid(manifest.get("standard"))
        and relative_pattern_list(manifest.get("requiredFiles"))
        and relative_pattern_list(manifest.get("governancePaths"))
        and string_list(approvals, nonempty=True)
        and set(approvals) <= {
            "github-review", "github-app-review", "signed-attestation",
        }
        and approval_evidence_config_valid(manifest.get("approvalEvidence"))
        and ticket_policy_valid(manifest.get("ticket"))
        and docker_policy_valid(manifest.get("docker"))
    )


def basic_manifest_valid(manifest: Any) -> bool:
    if not isinstance(manifest, dict) or manifest.get("schema") not in {
        "new-project.governance/v1", "new-project.governance/v2",
    }:
        return False
    common_valid = common_manifest_policy_valid(manifest)
    if not common_valid or manifest["schema"] == "new-project.governance/v1":
        return common_valid
    if "nonActiveStatuses" not in manifest["ticket"]:
        return False
    allowed_root_keys = {
        "$schema", "schema", "standard", "requiredFiles", "governancePaths",
        "trustedApprovalSources", "approvalEvidence", "ticket", "docker",
        "coordination", "delivery", "stacks",
    }
    coordination = manifest.get("coordination")
    delivery = manifest.get("delivery")
    return (
        set(manifest) <= allowed_root_keys
        and string_list(manifest.get("stacks", []))
        and set(manifest.get("stacks", [])) <= {"node", "python", "go", "rust", "java", "docker", "frontend", "terraform", "kubernetes"}
        and coordination_policy_valid(coordination)
        and (delivery is None or delivery_policy_valid(delivery))
    )


def lock_standard_valid(standard: Any, expected_version: str) -> bool:
    return isinstance(standard, dict) and (
        set(standard) == {"id", "version", "sourceRepository", "sourceRevision", "publicationStatus"}
        and standard.get("id") == "wellmanifest/new-project"
        and standard.get("version") == expected_version
        and standard.get("sourceRepository") == "wellmanifest/new-project"
        and isinstance(standard.get("sourceRevision"), str)
        and re.fullmatch(r"[0-9a-f]{40}", standard["sourceRevision"]) is not None
        and standard.get("publicationStatus") == "published"
    )


def load_managed_lock(lock_path: Path, manifest: dict[str, Any]) -> dict[str, str]:
    lock = load_json(lock_path)
    managed = lock["managedFiles"]
    if (
        lock.get("schema") != "new-project.lock/v1"
        or set(lock) != {"schema", "standard", "managedFiles"}
        or not isinstance(managed, dict)
    ):
        raise ValueError("unsupported lock schema")
    if not lock_standard_valid(lock["standard"], manifest["standard"]["version"]):
        raise ValueError("lock must identify the published immutable standard revision")
    if not all(
            isinstance(raw_path, str)
            and relative_pattern(raw_path)
            and isinstance(digest, str)
            and re.fullmatch(r"[a-f0-9]{64}", digest)
            for raw_path, digest in managed.items()
    ):
        raise ValueError("managedFiles must map repository-relative paths to lowercase SHA-256 digests")
    return managed


def check_managed_file(root: Path, raw_path: str, expected: str, report: Report) -> None:
    try:
        path = safe_repo_path(root, raw_path)
    except ValueError as error:
        report.add("GOV-SYNC-001", str(error), "Use repository-relative managed paths.", [raw_path])
        return
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    if actual != expected:
        report.add(
            "GOV-SYNC-001", f"Managed governance file digest differs: {raw_path}",
            "Restore the pinned file or perform an explicit standard upgrade and regenerate the lock.",
            [raw_path], {"expectedSha256": expected, "actualSha256": actual},
        )


def extension_error(required: Any, candidate: Any, path: str = "$") -> str | None:
    if isinstance(required, dict):
        if not isinstance(candidate, dict):
            return f"{path} must remain an object"
        for key, value in required.items():
            if key not in candidate:
                return f"{path}/{key} is required by the managed base"
            error = extension_error(value, candidate[key], f"{path}/{key}")
            if error:
                return error
        return None
    if isinstance(required, list):
        if not isinstance(candidate, list):
            return f"{path} must remain an array"
        for value in required:
            if value not in candidate:
                return f"{path} removed a value required by the managed base"
        return None
    if candidate != required:
        return f"{path} differs from the managed base"
    return None


def check_lock(
    root: Path,
    lock_path: Path | None,
    manifest: dict[str, Any],
    report: Report,
) -> None:
    if lock_path is None:
        return
    if not lock_path.is_file():
        report.add(
            "GOV-SYNC-001", "Governance lock file is missing.",
            "Copy the versioned manifest lock from the approved standard adoption.",
            [rel(root, lock_path)] if lock_path.is_relative_to(root) else [],
        )
        return
    try:
        managed = load_managed_lock(lock_path, manifest)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        report.add("GOV-SYNC-001", f"Governance lock is invalid: {error}", "Regenerate the lock from a trusted standard release.", [rel(root, lock_path)])
        return
    for raw_path, expected in sorted(managed.items()):
        check_managed_file(root, raw_path, expected, report)
    package_path = root / ".governance/package-manifest.json"
    if not package_path.is_file():
        return
    try:
        strategies = package_strategies(package_path.read_bytes())
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        report.add(
            "GOV-SYNC-001", f"Governance package manifest is invalid: {error}",
            "Restore the pinned package manifest through an explicit standard upgrade.",
            [rel(root, package_path)],
        )
        return
    manifest_target = ".governance/manifest.json"
    base_target = ".governance/manifest.base.json"
    if strategies.get(manifest_target) != "extendable":
        return
    if strategies.get(base_target) != "managed" or base_target not in managed:
        report.add(
            "GOV-SYNC-001", "Extendable governance manifest has no hash-bound managed base.",
            "Adopt the complete published package including manifest.base.json.",
            [base_target, manifest_target],
        )
        return
    try:
        base = load_json(safe_repo_path(root, base_target))
        error = extension_error(base, manifest)
    except (OSError, ValueError, json.JSONDecodeError) as load_error:
        error = f"managed manifest base is invalid: {load_error}"
    if error:
        report.add(
            "GOV-SYNC-001", f"Target governance manifest violates its managed base: {error}",
            "Restore standard-owned values; keep target changes inside the declared extension fields.",
            [base_target, manifest_target],
        )


def parse_ticket_state(readme: Path) -> tuple[str | None, str | None]:
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError:
        return None, None
    status_match = re.search(r"(?mi)^-[ \t]+\*\*Status\*\*:[ \t]*([A-Z_]+)[ \t]*$", text)
    state_match = re.search(r"(?mi)^-[ \t]+\*\*Workflow state\*\*:[ \t]*([A-Z_]+)[ \t]*$", text)
    return (
        status_match.group(1).upper() if status_match else None,
        state_match.group(1).upper() if state_match else None,
    )


def ticket_directories(root: Path, config: dict[str, Any]) -> list[Path]:
    ticket_root = safe_repo_path(root, config["root"])
    pattern = re.compile(config["directoryPattern"])
    if not ticket_root.is_dir():
        return []
    return sorted(
        path for path in ticket_root.iterdir()
        if path.is_dir() and not path.is_symlink() and pattern.fullmatch(path.name)
    )


def intent_common_error(intent: dict[str, Any], ticket_name: str) -> str | None:
    if intent.get("ticket") != ticket_name:
        return "intent schema or ticket identity differs"
    if not isinstance(intent.get("summary"), str) or not intent["summary"].strip():
        return "intent summary is blank"
    for field_name in ("allowedPaths", "forbiddenPaths", "stacks"):
        if not string_list(intent.get(field_name)):
            return f"intent {field_name} must be a list of non-blank strings"
    if not intent["allowedPaths"]:
        return "intent allowedPaths is empty"
    for field_name in ("allowedPaths", "forbiddenPaths"):
        if not all(relative_pattern(value) for value in intent[field_name]):
            return f"intent {field_name} must contain repository-relative patterns"
    return None


def ticket_id_list_error(intent: dict[str, Any], field_name: str) -> str | None:
    values = intent.get(field_name)
    if not isinstance(values, list) or not all(
        isinstance(value, str) and re.fullmatch(r"ticket-[0-9]{3}", value)
        for value in values
    ):
        return f"intent {field_name} must contain ticket IDs"
    return f"intent {field_name} contains duplicates" if len(values) != len(set(values)) else None


def intent_v2_error(intent: dict[str, Any], ticket_name: str) -> str | None:
    workstream = intent.get("workstream")
    if not isinstance(workstream, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", workstream):
        return "intent workstream is invalid"
    for field_name in ("dependsOn", "conflictsWith"):
        error = ticket_id_list_error(intent, field_name)
        if error:
            return error
    integration = intent.get("integrationTicket")
    if integration is not None and (not isinstance(integration, str) or not re.fullmatch(r"ticket-[0-9]{3}", integration)):
        return "intent integrationTicket must be null or a ticket ID"
    if integration == ticket_name:
        return "intent integrationTicket cannot reference its own ticket"
    return delivery_intent_error(intent["delivery"]) if "delivery" in intent else None


def intent_classification_error(value: Any) -> str | None:
    if not isinstance(value, dict) or set(value) != {"kind", "priority", "origin"}:
        return "intent classification must contain kind, priority and origin"
    if value.get("kind") not in {"BUG", "FEATURE", "SERVICE"}:
        return "intent classification kind is invalid"
    if value.get("priority") not in {"P0", "P1", "P2", "P3"}:
        return "intent classification priority is invalid"
    if value.get("origin") not in {"regression", "requested", "health"}:
        return "intent classification origin is invalid"
    return None


def intent_fields_error(intent: Any) -> str | None:
    v1_fields = {"schema", "ticket", "summary", "allowedPaths", "forbiddenPaths", "stacks"}
    v2_fields = v1_fields | {"workstream", "dependsOn", "conflictsWith", "integrationTicket"}
    if not isinstance(intent, dict) or intent.get("schema") not in {
        "new-project.intent/v1", "new-project.intent/v2", "new-project.intent/v3",
    }:
        return "unsupported intent schema"
    expected = v1_fields if intent["schema"] == "new-project.intent/v1" else v2_fields
    if intent["schema"] == "new-project.intent/v3":
        expected |= {"classification"}
    allowed = [expected] if intent["schema"] == "new-project.intent/v1" else [expected, expected | {"delivery"}]
    if set(intent) not in allowed:
        return f"intent must contain exactly the {intent['schema'].rsplit('/', 1)[-1]} fields"
    return None


def validate_intent(path: Path, ticket_name: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        intent = load_json(path)
    except (OSError, json.JSONDecodeError) as error:
        return None, str(error)
    error = intent_fields_error(intent)
    if error:
        return None, error
    assert isinstance(intent, dict)
    error = intent_common_error(intent, ticket_name)
    if error:
        return None, error
    if intent["schema"] in {"new-project.intent/v2", "new-project.intent/v3"}:
        error = intent_v2_error(intent, ticket_name)
        if error:
            return None, error
    if intent["schema"] == "new-project.intent/v3":
        error = intent_classification_error(intent.get("classification"))
        if error:
            return None, error
    return intent, None


def load_ticket_records(directories: list[Path], config: dict[str, Any]) -> list[TicketRecord]:
    records = []
    for directory in directories:
        status, workflow = parse_ticket_state(directory / "README.md")
        intent, error = validate_intent(directory / config["intentFile"], directory.name)
        records.append(TicketRecord(directory, status, workflow, intent, error))
    return records


def repository_files(root: Path, changed: list[str]) -> list[str]:
    try:
        raw = git_output(root, ["ls-files", "-co", "--exclude-standard", "-z"])
        files = raw.decode("utf-8", "surrogateescape").split("\0")
    except (subprocess.CalledProcessError, FileNotFoundError):
        files = [rel(root, path) for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]
    return sorted({*files, *changed} - {""})


def valid_active_tickets(
    root: Path,
    config: dict[str, Any],
    active: list[TicketRecord],
    workstreams: dict[str, Any],
    report: Report,
) -> list[TicketRecord]:
    valid: list[TicketRecord] = []
    for record in active:
        intent_path = rel(root, record.directory / config["intentFile"])
        if record.intent_error:
            report.add(
                "GOV-INTENT-002", f"Ticket intent is invalid: {record.intent_error}",
                "Create a valid new-project.intent/v3 file before implementation.", [intent_path],
            )
            continue
        assert record.intent is not None
        if record.intent["schema"] != "new-project.intent/v3":
            report.add(
                "GOV-INTENT-002", f"Active ticket {record.directory.name} lacks deterministic intent/v3 classification.",
                "Migrate the active ticket to intent/v3 and declare kind, priority and origin; archived v1/v2 tickets remain readable.", [intent_path],
            )
            continue
        workstream = record.intent["workstream"]
        if workstream not in workstreams:
            report.add(
                "GOV-WORKSTREAM-001", f"Active ticket {record.directory.name} declares unknown workstream '{workstream}'.",
                "Choose a workstream declared in the pinned governance manifest and obtain fresh plan approval.", [intent_path],
                {"workstream": workstream, "knownWorkstreams": sorted(workstreams)},
            )
            continue
        valid.append(record)
    return valid


def check_workstream_limits(
    root: Path,
    valid_active: list[TicketRecord],
    limit: int,
    report: Report,
) -> None:
    grouped: dict[str, list[TicketRecord]] = {}
    for record in valid_active:
        grouped.setdefault(record.intent["workstream"], []).append(record)  # type: ignore[index]
    for workstream, members in sorted(grouped.items()):
        if len(members) > limit:
            report.add(
                "GOV-WORKSTREAM-002", f"Workstream '{workstream}' has {len(members)} active tickets; limit is {limit}.",
                "Keep one active implementation ticket in this workstream or close/block-route the competing scope.",
                [rel(root, member.directory) for member in members],
                {"workstream": workstream, "tickets": [member.directory.name for member in members], "limit": limit},
            )


def dependency_graph(
    root: Path,
    records: list[TicketRecord],
    config: dict[str, Any],
    report: Report,
) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for record in records:
        if record.intent and record.intent.get("schema") in {"new-project.intent/v2", "new-project.intent/v3"}:
            graph[record.directory.name] = list(record.intent["dependsOn"])
            if record.directory.name in record.intent["dependsOn"] or record.directory.name in record.intent["conflictsWith"]:
                report.add(
                    "GOV-DEPENDENCY-001", f"Ticket {record.directory.name} references itself as a dependency or conflict.",
                    "Remove the self-reference and keep only directed edges to other tickets.", [rel(root, record.directory / config["intentFile"])],
                )
    return graph


def find_dependency_cycle(graph: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycle: list[str] = []

    def visit(name: str, trail: list[str]) -> bool:
        if name in visiting:
            cycle.extend(trail[trail.index(name):] + [name])
            return True
        if name in visited:
            return False
        visiting.add(name)
        for dependency in graph.get(name, []):
            if dependency in graph and visit(dependency, [*trail, dependency]):
                return True
        visiting.remove(name)
        visited.add(name)
        return False

    for name in sorted(graph):
        if visit(name, [name]):
            return cycle
    return []


def check_dependency_cycle(graph: dict[str, list[str]], report: Report) -> None:
    cycle = find_dependency_cycle(graph)
    if cycle:
        report.add(
            "GOV-DEPENDENCY-001", "Ticket dependency graph contains a cycle.",
            "Break the cycle by choosing a directed implementation order or an explicit integration ticket.",
            [f"project/{item}/intent.json" for item in sorted(set(cycle))], {"cycle": cycle},
        )


def integration_reference_valid(record: TicketRecord | None, required_workstream: str) -> bool:
    return bool(
        record is not None
        and record.intent is not None
        and record.intent.get("schema") in {"new-project.intent/v2", "new-project.intent/v3"}
        and record.intent.get("workstream") == required_workstream
        and record.status != "CANCELLED"
    )


def check_active_relationships(
    root: Path,
    config: dict[str, Any],
    coordination: dict[str, Any],
    records: list[TicketRecord],
    active: list[TicketRecord],
    valid_active: list[TicketRecord],
    report: Report,
) -> None:
    closed_statuses = set(config.get("closedStatuses", []))
    by_name = {record.directory.name: record for record in records}
    active_names = {record.directory.name for record in active}
    conflict_pairs: set[tuple[str, str]] = set()
    integration_config = coordination["integration"]
    for record in valid_active:
        assert record.intent is not None
        for dependency in record.intent["dependsOn"]:
            prerequisite = by_name.get(dependency)
            if prerequisite is None or prerequisite.status not in closed_statuses:
                report.add(
                    "GOV-DEPENDENCY-002", f"Active ticket {record.directory.name} has unfinished or missing dependency {dependency}.",
                    "Complete the prerequisite or return the dependent ticket to a non-active planning backlog.",
                    [rel(root, record.directory / config["intentFile"])],
                    {"ticket": record.directory.name, "dependency": dependency, "dependencyStatus": prerequisite.status if prerequisite else None},
                )
        for conflict in record.intent["conflictsWith"]:
            if conflict in active_names:
                conflict_pairs.add(tuple(sorted((record.directory.name, conflict))))
        integration_name = record.intent["integrationTicket"]
        if integration_name is not None:
            integration_record = by_name.get(integration_name)
            valid_integration = integration_reference_valid(integration_record, integration_config["workstream"])
            if not valid_integration:
                report.add(
                    "GOV-INTEGRATION-001",
                    f"Ticket {record.directory.name} references an invalid integration ticket {integration_name}.",
                    "Reference an existing, non-cancelled ticket in the manifest-declared integration workstream.",
                    [rel(root, record.directory / config["intentFile"])],
                    {"ticket": record.directory.name, "integrationTicket": integration_name, "requiredWorkstream": integration_config["workstream"]},
                )
    for first, second in sorted(conflict_pairs):
        report.add(
            "GOV-CONFLICT-001", f"Conflicting tickets {first} and {second} are active together.",
            "Serialize the tickets or resolve the conflict through an approved integration plan.",
            [f"project/{first}/intent.json", f"project/{second}/intent.json"],
        )


def check_workstream_claims(
    root: Path,
    config: dict[str, Any],
    workstreams: dict[str, Any],
    governance_patterns: list[str],
    files: list[str],
    valid_active: list[TicketRecord],
    report: Report,
) -> None:
    for record in valid_active:
        assert record.intent is not None
        owned_paths = workstreams[record.intent["workstream"]]["ownedPaths"]
        implementation_patterns = [
            pattern for pattern in record.intent["allowedPaths"]
            if not matches(pattern, governance_patterns)
        ]
        unowned_patterns = [
            pattern for pattern in implementation_patterns
            if not any(pattern_covered_by(pattern, owned) for owned in owned_paths)
        ]
        unowned_claims = [
            path for path in files
            if not matches(path, governance_patterns)
            and matches(path, record.intent["allowedPaths"])
            and not matches(path, record.intent["forbiddenPaths"])
            and not matches(path, owned_paths)
        ]
        if unowned_patterns or unowned_claims:
            report.add(
                "GOV-WORKSTREAM-003", f"Ticket {record.directory.name} claims paths outside workstream '{record.intent['workstream']}'.",
                "Narrow allowedPaths or route the paths to their owning workstream/integration ticket and obtain fresh approval.",
                sorted({*unowned_patterns, *unowned_claims})[:20],
                {
                    "ticket": record.directory.name,
                    "workstream": record.intent["workstream"],
                    "ownedPaths": owned_paths,
                    "unownedPatterns": unowned_patterns,
                    "concretePathCount": len(unowned_claims),
                },
            )


def ticket_shared_files(
    first: TicketRecord,
    second: TicketRecord,
    files: list[str],
    governance_patterns: list[str],
) -> list[str]:
    assert first.intent is not None and second.intent is not None
    return [
        path for path in files
        if not matches(path, governance_patterns)
        and matches(path, first.intent["allowedPaths"])
        and not matches(path, first.intent["forbiddenPaths"])
        and matches(path, second.intent["allowedPaths"])
        and not matches(path, second.intent["forbiddenPaths"])
    ]


def ticket_overlapping_patterns(
    first: TicketRecord,
    second: TicketRecord,
    governance_patterns: list[str],
) -> list[str]:
    assert first.intent is not None and second.intent is not None
    first_patterns = [pattern for pattern in first.intent["allowedPaths"] if not matches(pattern, governance_patterns)]
    second_patterns = [pattern for pattern in second.intent["allowedPaths"] if not matches(pattern, governance_patterns)]
    return sorted({
        f"{first_pattern} <-> {second_pattern}"
        for first_pattern in first_patterns
        for second_pattern in second_patterns
        if patterns_may_overlap(first_pattern, second_pattern)
    })


def check_scope_overlaps(
    valid_active: list[TicketRecord],
    files: list[str],
    governance_patterns: list[str],
    report: Report,
) -> None:
    for index, first in enumerate(valid_active):
        for second in valid_active[index + 1:]:
            shared_files = ticket_shared_files(first, second, files, governance_patterns)
            overlapping_patterns = ticket_overlapping_patterns(first, second, governance_patterns)
            if shared_files or overlapping_patterns:
                report.add(
                    "GOV-WORKSTREAM-004",
                    f"Active ticket scopes overlap: {first.directory.name} and {second.directory.name}.",
                    "Narrow one allowedPaths declaration, serialize the work, or route the shared contract through integration.",
                    shared_files[:20],
                    {"tickets": [first.directory.name, second.directory.name], "overlappingPatterns": overlapping_patterns, "concretePathCount": len(shared_files)},
                )


def check_ticket_statuses(
    root: Path,
    config: dict[str, Any],
    records: list[TicketRecord],
    report: Report,
) -> None:
    allowed = set(config.get("activeStatuses", ACTIVE_DEFAULT))
    allowed.update(config.get("nonActiveStatuses", []))
    allowed.update(config.get("closedStatuses", []))
    for record in records:
        if record.status not in allowed:
            report.add(
                "GOV-STATUS-001",
                f"Ticket {record.directory.name} has unknown status '{record.status or 'MISSING'}'.",
                "Use a status declared in activeStatuses, nonActiveStatuses or closedStatuses.",
                [rel(root, record.directory / "README.md")],
                {
                    "ticket": record.directory.name,
                    "status": record.status,
                    "allowedStatuses": sorted(allowed),
                },
            )


def check_coordination(
    root: Path,
    manifest: dict[str, Any],
    records: list[TicketRecord],
    changed: list[str],
    report: Report,
) -> None:
    coordination = manifest.get("coordination")
    if not isinstance(coordination, dict):
        return
    config = manifest["ticket"]
    check_ticket_statuses(root, config, records, report)
    active = [record for record in records if record.status in set(config.get("activeStatuses", ACTIVE_DEFAULT))]
    workstreams = coordination["workstreams"]
    valid_active = valid_active_tickets(root, config, active, workstreams, report)
    check_workstream_limits(root, valid_active, coordination["maxActiveTicketsPerWorkstream"], report)
    check_dependency_cycle(dependency_graph(root, records, config, report), report)
    check_active_relationships(root, config, coordination, records, active, valid_active, report)
    files = repository_files(root, changed)
    governance_patterns = manifest["governancePaths"]
    check_workstream_claims(root, config, workstreams, governance_patterns, files, valid_active, report)
    if coordination["rejectActiveScopeOverlap"]:
        check_scope_overlaps(valid_active, files, governance_patterns, report)


def check_required_files(root: Path, manifest: dict[str, Any], report: Report) -> None:
    missing = []
    for raw in manifest["requiredFiles"]:
        try:
            if not safe_repo_path(root, raw).exists():
                missing.append(raw)
        except ValueError:
            missing.append(raw)
    if missing:
        report.add("GOV-BOOT-001", "Required target-repository files are missing.", "Run the approved new-project bootstrap before implementation.", missing)

    docker = manifest["docker"]
    if docker["required"]:
        def first_repo_file(names: list[str]) -> str | None:
            for name in names:
                try:
                    if safe_repo_path(root, name).is_file():
                        return name
                except ValueError:
                    continue
            return None

        dockerfile = first_repo_file(docker["dockerfiles"])
        compose = first_repo_file(docker["composeFiles"])
        if dockerfile is None or compose is None:
            report.add(
                "GOV-DOCKER-001", "Required Dockerfile or Compose declaration is missing.",
                "Add a pinned Docker runtime and validate its Compose configuration.",
                [*([] if dockerfile else docker["dockerfiles"]), *([] if compose else docker["composeFiles"])],
            )


def immutable_image_reference(reference: str) -> bool:
    return reference == "scratch" or IMMUTABLE_IMAGE_RE.fullmatch(reference) is not None


def dockerfile_image_references(path: Path) -> list[tuple[int, str]]:
    references: list[tuple[int, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        tokens = line.strip().split()
        if not tokens or tokens[0].upper() != "FROM":
            continue
        image = next((token for token in tokens[1:] if not token.startswith("--")), "")
        references.append((line_number, image))
    return references


def compose_image_references(path: Path) -> list[tuple[int, str]]:
    references: list[tuple[int, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = COMPOSE_IMAGE_RE.match(line)
        if match:
            references.append((line_number, next(value for value in match.groups() if value is not None)))
    return references


def check_docker_image_references(root: Path, manifest: dict[str, Any], report: Report) -> None:
    docker = manifest["docker"]
    if not docker["required"]:
        return
    invalid: list[tuple[str, int, str]] = []
    for raw_path in docker["dockerfiles"]:
        path = safe_repo_path(root, raw_path)
        if path.is_file():
            invalid.extend(
                (raw_path, line_number, reference)
                for line_number, reference in dockerfile_image_references(path)
                if not immutable_image_reference(reference)
            )
    for raw_path in docker["composeFiles"]:
        path = safe_repo_path(root, raw_path)
        if path.is_file():
            invalid.extend(
                (raw_path, line_number, reference)
                for line_number, reference in compose_image_references(path)
                if not immutable_image_reference(reference)
            )
    if invalid:
        report.add(
            "GOV-DOCKER-002",
            "Docker image references are not pinned to immutable SHA-256 digests.",
            "Pin external images as name@sha256:<64 lowercase hex>; for a local-only Compose build, omit image so no mutable tag can be pulled.",
            [f"{path}:{line_number}" for path, line_number, _ in invalid],
            {"references": [reference for _, _, reference in invalid]},
        )


def check_stacks(root: Path, manifest: dict[str, Any], profiles_path: Path | None, report: Report) -> None:
    stacks = manifest.get("stacks", [])
    if not stacks or profiles_path is None:
        return
    try:
        profiles = load_json(profiles_path)["profiles"]
        if not isinstance(profiles, dict):
            raise TypeError("profiles must be an object")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        report.add("GOV-MANIFEST-001", "Stack profile catalog is unreadable.", "Restore the pinned stack profile catalog.", [])
        return
    for stack in stacks:
        profile = profiles.get(stack)
        if not isinstance(profile, dict):
            report.add("GOV-STACK-001", f"Unknown stack profile: {stack}", "Declare a profile published by the pinned governance standard.", [])
            continue
        markers = profile.get("anyFiles", [])
        if not string_list(markers) or not all(relative_pattern(marker) for marker in markers):
            report.add("GOV-MANIFEST-001", f"Stack profile '{stack}' has invalid markers.", "Restore the pinned stack profile catalog.", [])
            continue
        if markers and not any(safe_repo_path(root, marker).exists() for marker in markers):
            report.add("GOV-STACK-001", f"Declared stack '{stack}' has no recognized project marker.", "Add the stack marker or remove the inaccurate stack declaration.", markers)


def check_ticket_content(root: Path, directories: list[Path], config: dict[str, Any], report: Report) -> None:
    for directory in directories:
        status, _ = parse_ticket_state(directory / "README.md")
        if status in set(config["activeStatuses"]):
            missing = [rel(root, directory / item) for item in config["requiredFiles"] if not (directory / item).is_file()]
            for pattern in config["requiredAgentFiles"]:
                if not any(directory.glob(pattern)):
                    missing.append(rel(root, directory / pattern))
            if missing:
                report.add("GOV-TICKET-003", f"Active ticket {directory.name} is missing required governance files.", "Complete the ticket scaffold before implementation.", missing)
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            mode_executable = bool(path.stat().st_mode & 0o111)
            if path.suffix.lower() in EXECUTABLE_SUFFIXES or mode_executable:
                report.add(
                    "GOV-TICKET-004", f"Executable content is forbidden in ticket directory: {rel(root, path)}",
                    "Move implementation to the repository's normal source, test or scripts directory.", [rel(root, path)],
                )


def probable_secret_fields(text: str) -> list[str]:
    fields = []
    for match in SECRET_RE.finditer(text):
        shell_assignment = text[match.end(2):].startswith("=")
        environment_reference = re.match(r"^[A-Z][A-Z0-9_]*=", match.group(2))
        if not shell_assignment and not environment_reference and not SAFE_SECRET_VALUES.match(match.group(2)):
            fields.append(match.group(1))
    return sorted(set(fields))


def check_changed_file(root: Path, raw: str, report: Report) -> None:
    try:
        path = safe_repo_path(root, raw)
    except ValueError:
        return
    if not path.is_file() or path.stat().st_size > 1_000_000:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    secrets = probable_secret_fields(text)
    if secrets:
        report.add(
            "GOV-SECRET-001", f"Probable secret assignment detected in {raw}.",
            "Remove and rotate the secret; keep only placeholders in tracked files.", [raw], {"fieldNames": secrets},
        )
    if raw.startswith(("project/ticket-", ".governance/")) and LOCAL_PATH_RE.search(text):
        report.add(
            "GOV-PATH-001", f"Machine-local absolute path detected in governed artifact: {raw}",
            "Replace it with a repository-relative path before publication.", [raw],
        )
    if fnmatch.fnmatchcase(raw, "project/ticket-*/decisions.md"):
        check_decision_log_file(root, raw, text, report)


def check_decision_log_file(root: Path, raw: str, text: str, report: Report) -> None:
    """Validate recomputable decision records (C-DECISION / ticket-031)."""
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from decision_record import parse_dsl_record, split_decision_blocks, validate_record
    except ImportError:
        report.add(
            "GOV-DECISION-002",
            f"Cannot import decision_record helper while validating {raw}.",
            "Keep scripts/decision_record.py next to governance_check.py.",
            [raw],
        )
        return
    blocks = split_decision_blocks(text)
    if not blocks:
        report.add(
            "GOV-DECISION-001",
            f"Decision log {raw} has no DECISION records.",
            "Append a fenced ```dsl DECISION record or remove the empty log.",
            [raw],
        )
        return
    for block in blocks:
        try:
            record = parse_dsl_record(block)
        except ValueError as error:
            report.add(
                "GOV-DECISION-002",
                f"Decision record in {raw} is not parseable: {error}",
                "Store deterministic INPUT lines and a complete DECISION shape.",
                [raw],
            )
            continue
        for error in validate_record(record):
            code = "GOV-DECISION-002"
            if "GOV-DECISION-003" in error or "ADVISORY" in error:
                code = "GOV-DECISION-003"
            elif "GOV-DECISION-004" in error or "replayed verdict" in error:
                code = "GOV-DECISION-004"
            elif "GOV-DECISION-001" in error:
                code = "GOV-DECISION-001"
            report.add(
                code,
                f"Decision record in {raw}: {error}",
                "Fix the record so INPUT + APPLIED_RULE recompute VERDICT with DETERMINISTIC authority.",
                [raw],
            )


def check_changed_content(root: Path, changed: list[str], actor: str, trusted_human_change: bool, report: Report) -> None:
    human_paths = [path for path in changed if fnmatch.fnmatchcase(path, "project/ticket-*/user-*.md")]
    if human_paths and (actor != "human" or not trusted_human_change):
        report.add(
            "GOV-OWNER-001", "Human-owned participant content changed without trusted human intake evidence.",
            "Revert the agent edit or have the human owner submit it through the trusted intake boundary.", human_paths,
        )
    for raw in changed:
        check_changed_file(root, raw, report)


def check_declared_delivery_budget(
    policy: dict[str, Any],
    delivery: dict[str, Any],
    record: TicketRecord,
    intent_path: str,
    report: Report,
) -> None:
    complexity_limit = 10 if delivery["complexity"] == "XS" else policy["maxActiveMinutes"]
    declared_limits = delivery["budgets"]
    policy_limits = {
        "maxImplementationFiles": policy["maxImplementationFiles"],
        "maxAffectedComponents": policy["maxAffectedComponents"],
        "maxPublicInterfaceChanges": policy["maxPublicInterfaceChanges"],
        "maxRuntimeDependencies": policy["maxRuntimeDependencies"],
    }
    violations = {
        name: {"declared": declared_limits[name], "policy": limit}
        for name, limit in policy_limits.items()
        if declared_limits[name] > limit
    }
    if (
        delivery["complexity"] not in policy["allowedComplexityClasses"]
        or delivery["estimatedMinutes"] > policy["maxActiveMinutes"]
        or delivery["estimatedMinutes"] > complexity_limit
        or violations
    ):
        report.add(
            "GOV-DELIVERY-001",
            f"Ticket {record.directory.name} exceeds the approved delivery class or policy budget.",
            "Split the outcome into dependent XS/S slices; do not widen the current ticket or PR.",
            [intent_path],
            {
                "complexity": delivery["complexity"],
                "estimatedMinutes": delivery["estimatedMinutes"],
                "maxActiveMinutes": policy["maxActiveMinutes"],
                "budgetViolations": violations,
            },
        )


def check_delivery_timebox(
    policy: dict[str, Any],
    record: TicketRecord,
    intent_path: str,
    elapsed_minutes: int | None,
    report: Report,
) -> None:
    if elapsed_minutes is not None:
        if elapsed_minutes >= policy["maxActiveMinutes"]:
            report.add(
                "GOV-DELIVERY-001",
                f"Ticket {record.directory.name} reached its {policy['maxActiveMinutes']}-minute implementation timebox.",
                "Stop implementation, preserve evidence and plan unfinished work as an explicit dependent slice.",
                [intent_path], {"elapsedMinutes": elapsed_minutes},
            )
        elif elapsed_minutes >= policy["checkpointMinutes"]:
            report.add(
                "GOV-DELIVERY-002",
                f"Ticket {record.directory.name} reached its delivery checkpoint.",
                "Record completed and remaining scope now; stop at the hard timebox instead of expanding the diff.",
                [intent_path], {"elapsedMinutes": elapsed_minutes, "stopAtMinutes": policy["maxActiveMinutes"]},
                severity="warning",
            )


def check_delivery_base(
    root: Path,
    policy: dict[str, Any],
    delivery: dict[str, Any],
    record: TicketRecord,
    intent_path: str,
    base: str | None,
    report: Report,
) -> None:
    if delivery["targetBranch"] not in policy["targetBranches"]:
        report.add(
            "GOV-BASE-001",
            f"Ticket {record.directory.name} targets unapproved branch '{delivery['targetBranch']}'.",
            "Choose a manifest-approved target branch and obtain fresh approval for its exact base SHA.",
            [intent_path], {"allowedTargets": policy["targetBranches"]},
        )

    accepted_sha = delivery["acceptedBaseSha"]
    observed_base = None
    if base:
        try:
            observed_base = git_output(root, ["rev-parse", f"{base}^{{commit}}"]).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            report.add(
                "GOV-BASE-001", "The supplied base revision cannot be resolved.",
                "Fetch the complete target history and rerun against the exact accepted base SHA.",
                [intent_path], {"suppliedBase": base, "acceptedBaseSha": accepted_sha},
            )
        if observed_base and observed_base != accepted_sha:
            report.add(
                "GOV-BASE-001", f"Ticket {record.directory.name} approval is bound to a stale or different base SHA.",
                "Refresh the branch, update architecture/scope evidence and obtain fresh approval before continuing.",
                [intent_path], {"acceptedBaseSha": accepted_sha, "observedBaseSha": observed_base},
            )

    target_refs = [
        f"refs/remotes/origin/{delivery['targetBranch']}",
        f"refs/heads/{delivery['targetBranch']}",
    ]
    for target_ref in target_refs:
        try:
            current_target = git_output(root, ["rev-parse", "--verify", f"{target_ref}^{{commit}}"]).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        if current_target != accepted_sha:
            report.add(
                "GOV-BASE-001", f"Target branch '{delivery['targetBranch']}' moved after ticket approval.",
                "Refresh from the target, re-run conflict and validation checks, then obtain fresh approval if intent or architecture changed.",
                [intent_path], {"acceptedBaseSha": accepted_sha, "currentTargetSha": current_target, "targetRef": target_ref},
            )
        break


def map_implementation_components(
    implementation: list[str],
    components: list[dict[str, Any]],
) -> tuple[list[str], list[str], set[str]]:
    unmapped: list[str] = []
    multiply_mapped: list[str] = []
    touched_components: set[str] = set()
    for path in implementation:
        owners = [component["name"] for component in components if matches(path, component["paths"])]
        if not owners:
            unmapped.append(path)
        elif len(owners) > 1:
            multiply_mapped.append(path)
        else:
            touched_components.add(owners[0])
    return unmapped, multiply_mapped, touched_components


def check_delivery_architecture(
    policy: dict[str, Any],
    delivery: dict[str, Any],
    record: TicketRecord,
    implementation: list[str],
    intent_path: str,
    report: Report,
) -> set[str]:
    declared_limits = delivery["budgets"]
    architecture = delivery["architecture"]
    components = architecture["components"]
    component_overflow = len(components) > min(
        declared_limits["maxAffectedComponents"], policy["maxAffectedComponents"],
    )
    interface_overflow = len(architecture["interfaceChanges"]) > min(
        declared_limits["maxPublicInterfaceChanges"], policy["maxPublicInterfaceChanges"],
    )
    dependency_overflow = len(delivery["runtimeDependencies"]) > min(
        declared_limits["maxRuntimeDependencies"], policy["maxRuntimeDependencies"],
    )
    unmapped, multiply_mapped, touched_components = map_implementation_components(implementation, components)
    if component_overflow or unmapped or multiply_mapped:
        report.add(
            "GOV-ARCHITECTURE-001",
            f"Ticket {record.directory.name} has unresolved or ambiguous component ownership.",
            "Decide component ownership before EDIT; map every changed implementation path to exactly one approved component.",
            [intent_path, *unmapped, *multiply_mapped],
            {
                "declaredComponents": [component["name"] for component in components],
                "touchedComponents": sorted(touched_components),
                "unmappedPaths": unmapped,
                "multiplyMappedPaths": multiply_mapped,
            },
        )
    check_actual_delivery_budget(
        policy, delivery, record, implementation, touched_components,
        interface_overflow, dependency_overflow, report,
    )
    return touched_components


def check_actual_delivery_budget(
    policy: dict[str, Any],
    delivery: dict[str, Any],
    record: TicketRecord,
    implementation: list[str],
    touched_components: set[str],
    interface_overflow: bool,
    dependency_overflow: bool,
    report: Report,
) -> None:
    declared_limits = delivery["budgets"]
    implementation_limit = min(declared_limits["maxImplementationFiles"], policy["maxImplementationFiles"])
    public_paths = [path for path in implementation if matches(path, policy["publicInterfacePaths"])]
    dependency_paths = [path for path in implementation if path in policy["dependencyManifestPaths"]]
    if (
        len(implementation) > implementation_limit
        or len(touched_components) > declared_limits["maxAffectedComponents"]
        or interface_overflow
        or dependency_overflow
        or len(public_paths) > declared_limits["maxPublicInterfaceChanges"]
    ):
        report.add(
            "GOV-BUDGET-001",
            f"Actual diff for {record.directory.name} exceeds its approved complexity budget.",
            "Stop and split the remaining outcome into an explicitly dependent ticket; do not enlarge the current PR.",
            implementation,
            {
                "implementationFiles": len(implementation),
                "implementationFileLimit": implementation_limit,
                "touchedComponents": sorted(touched_components),
                "publicInterfacePaths": public_paths,
                "dependencyManifestPaths": dependency_paths,
                "declaredRuntimeDependencies": delivery["runtimeDependencies"],
            },
        )


def check_integration_ownership(
    manifest: dict[str, Any],
    delivery: dict[str, Any],
    record: TicketRecord,
    intent_path: str,
    report: Report,
) -> None:
    integration_workstream = manifest["coordination"]["integration"]["workstream"]
    architecture = delivery["architecture"]
    if (architecture["responsibilityChanges"] or architecture["dataChanges"]) and record.intent["workstream"] != integration_workstream:
        report.add(
            "GOV-ARCHITECTURE-001",
            "Responsibility or persistent-data movement is not owned by an integration slice.",
            "Create and approve a <=30-minute integration-workstream slice before changing component ownership or persistent data.",
            [intent_path],
            {"workstream": record.intent["workstream"], "requiredWorkstream": integration_workstream},
        )


def check_delivery_gate(
    root: Path,
    manifest: dict[str, Any],
    record: TicketRecord,
    implementation: list[str],
    base: str | None,
    elapsed_minutes: int | None,
    report: Report,
) -> None:
    policy = manifest.get("delivery")
    if not isinstance(policy, dict) or not policy.get("requiredForImplementation"):
        return
    assert record.intent is not None
    delivery = record.intent.get("delivery")
    intent_path = rel(root, record.directory / manifest["ticket"]["intentFile"])
    if not isinstance(delivery, dict):
        report.add(
            "GOV-DELIVERY-001",
            f"Implementation ticket {record.directory.name} has no bounded delivery contract.",
            "Return to WAIT_FOR_APPROVAL, declare one <=30-minute XS/S outcome with architecture and validation evidence, then obtain fresh approval.",
            [intent_path],
        )
        return
    check_declared_delivery_budget(policy, delivery, record, intent_path, report)
    check_delivery_timebox(policy, record, intent_path, elapsed_minutes, report)
    check_delivery_base(root, policy, delivery, record, intent_path, base, report)
    check_delivery_architecture(policy, delivery, record, implementation, intent_path, report)
    check_integration_ownership(manifest, delivery, record, intent_path, report)


def ticket_owns_implementation(record: TicketRecord, implementation: list[str]) -> bool:
    return bool(
        record.intent is not None
        and record.intent.get("schema") in {"new-project.intent/v2", "new-project.intent/v3"}
        and all(
            matches(path, record.intent["allowedPaths"])
            and not matches(path, record.intent["forbiddenPaths"])
            for path in implementation
        )
    )


def ticket_path_owners(active: list[TicketRecord], implementation: list[str]) -> dict[str, list[str]]:
    return {
        path: [
            record.directory.name for record in active
            if record.intent is not None
            and matches(path, record.intent["allowedPaths"])
            and not matches(path, record.intent["forbiddenPaths"])
        ]
        for path in implementation
    }


def select_change_ticket(
    root: Path,
    active: list[TicketRecord],
    coordination: Any,
    implementation: list[str],
    report: Report,
) -> TicketRecord | None:
    if not active:
        report.add(
            "GOV-TICKET-001", "Implementation paths changed without an active ticket.",
            "Create the next target-repository ticket, publish its plan and obtain approval before editing implementation.", implementation,
        )
        return None
    if not isinstance(coordination, dict):
        if len(active) > 1:
            report.add(
                "GOV-TICKET-002", "More than one active ticket exists.",
                "Continue the existing ticket or close/cancel it before creating another.",
                [rel(root, item.directory) for item in active], {"tickets": [item.directory.name for item in active]},
            )
            return None
        return active[0]
    candidates = [record for record in active if ticket_owns_implementation(record, implementation)]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates and len(active) == 1:
        return active[0]
    path_owners = ticket_path_owners(active, implementation)
    report.add(
        "GOV-TICKET-005", "Implementation diff does not resolve to exactly one active ticket.",
        "Use one ticket per branch/PR, narrow allowedPaths, or create an approved integration ticket for the combined diff.",
        implementation, {"candidateTickets": [record.directory.name for record in candidates], "pathOwners": path_owners},
    )
    return None


def check_selected_ticket_state(
    root: Path,
    config: dict[str, Any],
    selected: TicketRecord,
    implementation: list[str],
    base: str | None,
    head: str,
    governance_patterns: list[str],
    report: Report,
) -> None:
    directory = selected.directory
    workflow = selected.workflow
    check_history_order(
        root, base=base, head=head, ticket_name=directory.name,
        ticket_root=config["root"],
        intent_path=config["intentFile"], governance_patterns=governance_patterns,
        report=report,
    )
    if workflow not in set(config["implementationStates"]):
        report.add(
            "GOV-INTENT-001", f"Ticket {directory.name} is in workflow state {workflow or 'UNKNOWN'}, not an implementation state.",
            "Keep the change plan-only until explicit approval moves the ticket to EDIT.", implementation,
        )


def check_workstream_change_scope(
    records: list[TicketRecord],
    coordination: dict[str, Any],
    selected: TicketRecord,
    implementation: list[str],
    report: Report,
) -> None:
    intent = selected.intent
    assert intent is not None
    workstream = coordination["workstreams"].get(intent["workstream"])
    if isinstance(workstream, dict):
        unowned = [path for path in implementation if not matches(path, workstream["ownedPaths"])]
        if unowned:
            report.add(
                "GOV-WORKSTREAM-003", f"Changed paths are not owned by workstream '{intent['workstream']}'.",
                "Move the change to its owning workstream or create and approve an integration ticket; do not widen ownership retroactively.",
                unowned, {"ticket": selected.directory.name, "workstream": intent["workstream"], "ownedPaths": workstream["ownedPaths"]},
            )
    integration = coordination["integration"]
    shared = [path for path in implementation if matches(path, integration["requiredForPaths"])]
    if shared and intent["workstream"] != integration["workstream"]:
        integration_name = intent["integrationTicket"]
        integration_record = next((record for record in records if record.directory.name == integration_name), None)
        report.add(
            "GOV-INTEGRATION-001", "Shared contract paths must be changed by the integration-workstream ticket.",
            "Move the shared-path diff to the referenced integration ticket's branch; integrationTicket coordinates work but does not transfer path ownership.",
            shared,
            {
                "ticket": selected.directory.name,
                "integrationTicket": integration_name,
                "validIntegrationReference": integration_reference_valid(integration_record, integration["workstream"]),
                "requiredWorkstream": integration["workstream"],
            },
        )


def check_selected_ticket_intent(
    root: Path,
    manifest: dict[str, Any],
    records: list[TicketRecord],
    selected: TicketRecord,
    implementation: list[str],
    base: str | None,
    elapsed_minutes: int | None,
    report: Report,
) -> None:
    directory = selected.directory
    config = manifest["ticket"]
    intent_path = directory / config["intentFile"]
    intent, error = selected.intent, selected.intent_error
    if error:
        report.add("GOV-INTENT-002", f"Ticket intent is invalid: {error}", "Create a valid intent file before implementation.", [rel(root, intent_path)])
    else:
        outside = [path for path in implementation if not matches(path, intent["allowedPaths"]) or matches(path, intent["forbiddenPaths"])]
        if outside:
            report.add(
                "GOV-SCOPE-001", "Changed implementation paths are outside the ticket intent.",
                "Revert the paths or return to PLAN, expand allowedPaths and obtain fresh approval.", outside,
                {"ticket": directory.name, "allowedPaths": intent["allowedPaths"]},
            )
        coordination = manifest.get("coordination")
        if isinstance(coordination, dict) and intent.get("schema") in {"new-project.intent/v2", "new-project.intent/v3"}:
            check_workstream_change_scope(records, coordination, selected, implementation, report)
        if intent is not None:
            check_delivery_gate(root, manifest, selected, implementation, base, elapsed_minutes, report)


def approval_subject_valid(evidence: Any) -> bool:
    required = {
        "schema", "source", "repository", "pullRequest", "headSha", "ticket",
        "actor", "verification",
    }
    return (
        isinstance(evidence, dict)
        and set(evidence) == required
        and evidence.get("schema") == "new-project.approval-evidence/v1"
        and evidence.get("source") in {
            "github-review", "github-app-review", "signed-attestation",
        }
        and isinstance(evidence.get("repository"), str)
        and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", evidence["repository"]) is not None
        and isinstance(evidence.get("pullRequest"), int)
        and not isinstance(evidence.get("pullRequest"), bool)
        and evidence["pullRequest"] >= 1
        and isinstance(evidence.get("headSha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", evidence["headSha"]) is not None
        and isinstance(evidence.get("ticket"), str)
        and re.fullmatch(r"ticket-[0-9]{3}", evidence["ticket"]) is not None
    )


def approval_actor_valid(actor: Any) -> bool:
    return (
        isinstance(actor, dict)
        and set(actor) == {"login", "type"}
        and isinstance(actor.get("login"), str)
        and bool(actor["login"])
        and actor.get("type") in {"User", "Bot", "Workflow"}
    )


def approval_verification_valid(verification: Any) -> bool:
    return (
        isinstance(verification, dict)
        and {"method", "verified"} <= set(verification)
        and set(verification) <= {"method", "verified", "issuer", "predicateType"}
        and verification.get("method") in {
            "github-api-allowlist", "github-attestation", "sigstore",
        }
        and verification.get("verified") is True
    )


def approval_authority_valid(
    evidence: dict[str, Any],
    manifest: dict[str, Any],
) -> bool:
    source = evidence["source"]
    actor = evidence["actor"]
    verification = evidence["verification"]
    method = verification["method"]
    if source == "github-review":
        return actor["type"] == "User" and method == "github-api-allowlist"
    if source == "github-app-review":
        return (
            actor["type"] == "Bot"
            and actor["login"].endswith("[bot]")
            and method == "github-api-allowlist"
        )
    approval_config = manifest.get("approvalEvidence") or {}
    expected_predicate = approval_config.get(
        "signedAttestationPredicateType",
        "https://wellmanifest.dev/attestations/validator/v1",
    )
    return (
        actor["type"] in {"Bot", "Workflow"}
        and method in {"github-attestation", "sigstore"}
        and isinstance(verification.get("issuer"), str)
        and bool(verification["issuer"])
        and verification.get("predicateType") == expected_predicate
    )


def approval_binding_mismatches(
    evidence: dict[str, Any],
    expected_repository: str | None,
    expected_pull_request: int | None,
    expected_head: str | None,
) -> tuple[bool, dict[str, dict[str, Any]]]:
    missing = (
        expected_repository is None
        or expected_pull_request is None
        or expected_head is None
        or re.fullmatch(r"[0-9a-f]{40}", expected_head or "") is None
    )
    expected = {
        "repository": expected_repository,
        "pullRequest": expected_pull_request,
        "headSha": expected_head,
    }
    mismatches = {
        name: {"evidence": evidence[name], "expected": value}
        for name, value in expected.items()
        if evidence[name] != value
    }
    return missing, mismatches


def load_external_approval_evidence(
    root: Path,
    raw_path: str | None,
    report: Report,
) -> Any | None:
    if not raw_path:
        return None
    expanded = Path(raw_path).expanduser()
    if not expanded.is_absolute():
        expanded = Path.cwd() / expanded
    try:
        path = expanded.parent.resolve(strict=True) / expanded.name
    except OSError as error:
        report.add(
            "GOV-APPROVAL-003", f"Approval evidence path is unreadable: {error}",
            "Have the protected approval resolver create a valid v1 evidence document outside the checkout.",
        )
        return None
    if path.is_relative_to(root):
        report.add(
            "GOV-APPROVAL-003",
            "Approval evidence is controlled by the pull-request checkout.",
            "Create evidence outside the checkout from a protected workflow after API or signature verification.",
            [rel(root, path)],
        )
        return None
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if no_follow is None:
        report.add(
            "GOV-APPROVAL-003",
            "Approval evidence cannot be opened safely on this platform.",
            "Use a validator platform that supports no-follow file opens for external approval evidence.",
        )
        return None
    descriptor = -1
    try:
        flags = os.O_RDONLY | no_follow | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(path, flags)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("approval evidence is not a regular file")
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            descriptor = -1
            evidence = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        report.add(
            "GOV-APPROVAL-003", f"Approval evidence is unreadable: {error}",
            "Have the protected approval resolver create a valid v1 evidence document outside the checkout.",
        )
        return None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return evidence


def approval_evidence(
    root: Path,
    raw_path: str | None,
    manifest: dict[str, Any],
    expected_repository: str | None,
    expected_pull_request: int | None,
    expected_head: str | None,
    report: Report,
) -> dict[str, Any] | None:
    evidence = load_external_approval_evidence(root, raw_path, report)
    if evidence is None:
        return None
    actor = evidence.get("actor") if isinstance(evidence, dict) else None
    verification = evidence.get("verification") if isinstance(evidence, dict) else None
    if not (
        approval_subject_valid(evidence)
        and approval_actor_valid(actor)
        and approval_verification_valid(verification)
    ):
        report.add(
            "GOV-APPROVAL-003", "Approval evidence does not conform to new-project.approval-evidence/v1.",
            "Regenerate evidence with the protected resolver and the pinned approval-evidence schema.",
        )
        return None
    missing, mismatches = approval_binding_mismatches(
        evidence, expected_repository, expected_pull_request, expected_head,
    )
    if missing or mismatches:
        report.add(
            "GOV-APPROVAL-004",
            "Approval evidence is not bound to the current repository, pull request and HEAD.",
            "Pass the current protected event bindings and request a fresh approval for the exact HEAD.",
            evidence={"missingExpectedBinding": missing, "mismatches": mismatches},
        )
        return None
    if not approval_authority_valid(evidence, manifest):
        report.add(
            "GOV-APPROVAL-005",
            "Approval actor or verification method is not valid for the claimed source.",
            "Use an allowlisted User, an allowlisted GitHub App bot login, or a signature-verified trusted attestation issuer.",
            evidence={
                "source": evidence["source"],
                "actor": evidence["actor"],
                "verification": evidence["verification"],
            },
        )
        return None
    return evidence


def check_change_approval(
    root: Path,
    manifest: dict[str, Any],
    selected: TicketRecord,
    approval_source: str | None,
    approved_ticket: str | None,
    report: Report,
) -> None:
    directory = selected.directory
    trusted = set(manifest["trustedApprovalSources"])
    if approval_source not in trusted:
        report.add(
            "GOV-APPROVAL-001", "No trusted external approval was supplied for implementation.",
            "Require an approving CODEOWNER GitHub review or signed attestation; Markdown status alone is not trusted.",
            [rel(root, directory / "README.md")], {"suppliedSource": approval_source, "trustedSources": sorted(trusted)},
        )
    approved_tickets = set((approved_ticket or "").split(",")) - {""}
    if directory.name not in approved_tickets:
        report.add(
            "GOV-APPROVAL-002", "Trusted approval does not identify the active ticket.",
            "Approve the current ticket after reviewing its latest intent and implementation diff.",
            [rel(root, directory)], {"activeTicket": directory.name, "approvedTickets": sorted(approved_tickets)},
        )


def resolve_change_approval(
    root: Path,
    manifest: dict[str, Any],
    selected: TicketRecord,
    approval_source: str | None,
    approved_ticket: str | None,
    approval_evidence_path: str | None,
    expected_repository: str | None,
    expected_pull_request: int | None,
    expected_head: str | None,
    report: Report,
) -> None:
    supplied = approval_evidence(
        root, approval_evidence_path, manifest, expected_repository,
        expected_pull_request, expected_head, report,
    )
    if supplied is not None:
        approval_source = supplied["source"]
        approved_ticket = supplied["ticket"]
    elif approval_source in {"github-app-review", "signed-attestation"}:
        report.add(
            "GOV-APPROVAL-003",
            f"Approval source {approval_source} requires external v1 evidence.",
            "Create bound evidence outside the checkout after allowlist or signature verification.",
        )
    check_change_approval(
        root, manifest, selected, approval_source, approved_ticket, report,
    )


def git_revision_file(root: Path, revision: str, raw_path: str) -> bytes | None:
    try:
        return git_output(root, ["show", f"{revision}:{raw_path}"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def package_entry(item: Any) -> tuple[str, str, str]:
    if not isinstance(item, dict) or set(item) != {"source", "target", "strategy", "executable"}:
        raise ValueError("package manifest entry fields are invalid")
    source, target = item.get("source"), item.get("target")
    if not isinstance(source, str) or not isinstance(target, str):
        raise TypeError("package manifest entry is invalid")
    if not relative_pattern(source) or not relative_pattern(target):
        raise ValueError("package manifest entry is invalid")
    if item.get("strategy") not in {"managed", "seed", "extendable"}:
        raise ValueError("package manifest entry is invalid")
    if not isinstance(item.get("executable"), bool):
        raise TypeError("package manifest entry is invalid")
    if item.get("strategy") == "extendable" and (
        source != "governance/manifest.default.json"
        or target != ".governance/manifest.json"
        or item.get("executable")
    ):
        raise ValueError("package manifest extendable target is invalid")
    return source, target, item["strategy"]


def package_strategies(content: bytes) -> dict[str, str]:
    document = json.loads(content)
    if not isinstance(document, dict) or set(document) != {"schema", "files"}:
        raise ValueError("package manifest fields are invalid")
    if document.get("schema") != "new-project.package-manifest/v1" or not isinstance(document.get("files"), list):
        raise ValueError("package manifest schema is invalid")
    strategies: dict[str, str] = {}
    for item in document["files"]:
        _source, target, strategy = package_entry(item)
        if target in strategies:
            raise ValueError("package manifest targets must be unique")
        strategies[target] = strategy
    if not strategies:
        raise ValueError("package manifest is empty")
    return strategies


def adoption_standard_binding_is_valid(document: dict[str, Any], expected_revision: str) -> bool:
    standard = document.get("standard")
    if document.get("schema") != "new-project.lock/v1" or not isinstance(standard, dict):
        return False
    fields = {"id", "version", "sourceRepository", "sourceRevision", "publicationStatus"}
    if set(standard) != fields:
        return False
    expected = {
        "id": "wellmanifest/new-project",
        "sourceRepository": "wellmanifest/new-project",
        "sourceRevision": expected_revision,
        "publicationStatus": "published",
    }
    if any(standard.get(key) != value for key, value in expected.items()):
        return False
    version = standard.get("version")
    return isinstance(version, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is not None


def adoption_lock(content: bytes, expected_revision: str) -> dict[str, str]:
    document = json.loads(content)
    if not isinstance(document, dict) or set(document) != {"schema", "standard", "managedFiles"}:
        raise ValueError("adoption lock fields are invalid")
    managed = document.get("managedFiles")
    if not adoption_standard_binding_is_valid(document, expected_revision) or not isinstance(managed, dict):
        raise ValueError("adoption lock standard binding is invalid")
    if not all(
        isinstance(path, str)
        and relative_pattern(path)
        and isinstance(digest, str)
        and re.fullmatch(r"[a-f0-9]{64}", digest) is not None
        for path, digest in managed.items()
    ):
        raise ValueError("adoption lock managed hashes are invalid")
    return managed


def content_digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def standard_adoption_records(active: list[TicketRecord]) -> list[TicketRecord]:
    return [
        record for record in active
        if record.intent is not None
        and isinstance(record.intent.get("delivery"), dict)
        and "standardAdoption" in record.intent["delivery"]
    ]


def load_standard_adoption_evidence(
    root: Path,
    base: str,
    adoption: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str], bool]:
    base_package_content = git_revision_file(root, base, ".governance/package-manifest.json")
    base_lock_content = git_revision_file(root, base, ".governance/manifest.lock.json")
    head_package_path = safe_repo_path(root, ".governance/package-manifest.json")
    head_lock_path = safe_repo_path(root, ".governance/manifest.lock.json")
    if not head_package_path.is_file() or not head_lock_path.is_file():
        raise ValueError("head package manifest or lock is missing")
    initial = adoption["fromRevision"] is None
    if initial:
        if base_package_content is not None or base_lock_content is not None:
            raise ValueError("initial adoption base already contains a package manifest or lock")
        base_strategies: dict[str, str] = {}
        base_hashes: dict[str, str] = {}
    else:
        if base_package_content is None or base_lock_content is None:
            raise ValueError("upgrade base package manifest or lock is missing")
        base_strategies = package_strategies(base_package_content)
        base_hashes = adoption_lock(base_lock_content, adoption["fromRevision"])
    head_strategies = package_strategies(head_package_path.read_bytes())
    head_hashes = adoption_lock(head_lock_path.read_bytes(), adoption["toRevision"])
    base_managed = {path for path, strategy in base_strategies.items() if strategy == "managed"}
    head_managed = {path for path, strategy in head_strategies.items() if strategy == "managed"}
    if frozenset(base_hashes) not in {frozenset(base_strategies), frozenset(base_managed)}:
        raise ValueError("base package targets and lock targets differ")
    if set(head_hashes) != head_managed:
        raise ValueError("package targets and lock targets differ")
    return base_strategies, head_strategies, base_hashes, head_hashes, initial


def verify_changed_managed_paths(
    root: Path,
    base: str,
    changed: list[str],
    base_strategies: dict[str, str],
    head_strategies: dict[str, str],
    base_hashes: dict[str, str],
    head_hashes: dict[str, str],
    initial: bool,
) -> set[str]:
    exempt: set[str] = set()
    for raw_path in changed:
        if head_strategies.get(raw_path) != "managed":
            continue
        head_path = safe_repo_path(root, raw_path)
        if not head_path.is_file() or content_digest(head_path.read_bytes()) != head_hashes[raw_path]:
            raise ValueError(f"head managed hash differs: {raw_path}")
        base_content = git_revision_file(root, base, raw_path)
        if raw_path in base_strategies:
            if base_strategies[raw_path] != "managed" or base_content is None:
                raise ValueError(f"managed strategy continuity differs: {raw_path}")
            if content_digest(base_content) != base_hashes[raw_path]:
                raise ValueError(f"base managed hash differs: {raw_path}")
        elif base_content is not None:
            if initial:
                # Installing the standard does not erase target ownership.
                # A replaced path remains an ordinary implementation change.
                continue
            raise ValueError(f"new managed target already existed at base: {raw_path}")
        exempt.add(raw_path)
    if not exempt:
        raise ValueError("no changed managed payload was verified")
    return exempt


def atomic_standard_adoption_paths(
    root: Path,
    base: str | None,
    changed: list[str],
    active: list[TicketRecord],
    report: Report,
) -> set[str]:
    records = standard_adoption_records(active)
    if not records:
        return set()
    evidence_paths = [".governance/manifest.lock.json", ".governance/package-manifest.json"]
    if len(records) != 1:
        report.add(
            "GOV-SYNC-001",
            "Atomic standard adoption must resolve to exactly one active ticket.",
            "Keep one approved adoption ticket active and serialize every other adoption.",
            [rel(root, record.directory / "intent.json") for record in records],
        )
        return set()
    record = records[0]
    assert record.intent is not None
    adoption = record.intent["delivery"]["standardAdoption"]
    error = standard_adoption_error(adoption)
    if error or base is None or ".governance/manifest.lock.json" not in changed:
        report.add(
            "GOV-SYNC-001",
            f"Atomic standard adoption preconditions are invalid: {error or 'base and changed lock are required'}.",
            "Declare null-to-SHA bootstrap or distinct immutable upgrade revisions, compare against the approved Git base and regenerate the complete lock through Goal.",
            evidence_paths,
        )
        return set()
    try:
        evidence = load_standard_adoption_evidence(root, base, adoption)
        return verify_changed_managed_paths(root, base, changed, *evidence)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        report.add(
            "GOV-SYNC-001",
            f"Atomic standard adoption is inconsistent: {error}.",
            "Restore the base, install the complete published managed set through Goal and regenerate its lock before review.",
            evidence_paths,
            {"ticket": record.directory.name, "base": base},
        )
        return set()


def check_change_gate(
    root: Path,
    manifest: dict[str, Any],
    records: list[TicketRecord],
    changed: list[str],
    base: str | None,
    head: str,
    approval_source: str | None,
    approved_ticket: str | None,
    approval_evidence_path: str | None,
    expected_repository: str | None,
    expected_pull_request: int | None,
    expected_head: str | None,
    enforce_approval: bool,
    elapsed_minutes: int | None,
    report: Report,
) -> str | None:
    governance_patterns = manifest["governancePaths"]
    config = manifest["ticket"]
    active = [record for record in records if record.status in set(config.get("activeStatuses", ACTIVE_DEFAULT))]
    adoption_paths = atomic_standard_adoption_paths(root, base, changed, active, report)
    implementation = [
        path for path in changed
        if not matches(path, governance_patterns) and path not in adoption_paths
    ]
    if not implementation:
        return None
    selected = select_change_ticket(root, active, manifest.get("coordination"), implementation, report)
    if selected is None:
        return None
    check_selected_ticket_state(root, config, selected, implementation, base, head, governance_patterns, report)
    check_selected_ticket_intent(root, manifest, records, selected, implementation, base, elapsed_minutes, report)
    if enforce_approval:
        resolve_change_approval(
            root, manifest, selected, approval_source, approved_ticket,
            approval_evidence_path, expected_repository, expected_pull_request,
            expected_head, report,
        )
    return selected.directory.name


def sarif(payload: dict[str, Any]) -> dict[str, Any]:
    findings = payload["findings"]
    rules = {}
    results = []
    for item in findings:
        rules[item["code"]] = {
            "id": item["code"],
            "shortDescription": {"text": item["message"]},
            "help": {"text": item["remediation"]},
        }
        result: dict[str, Any] = {
            "ruleId": item["code"],
            "level": "error" if item["severity"] == "error" else "warning",
            "message": {"text": item["message"]},
        }
        if item["paths"]:
            result["locations"] = [{
                "physicalLocation": {"artifactLocation": {"uri": item["paths"][0]}},
            }]
        results.append(result)
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "new-project-governance", "version": RUNTIME_VERSION, "rules": [rules[key] for key in sorted(rules)]}},
            "results": results,
        }],
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = []
    for item in payload["findings"]:
        paths = f" [{', '.join(item['paths'])}]" if item["paths"] else ""
        lines.append(f"{item['code']} {item['severity'].upper()}: {item['message']}{paths}")
        lines.append(f"  remediation: {item['remediation']}")
    summary = payload["summary"]
    code = "GOV-PASS" if payload["status"] == "passed" else "GOV-FAIL"
    lines.append(f"{code}: {payload['status']} ({summary['errors']} errors, {summary['warnings']} warnings)")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default=".governance/manifest.json")
    parser.add_argument("--lock", default=None)
    parser.add_argument("--stack-profiles", default=None)
    parser.add_argument(
        "--work-classification",
        default=".governance/work-classification.dsl.json",
    )
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--actor", choices=["agent", "human", "ci"], default="agent")
    parser.add_argument("--trusted-human-change", action="store_true")
    parser.add_argument("--enforce-approval", action="store_true")
    parser.add_argument("--approval-source")
    parser.add_argument("--approved-ticket")
    parser.add_argument("--approval-evidence")
    parser.add_argument("--expected-repository")
    parser.add_argument("--expected-pull-request", type=int)
    parser.add_argument("--expected-head")
    parser.add_argument("--resolved-ticket-output")
    parser.add_argument("--elapsed-minutes", type=int)
    parser.add_argument("--format", choices=["text", "json", "sarif"], default="text")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def load_manifest(root: Path, raw_path: str, report: Report) -> dict[str, Any] | None:
    try:
        manifest_path = safe_repo_path(root, raw_path)
    except ValueError as error:
        report.add("GOV-MANIFEST-001", str(error), "Use a repository-relative manifest path.")
        return None
    try:
        manifest = load_json(manifest_path)
        if not basic_manifest_valid(manifest):
            raise ValueError("required manifest fields are missing or invalid")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report.add("GOV-MANIFEST-001", f"Governance manifest is invalid: {error}", "Restore a manifest conforming to the pinned governance schema.", [raw_path])
        return None
    return manifest


def optional_repo_path(
    root: Path,
    raw_path: str | None,
    code: str,
    label: str,
    report: Report,
) -> Path | None:
    if not raw_path:
        return None
    try:
        return safe_repo_path(root, raw_path)
    except ValueError as error:
        report.add(code, str(error), f"Use a repository-relative {label} path.", [raw_path])
        return None


def resolve_changed_paths(
    args: argparse.Namespace,
    root: Path,
    base: str | None,
    report: Report,
) -> list[str]:
    try:
        return changed_paths(root, base, args.head, args.changed_file)
    except (RuntimeError, ValueError) as error:
        report.add(
            "GOV-DIFF-001", str(error),
            "Use repository-relative changed paths and fetch the complete base/head history before retrying.",
            evidence={"base": base, "head": args.head},
        )
        return []


def resolve_validation_base(
    supplied_base: str | None,
    records: list[TicketRecord],
    config: dict[str, Any],
) -> str | None:
    if supplied_base is not None:
        return supplied_base
    active_statuses = set(config.get("activeStatuses", ACTIVE_DEFAULT))
    active = [record for record in records if record.status in active_statuses]
    adoption_records = standard_adoption_records(active)
    if len(adoption_records) != 1:
        return None
    record = adoption_records[0]
    assert record.intent is not None
    return record.intent["delivery"]["acceptedBaseSha"]


def run_governance_checks(
    args: argparse.Namespace,
    root: Path,
    manifest: dict[str, Any],
    report: Report,
) -> str | None:
    lock_path = optional_repo_path(root, args.lock, "GOV-SYNC-001", "governance lock", report)
    profiles_path = optional_repo_path(root, args.stack_profiles, "GOV-MANIFEST-001", "stack-profile", report)
    directories = ticket_directories(root, manifest["ticket"])
    records = load_ticket_records(directories, manifest["ticket"])
    base = resolve_validation_base(args.base, records, manifest["ticket"])
    changed = resolve_changed_paths(args, root, base, report)
    load_work_classification(root, report, args.work_classification)
    check_lock(root, lock_path, manifest, report)
    check_required_files(root, manifest, report)
    check_docker_image_references(root, manifest, report)
    check_stacks(root, manifest, profiles_path, report)
    check_ticket_content(root, directories, manifest["ticket"], report)
    check_coordination(root, manifest, records, changed, report)
    check_changed_content(root, changed, args.actor, args.trusted_human_change, report)
    return check_change_gate(
        root, manifest, records, changed, base, args.head, args.approval_source,
        args.approved_ticket, args.approval_evidence, args.expected_repository,
        args.expected_pull_request, args.expected_head, args.enforce_approval,
        args.elapsed_minutes, report,
    )


def formatted_report(payload: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_format == "sarif":
        return json.dumps(sarif(payload), indent=2, sort_keys=True) + "\n"
    return render_text(payload)


def write_report(output_path: Path | None, output: str) -> None:
    if output_path is None:
        sys.stdout.write(output)
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")


def write_resolved_ticket(
    root: Path,
    raw_path: str | None,
    selected_ticket: str | None,
    report: Report,
) -> None:
    if not raw_path or not selected_ticket or report.errors:
        return
    path = Path(raw_path).expanduser().resolve()
    if path.is_relative_to(root):
        report.add(
            "GOV-PATH-001", "Resolved ticket output must be outside the repository checkout.",
            "Write ephemeral approval context to runner.temp or another protected directory.",
            [rel(root, path)],
        )
        return
    try:
        path.write_text(f"{selected_ticket}\n", encoding="utf-8")
    except OSError as error:
        report.add(
            "GOV-PATH-001", f"Could not write resolved ticket output: {error}",
            "Use a writable protected directory outside the checkout.",
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.root).resolve()
    report = Report(root)
    manifest = load_manifest(root, args.manifest, report)
    selected_ticket: str | None = None

    if manifest is not None:
        selected_ticket = run_governance_checks(args, root, manifest, report)
    write_resolved_ticket(root, args.resolved_ticket_output, selected_ticket, report)
    output_path = optional_repo_path(root, args.output, "GOV-PATH-001", "report output", report)
    payload = report.payload()
    write_report(output_path, formatted_report(payload, args.format))
    return 0 if report.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
