from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from goal.governance import delivery, remediation


def _project(tmp_path: Path) -> Path:
    governance = tmp_path / ".governance"
    governance.mkdir()
    (governance / "diagnostics.json").write_text(
        json.dumps(
            {
                "schema": "new-project.diagnostics/v2",
                "codes": {
                    "GOV-INTENT-003": {
                        "message": "Intent was published after implementation.",
                        "remediation": "Rebuild the branch with intent first.",
                        "documentation": "error/GOV-INTENT-003.md",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_publishes_canonical_proposal_and_delegates_without_shell(
    tmp_path: Path, monkeypatch
) -> None:
    project = _project(tmp_path)
    calls: list[tuple[list[str], dict]] = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "created PLF-001\n", "")

    monkeypatch.setattr(remediation.subprocess, "run", runner)
    result = remediation.publish_governance_remediation(
        project,
        "GOV-INTENT-003 ERROR: intent.json did not exist before implementation.\n",
    )

    assert result.proposal_path is not None
    assert result.delegated is True
    assert result.proposal_path.is_file()
    payload = json.loads(result.proposal_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "planfile.ticket-proposal.v1"
    assert payload["dedupe_key"] == "goal-governance:GOV-INTENT-003"
    assert payload["source"]["finding_id"] == "GOV-INTENT-003"
    assert calls == [
        (
            [
                "koru",
                "goal-remediation",
                "--project",
                str(project),
                "--proposal",
                str(result.proposal_path),
            ],
            {
                "cwd": project,
                "capture_output": True,
                "text": True,
                "check": False,
                "timeout": 30,
            },
        )
    ]

    assert payload["acceptance_criteria"]


def test_unpublished_diagnostic_does_not_write_or_delegate(tmp_path: Path, monkeypatch) -> None:
    project = _project(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        remediation.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command),
    )

    result = remediation.publish_governance_remediation(project, "GOV-UNKNOWN-999 ERROR")

    assert result.proposal_path is None
    assert result.delegated is False
    assert calls == []
    assert not (project / ".planfile").exists()


def test_multiple_diagnostics_create_one_proposal_and_delegation_each(
    tmp_path: Path, monkeypatch
) -> None:
    project = _project(tmp_path)
    catalog = json.loads(
        (project / ".governance/diagnostics.json").read_text(encoding="utf-8")
    )
    catalog["codes"]["GOV-BASE-001"] = {
        "message": "The approved base changed.",
        "remediation": "Refresh the approved base before implementation.",
        "documentation": "error/GOV-BASE-001.md",
    }
    (project / ".governance/diagnostics.json").write_text(
        json.dumps(catalog), encoding="utf-8"
    )
    calls: list[list[str]] = []

    def runner(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "created\n", "")

    monkeypatch.setattr(remediation.subprocess, "run", runner)
    result = remediation.publish_governance_remediation(
        project,
        "GOV-INTENT-003 ERROR\nGOV-BASE-001 ERROR\n",
    )

    proposals = sorted(
        (project / ".planfile/.koru/goal-remediation").glob("*.json")
    )
    assert result.delegated is True
    assert [path.name.split("-")[0:2] for path in proposals] == [
        ["GOV", "BASE"],
        ["GOV", "INTENT"],
    ]
    assert len(calls) == 2
    assert all(command[:2] == ["koru", "goal-remediation"] for command in calls)


def test_delegation_can_be_disabled_while_proposal_remains_audit_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    project = _project(tmp_path)
    monkeypatch.setenv("GOAL_KORU_REMEDIATION", "off")

    result = remediation.publish_governance_remediation(project, "GOV-INTENT-003 ERROR")

    assert result.delegated is False
    assert result.proposal_path is not None
    assert "disabled" in result.detail


def test_governance_gate_publishes_before_raising_original_failure(
    tmp_path: Path, monkeypatch
) -> None:
    project = _project(tmp_path)
    (project / ".governance/manifest.json").write_text("{}", encoding="utf-8")
    (project / ".governance/manifest.lock.json").write_text("{}", encoding="utf-8")
    (project / ".governance/stack-profiles.json").write_text("{}", encoding="utf-8")
    (project / ".governance/governance_check.py").write_text("", encoding="utf-8")
    gate = project / "project/governance-check.sh"
    gate.parent.mkdir()
    gate.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
    monkeypatch.setenv("GOAL_KORU_REMEDIATION", "off")

    def run(arguments, *, cwd=None):
        if arguments == [str(gate)]:
            return subprocess.CompletedProcess(
                arguments,
                7,
                "GOV-INTENT-003 ERROR: intent was published late\n",
                "",
            )
        raise AssertionError(arguments)

    monkeypatch.setattr(delivery, "_run", run)

    with pytest.raises(delivery.click.ClickException, match="GOV-INTENT-003"):
        delivery._governance_gate(project)

    proposals = list((project / ".planfile/.koru/goal-remediation").glob("*.json"))
    assert len(proposals) == 1
