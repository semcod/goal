"""Tests for immutable new-project adoption through Goal."""

import json
import subprocess

from click.testing import CliRunner
import pytest

import goal.cli as goal_cli
from goal.cli import main


@pytest.fixture(autouse=True)
def disable_version_network(monkeypatch):
    monkeypatch.setattr(goal_cli, "_show_goal_version_banner", lambda: None)
    monkeypatch.setattr(goal_cli, "_maybe_self_update", lambda latest, yes: None)


def _git(root, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def make_standard(tmp_path):
    standard = tmp_path / "standard-source"
    scripts = standard / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "create_adoption_lock.py").write_text(
        """#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--target-root', required=True)
parser.add_argument('--source-revision', required=True)
parser.add_argument('--check', action='store_true')
parser.add_argument('--upgrade', action='store_true')
args = parser.parse_args()
target = Path(args.target_root)
if args.check:
    print('CREATE .governance/manifest.lock.json')
    raise SystemExit(1)
(target / '.fake-adoption.json').write_text(json.dumps({
    'revision': args.source_revision,
    'upgrade': args.upgrade,
}), encoding='utf-8')
print(f'adopted fake standard at {args.source_revision}')
""",
        encoding="utf-8",
    )
    _git(standard, "init", "--quiet")
    _git(standard, "config", "user.email", "goal-governance@example.invalid")
    _git(standard, "config", "user.name", "goal-governance-test")
    _git(standard, "add", ".")
    _git(standard, "commit", "--quiet", "-m", "publish fake standard")
    revision = _git(standard, "rev-parse", "HEAD").stdout.strip()
    return standard, revision


def make_adopted_governance(target, *, exit_code=0):
    package = target / ".governance"
    package.mkdir(parents=True)
    (package / "governance_check.py").write_text(
        f"""\
import sys

print("VALIDATOR_ARGS=" + "|".join(sys.argv[1:]))
print("validator diagnostic", file=sys.stderr)
raise SystemExit({exit_code})
""",
        encoding="utf-8",
    )
    for name in ("manifest.json", "manifest.lock.json", "stack-profiles.json"):
        (package / name).write_text("{}\n", encoding="utf-8")


def make_workspace_checker(target, *, exit_code=0):
    package = target / ".governance"
    package.mkdir(parents=True, exist_ok=True)
    (package / "workspace_lifecycle_check.py").write_text(
        f"""\
import sys

print("WORKSPACE_ARGS=" + "|".join(sys.argv[1:]))
print("workspace diagnostic", file=sys.stderr)
raise SystemExit({exit_code})
""",
        encoding="utf-8",
    )


def test_governance_help_exposes_adoption_command():
    result = CliRunner().invoke(main, ["governance", "--help"])

    assert result.exit_code == 0
    assert "adopt" in result.output
    assert "check" in result.output
    assert "workspace-check" in result.output


def test_workspace_check_runs_adopted_checker_and_forwards_exact_paths(tmp_path):
    target = tmp_path / "target"
    workspace = tmp_path / "workspace"
    allowed_one = workspace / "active-one"
    allowed_two = workspace / "active-two"
    target.mkdir()
    workspace.mkdir()
    make_workspace_checker(target, exit_code=9)

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "workspace-check",
            "--target-root",
            str(target),
            "--workspace-root",
            str(workspace),
            "--allow",
            str(allowed_one),
            "--allow",
            str(allowed_two),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 9
    expected = (
        f"--workspace-root|{workspace}|--allow|{allowed_one}|"
        f"--allow|{allowed_two}|--format|json"
    )
    assert f"WORKSPACE_ARGS={expected}" in result.output
    assert "workspace diagnostic" in result.output


def test_workspace_check_fails_closed_without_adopted_checker(tmp_path):
    target = tmp_path / "target"
    workspace = tmp_path / "workspace"
    target.mkdir()
    workspace.mkdir()

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "workspace-check",
            "--target-root",
            str(target),
            "--workspace-root",
            str(workspace),
        ],
    )

    assert result.exit_code == 1
    assert "adopted workspace lifecycle checker is missing" in result.output
    assert ".governance/workspace_lifecycle_check.py" in result.output


