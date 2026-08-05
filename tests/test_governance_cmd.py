"""Tests for immutable new-project adoption through Goal."""

import json
from pathlib import Path
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


def test_governance_help_exposes_adoption_command():
    result = CliRunner().invoke(main, ["governance", "--help"])

    assert result.exit_code == 0
    assert "adopt" in result.output


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
