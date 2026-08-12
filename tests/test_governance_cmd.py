"""Tests for immutable new-project adoption through Goal."""

import json
import subprocess
from urllib.error import URLError

from click.testing import CliRunner
import pytest

import goal.cli as goal_cli
import goal.cli.governance_cmd as governance_cmd
from goal.cli import main


class FakeReleaseResponse:
    def __init__(self, payload):
        self.payload = (
            payload
            if isinstance(payload, bytes)
            else json.dumps(payload).encode("utf-8")
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self, limit=-1):
        return self.payload if limit < 0 else self.payload[:limit]


@pytest.fixture(autouse=True)
def disable_version_network(monkeypatch):
    monkeypatch.setattr(goal_cli, "_show_goal_version_banner", lambda: None)
    monkeypatch.setattr(goal_cli, "_maybe_self_update", lambda latest, yes: None)
    monkeypatch.setattr(
        governance_cmd,
        "urlopen",
        lambda request, timeout: FakeReleaseResponse(
            {
                "tag_name": "v0.1.0",
                "draft": False,
                "prerelease": False,
                "published_at": "2026-08-12T00:00:00Z",
            }
        ),
    )


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
parser.add_argument('--allow-unpublished-for-testing', action='store_true')
args = parser.parse_args()
target = Path(args.target_root)
if args.allow_unpublished_for_testing:
    (target / '.candidate-testing').write_text('explicit\\n', encoding='utf-8')
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
    (standard / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    _git(standard, "init", "--quiet")
    _git(standard, "config", "user.email", "goal-governance@example.invalid")
    _git(standard, "config", "user.name", "goal-governance-test")
    _git(standard, "add", ".")
    _git(standard, "commit", "--quiet", "-m", "publish fake standard")
    revision = _git(standard, "rev-parse", "HEAD").stdout.strip()
    _git(standard, "tag", "-a", "v0.1.0", "-m", "fake release")
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


def test_governance_check_routes_source_hub_without_recommending_adoption(tmp_path):
    target = tmp_path / "new-project"
    for relative in (
        "governance/package-manifest.json",
        "governance/manifest.default.json",
        "scripts/governance_check.py",
    ):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        ["governance", "check", "--target-root", str(target)],
    )

    assert result.exit_code == 1
    assert "source hub, not an adopted repository" in result.output
    assert "do not adopt" in result.output


def test_governance_check_surfaces_v2_remediation_and_runbook(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    make_adopted_governance(target, exit_code=7)
    package = target / ".governance"
    (package / "governance_check.py").write_text(
        "print('GOV-TICKET-001: failed')\nraise SystemExit(7)\n",
        encoding="utf-8",
    )
    (package / "diagnostics.json").write_text(
        json.dumps(
            {
                "schema": "new-project.diagnostics/v2",
                "codes": {
                    "GOV-TICKET-001": {
                        "message": "Ticket is missing.",
                        "remediation": "Create exactly one bounded ticket.",
                        "documentation": "error/GOV-TICKET-001.md",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    runbook = package / "error" / "GOV-TICKET-001.md"
    runbook.parent.mkdir()
    runbook.write_text("# Runbook\n", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        ["governance", "check", "--target-root", str(target)],
    )

    assert result.exit_code == 7
    assert "canonical remediation for GOV-TICKET-001" in result.output
    assert "Create exactly one bounded ticket." in result.output
    assert ".governance/error/GOV-TICKET-001.md" in result.output


def test_verify_delivery_does_not_create_missing_goal_yaml():
    runner = CliRunner()
    with runner.isolated_filesystem():
        root = governance_cmd.Path.cwd()
        _git(root, "init", "--quiet")
        result = runner.invoke(main, ["governance", "verify-delivery"])

        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["enabled"] is False
        assert not (root / "goal.yaml").exists()


def test_verify_delivery_does_not_rewrite_existing_goal_yaml():
    runner = CliRunner()
    with runner.isolated_filesystem():
        root = governance_cmd.Path.cwd()
        _git(root, "init", "--quiet")
        config = root / "goal.yaml"
        config.write_text(
            "project:\n  name: deliberately-stale\n"
            "advanced:\n  auto_update_config: true\n",
            encoding="utf-8",
        )
        before = config.read_bytes()

        result = runner.invoke(main, ["governance", "verify-delivery"])

        assert result.exit_code == 0, result.output
        assert config.read_bytes() == before


def test_authorize_push_fails_closed_without_goal_yaml():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main, ["governance", "authorize-push", "origin"]
        )

        assert result.exit_code == 1
        assert "requires an existing goal.yaml" in result.output
        assert not governance_cmd.Path("goal.yaml").exists()


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


def test_adopt_rejects_revision_without_release_tag(tmp_path):
    standard, revision = make_standard(tmp_path)
    _git(standard, "tag", "-d", "v0.1.0")
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
        ],
    )

    assert result.exit_code == 1
    assert "has no published release tag v0.1.0" in result.output
    assert not (target / ".fake-adoption.json").exists()


def test_adopt_rejects_lightweight_release_tag(tmp_path):
    standard, revision = make_standard(tmp_path)
    _git(standard, "tag", "-d", "v0.1.0")
    _git(standard, "tag", "v0.1.0", revision)
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
        ],
    )

    assert result.exit_code == 1
    assert "must be an annotated Git tag" in result.output
    assert not (target / ".fake-adoption.json").exists()


def test_adopt_rejects_release_tag_for_another_revision(tmp_path):
    standard, _released_revision = make_standard(tmp_path)
    (standard / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    _git(standard, "add", "candidate.txt")
    _git(standard, "commit", "--quiet", "-m", "unreleased candidate")
    revision = _git(standard, "rev-parse", "HEAD").stdout.strip()
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
        ],
    )

    assert result.exit_code == 1
    assert "does not identify requested revision" in result.output
    assert not (target / ".fake-adoption.json").exists()