def test_governance_check_runs_adopted_validator_and_forwards_options(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    make_adopted_governance(target, exit_code=7)

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "check",
            "--target-root",
            str(target),
            "--actor",
            "agent",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 7
    expected = (
        f"--root|{target}|--manifest|.governance/manifest.json|"
        "--lock|.governance/manifest.lock.json|"
        "--stack-profiles|.governance/stack-profiles.json|"
        "--actor|agent|--format|json"
    )
    assert f"VALIDATOR_ARGS={expected}" in result.output
    assert "validator diagnostic" in result.output


def test_governance_check_skips_mutable_interactive_main_setup(
    tmp_path, monkeypatch
):
    target = tmp_path / "target"
    target.mkdir()
    make_adopted_governance(target)

    def forbidden(*args, **kwargs):
        raise AssertionError("governance check entered mutable main setup")

    monkeypatch.setattr(goal_cli, "_warn_goal_binary_mismatch", forbidden)
    monkeypatch.setattr(goal_cli, "_warn_wheel_shadows_editable", forbidden)
    monkeypatch.setattr(goal_cli, "_show_goal_version_banner", forbidden)
    monkeypatch.setattr(goal_cli, "_maybe_self_update", forbidden)
    monkeypatch.setattr(goal_cli, "ensure_config", forbidden)
    monkeypatch.setattr(goal_cli, "get_user_config", forbidden)
    monkeypatch.setattr(goal_cli, "load_config", lambda *args, **kwargs: {})

    result = CliRunner().invoke(
        main,
        ["governance", "check", "--target-root", str(target)],
    )

    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert "VALIDATOR_ARGS=" in result.output


def test_governance_adopt_skips_mutable_caller_setup(tmp_path, monkeypatch):
    standard, revision = make_standard(tmp_path)
    target = tmp_path / "target"
    caller = tmp_path / "caller"
    target.mkdir()
    caller.mkdir()
    monkeypatch.chdir(caller)

    def forbidden(*args, **kwargs):
        raise AssertionError("governance adopt entered mutable main setup")

    monkeypatch.setattr(goal_cli, "_warn_goal_binary_mismatch", forbidden)
    monkeypatch.setattr(goal_cli, "_warn_wheel_shadows_editable", forbidden)
    monkeypatch.setattr(goal_cli, "_show_goal_version_banner", forbidden)
    monkeypatch.setattr(goal_cli, "_maybe_self_update", forbidden)
    monkeypatch.setattr(goal_cli, "ensure_config", forbidden)
    monkeypatch.setattr(goal_cli, "get_user_config", forbidden)
    monkeypatch.setattr(goal_cli, "load_config", lambda *args, **kwargs: {})

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "adopt",
            "--standard-repository",
            str(standard),
            "--source-revision",
            revision,
            "--target-root",
            str(target),
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert (target / ".fake-adoption.json").is_file()
    assert not (caller / "goal.yaml").exists()


def test_governance_check_fails_closed_for_incomplete_package(tmp_path):
    target = tmp_path / "target"
    target.mkdir()

    result = CliRunner().invoke(
        main,
        ["governance", "check", "--target-root", str(target)],
    )

    assert result.exit_code == 1
    assert "adopted governance package is incomplete" in result.output
    assert ".governance/governance_check.py" in result.output
    assert "goal governance adopt" in result.output


def test_governance_check_rejects_managed_path_override(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    make_adopted_governance(target)

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "check",
            "--target-root",
            str(target),
            "--manifest=other.json",
        ],
    )

    assert result.exit_code == 2
    assert "--manifest is managed by Goal" in result.output


def test_adopt_fetches_exact_revision_and_forwards_upgrade(tmp_path):
    standard, revision = make_standard(tmp_path)
    target = tmp_path / "target"
    target.mkdir()

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "adopt",
            "--standard-repository",
            str(standard),
            "--source-revision",
            revision,
            "--target-root",
            str(target),
            "--upgrade",
        ],
    )

    assert result.exit_code == 0, result.output
    marker = json.loads((target / ".fake-adoption.json").read_text(encoding="utf-8"))
    assert marker == {"revision": revision, "upgrade": True}
    assert revision in result.output


def test_check_forwards_exit_code_without_writing(tmp_path):
    standard, revision = make_standard(tmp_path)
    target = tmp_path / "target"
    target.mkdir()

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "adopt",
            "--standard-repository",
            str(standard),
            "--source-revision",
            revision,
            "--target-root",
            str(target),
            "--check",
        ],
    )

    assert result.exit_code == 1
    assert "CREATE .governance/manifest.lock.json" in result.output
    assert not (target / ".fake-adoption.json").exists()


def test_rejects_non_full_revision_before_fetch(tmp_path):
    target = tmp_path / "target"
    target.mkdir()

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "adopt",
            "--source-revision",
            "deadbeef",
            "--target-root",
            str(target),
        ],
    )

    assert result.exit_code == 2
    assert "full lowercase 40-character commit SHA" in result.output


def test_rejects_check_with_upgrade(tmp_path):
    target = tmp_path / "target"
    target.mkdir()

    result = CliRunner().invoke(
        main,
        [
            "governance",
            "adopt",
            "--source-revision",
            "a" * 40,
            "--target-root",
            str(target),
            "--check",
            "--upgrade",
        ],
    )

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output
