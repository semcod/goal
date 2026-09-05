"""Governance blocks legacy push before bootstrap can mutate a repository."""

import json
import subprocess

import click
import pytest

from goal.governance import delivery
from goal.push import core


def repository(tmp_path, *, adopted=True, failure=True):
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    if adopted:
        for relative in delivery.GOVERNANCE_PACKAGE_FILES.values():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n")
        gate = root / "project/governance-check.sh"
        gate.parent.mkdir()
        gate.write_text(
            "#!/bin/sh\n"
            "echo checked > gate-ran\n"
            + (
                'echo "GOV-SCOPE-001: outside ticket scope"\nexit 1\n'
                if failure
                else "exit 0\n"
            )
        )
        gate.chmod(0o755)
        (root / delivery.GOVERNANCE_DIAGNOSTICS).write_text(
            json.dumps(
                {
                    "schema": "new-project.diagnostics/v2",
                    "codes": {
                        "GOV-SCOPE-001": {"remediation": "Create a bounded ticket."}
                    },
                }
            )
        )
    return root


def test_invalid_adoption_stops_push_before_initialization(tmp_path, monkeypatch):
    root = repository(tmp_path)
    monkeypatch.chdir(root)
    (root / "VERSION").write_text("1.0.0\n")

    def unexpected(*args, **kwargs):
        pytest.fail("workflow side effects started before governance passed")

    monkeypatch.setattr(core, "_initialize_context", unexpected)
    monkeypatch.setattr(core, "_bootstrap_projects_for_delivery", unexpected)
    with pytest.raises(click.ClickException, match="GOV-SCOPE-001") as error:
        core.execute_push_workflow(
            ctx_obj={"config": {}, "all_flags": True},
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket=None,
            abstraction=None,
            todo=False,
        )
    assert "Create a bounded ticket." in str(error.value)
    assert (root / "gate-ran").exists()
    assert (root / "VERSION").read_text() == "1.0.0\n"


def test_valid_adoption_checked_from_subdirectory(tmp_path):
    root = repository(tmp_path, failure=False)
    nested = root / "src"
    nested.mkdir()
    delivery.validate_legacy_governance(cwd=nested)
    assert (root / "gate-ran").exists()


def test_incomplete_adoption_fails_closed(tmp_path):
    root = repository(tmp_path)
    (root / delivery.GOVERNANCE_PACKAGE_FILES["lock"]).unlink()
    with pytest.raises(click.ClickException, match="GOV-MANIFEST-001"):
        delivery.validate_legacy_governance(cwd=root)
    assert not (root / "gate-ran").exists()


@pytest.mark.parametrize("git_repository", [True, False])
def test_unadopted_project_preserves_legacy_flow(tmp_path, monkeypatch, git_repository):
    root = repository(tmp_path, adopted=False) if git_repository else tmp_path

    def unexpected(*args, **kwargs):
        pytest.fail("unadopted project must not run a governance gate")

    monkeypatch.setattr(delivery, "_governance_gate", unexpected)
    delivery.validate_legacy_governance(cwd=root)