def test_adopt_rejects_missing_github_release(tmp_path, monkeypatch):
    standard, revision = make_standard(tmp_path)
    target = tmp_path / "target"
    target.mkdir()

    def unavailable(request, timeout):
        raise URLError("release not found")

    monkeypatch.setattr(governance_cmd, "urlopen", unavailable)
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

    assert result.exit_code == 1
    assert "has no verifiable published GitHub Release v0.1.0" in result.output
    assert not (target / ".fake-adoption.json").exists()


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"{", "metadata for v0.1.0 is invalid"),
        (b"[]", "metadata for v0.1.0 is invalid"),
        (
            b"x" * (governance_cmd.MAX_RELEASE_METADATA_BYTES + 1),
            "metadata for v0.1.0 is unexpectedly large",
        ),
    ],
    ids=("malformed-json", "non-object", "oversized"),
)
def test_adopt_rejects_invalid_github_release_metadata(
    tmp_path, monkeypatch, raw, message
):
    standard, revision = make_standard(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    monkeypatch.setattr(
        governance_cmd,
        "urlopen",
        lambda request, timeout: FakeReleaseResponse(raw),
    )

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

    assert result.exit_code == 1
    assert message in result.output
    assert not (target / ".fake-adoption.json").exists()


@pytest.mark.parametrize(
    ("release", "message"),
    [
        (
            {
                "tag_name": "v9.9.9",
                "draft": False,
                "prerelease": False,
                "published_at": "2026-08-12T00:00:00Z",
            },
            "does not identify standard tag v0.1.0",
        ),
        (
            {
                "tag_name": "v0.1.0",
                "draft": True,
                "prerelease": False,
                "published_at": "2026-08-12T00:00:00Z",
            },
            "is not a final published release",
        ),
        (
            {
                "tag_name": "v0.1.0",
                "draft": False,
                "prerelease": True,
                "published_at": "2026-08-12T00:00:00Z",
            },
            "is not a final published release",
        ),
        (
            {
                "tag_name": "v0.1.0",
                "draft": False,
                "prerelease": False,
                "published_at": None,
            },
            "is not a final published release",
        ),
    ],
)
def test_adopt_rejects_nonfinal_github_release(
    tmp_path, monkeypatch, release, message
):
    standard, revision = make_standard(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    monkeypatch.setattr(
        governance_cmd,
        "urlopen",
        lambda request, timeout: FakeReleaseResponse(release),
    )

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

    assert result.exit_code == 1
    assert message in result.output
    assert not (target / ".fake-adoption.json").exists()


def test_explicit_candidate_mode_skips_release_proof_and_is_forwarded(
    tmp_path, monkeypatch
):
    standard, revision = make_standard(tmp_path)
    _git(standard, "tag", "-d", "v0.1.0")
    target = tmp_path / "target"
    target.mkdir()

    def forbidden(*args, **kwargs):
        raise AssertionError("candidate testing attempted GitHub Release lookup")

    monkeypatch.setattr(governance_cmd, "urlopen", forbidden)

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
            "--allow-unpublished-for-testing",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (target / ".candidate-testing").read_text(encoding="utf-8") == "explicit\n"
    assert (target / ".fake-adoption.json").is_file()


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
