"""Regression coverage for ticket-024 delivery integrity boundaries."""

import importlib
import os
from contextlib import ExitStack, nullcontext
from pathlib import Path
from unittest.mock import patch

import click
import pytest


def test_legacy_push_import_does_not_replace_canonical_cli_command() -> None:
    """Importing the compatibility module must not replace the governed CLI."""
    from goal.cli import main

    canonical = main.commands["push"]
    legacy = importlib.import_module("goal.push.commands")
    importlib.reload(legacy)

    assert main.commands["push"] is canonical


def test_self_update_ignores_non_string_version_provider_result() -> None:
    """Only a concrete version string may authorize a self-update attempt."""
    from goal.cli import _maybe_self_update

    with patch("goal.cli._auto_update_goal") as auto_update:
        _maybe_self_update(object(), yes=True)  # type: ignore[arg-type]

    auto_update.assert_not_called()


def test_cost_badge_skip_applies_to_commit_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The documented skip switch must cover both bootstrap and commit refresh."""
    from goal.push.core import _handle_commit_phase

    monkeypatch.setenv("GOAL_SKIP_COSTS_BADGE", "1")
    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": None,
        "user_config": {},
    }
    with (
        patch("goal.push.core.handle_version_sync"),
        patch("goal.push.core.handle_changelog"),
        patch("goal.push.core._update_cost_badges") as update_badges,
        patch("goal.push.core.run_git_local") as run_git_local,
        patch("goal.push.core.handle_single_commit") as single_commit,
    ):
        _handle_commit_phase(
            ctx_obj=ctx_obj,
            split=False,
            message=None,
            commit_title="fix: preserve metadata boundary",
            commit_body=None,
            commit_msg="fix: preserve metadata boundary",
            files=["goal/push/core.py"],
            ticket=None,
            new_version="1.2.4",
            current_version="1.2.3",
            no_version_sync=False,
            no_changelog=False,
        )

    update_badges.assert_not_called()
    run_git_local.assert_not_called()
    single_commit.assert_called_once()


def test_goal_cost_badge_control_does_not_leak_into_project_tests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Goal-only control variables must not alter the project's own test suite."""
    from goal.push.core import _run_test_stage_or_exit

    monkeypatch.setenv("GOAL_SKIP_COSTS_BADGE", "1")
    observed: list[str | None] = []

    def run_test_stage(*_args: object, **_kwargs: object) -> tuple[str, int]:
        observed.append(os.getenv("GOAL_SKIP_COSTS_BADGE"))
        return "Tests passed", 0

    with patch("goal.push.core.run_test_stage", side_effect=run_test_stage):
        result = _run_test_stage_or_exit(
            project_types=["python"],
            ctx_obj={"yes": True},
            markdown=False,
            files=["goal/push/core.py"],
            stats={},
            current_version="1.2.3",
            new_version="1.2.3",
            commit_msg="fix: isolate Goal controls",
            commit_body=None,
        )

    assert result == ("Tests passed", 0)
    assert observed == [None]
    assert os.environ["GOAL_SKIP_COSTS_BADGE"] == "1"


@pytest.mark.parametrize("existing_config", [False, True])
def test_dry_run_context_does_not_create_or_rewrite_goal_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing_config: bool
) -> None:
    """Global dry-run configuration loading must be observably read-only."""
    from goal.cli import _configure_main_context

    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    config_path = tmp_path / "goal.yaml"
    if existing_config:
        config_path.write_text(
            """
version: '1.0'
project:
  name: stale-name
  type: []
versioning:
  strategy: semver
  files: []
git:
  commit:
    strategy: conventional
advanced:
  auto_update_config: true
""".lstrip(),
            encoding="utf-8",
        )
    before = config_path.read_bytes() if config_path.exists() else None
    ctx = click.Context(click.Command("goal"), obj={})

    with patch("goal.cli.get_user_config", return_value={}):
        _configure_main_context(
            ctx,
            "patch",
            None,
            False,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            True,
            None,
            None,
            "direct-main",
        )

    after = config_path.read_bytes() if config_path.exists() else None
    assert after == before


@pytest.mark.parametrize("existing_config", [False, True])
def test_subcommand_help_does_not_create_or_rewrite_goal_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing_config: bool
) -> None:
    """Rendering push help must not initialize mutable project state."""
    from click.testing import CliRunner

    from goal.cli import main

    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "goal.yaml"
    if existing_config:
        config_path.write_text(
            "advanced:\n  auto_update_config: true\nproject:\n  name: retained\n",
            encoding="utf-8",
        )
    before = config_path.read_bytes() if config_path.exists() else None

    result = CliRunner().invoke(main, ["push", "--help"])

    assert result.exit_code == 0, result.output
    after = config_path.read_bytes() if config_path.exists() else None
    assert after == before


def test_non_governed_push_failure_aborts_before_success_summary() -> None:
    """The legacy delivery path must propagate an unsuccessful remote push."""
    from goal.push.core import execute_push_workflow

    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": {},
        "user_config": {},
    }
    with (
        patch("goal.push.core.check_pyproject_toml", return_value=None),
        patch("goal.push.core._initialize_context"),
        patch("goal.push.core._detect_project_types", return_value=["python"]),
        patch("goal.push.core._bootstrap_projects"),
        patch("goal.push.core.run_git"),
        patch("goal.push.core.get_staged_files", return_value=["goal/feature.py"]),
        patch("goal.push.core._validate_staged_files"),
        patch("goal.push.core.get_diff_content", return_value="diff"),
        patch(
            "goal.push.core.get_diff_stats",
            return_value={"goal/feature.py": (1, 0)},
        ),
        patch(
            "goal.push.core.get_commit_message",
            return_value=("fix: preserve delivery result", None, {}),
        ),
        patch("goal.push.core.get_version_info", return_value=("1.0.0", "1.0.1")),
        patch("goal.push.core.run_test_stage", return_value=("Tests passed", 0)),
        patch("goal.push.core._handle_commit_phase"),
        patch("goal.push.core.handle_publish", return_value=(True, None)),
        patch("goal.push.core.create_tag", return_value="v1.0.1"),
        patch("goal.git_ops.get_remote_branch", return_value="main"),
        patch("goal.push.core.push_to_remote", return_value=False),
        patch("goal.push.core.handle_todo_stage", return_value=True),
        patch("goal.push.core.output_final_summary") as summary,
        pytest.raises(click.ClickException, match="Git remote push failed"),
    ):
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            no_publish=False,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket=None,
            abstraction=None,
            todo=False,
        )

    summary.assert_not_called()


def test_clean_force_publish_uses_premerged_version_without_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A clean publish-only release must not stop at the no-files shortcut."""
    from goal.push.core import execute_push_workflow

    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": {},
        "user_config": {},
        "delivery_mode": "publish-only",
    }
    delivery = type("Delivery", (), {"mode": "publish-only"})()
    decision = type(
        "Decision",
        (),
        {
            "reason": "already-bumped",
            "managed_specs": (
                "VERSION",
                "pyproject.toml:version",
                "goal/__init__.py:__version__",
            ),
            "local_drift": False,
        },
    )()
    bootstrap_controls: list[str | None] = []

    def observe_bootstrap(*_args: object, **_kwargs: object) -> None:
        bootstrap_controls.append(os.getenv("GOAL_SKIP_COSTS_BADGE"))

    monkeypatch.delenv("GOAL_SKIP_COSTS_BADGE", raising=False)

    with (
        patch(
            "goal.governance.delivery.resolve_delivery_policy",
            return_value=delivery,
        ),
        patch("goal.governance.delivery.validate_delivery_ready"),
        patch("goal.governance.delivery.record_delivery_event") as delivery_event,
        patch("goal.push.core.check_pyproject_toml", return_value=None),
        patch("goal.push.core._initialize_context"),
        patch("goal.push.core._detect_project_types", return_value=["python"]),
        patch("goal.push.core._bootstrap_projects", side_effect=observe_bootstrap),
        patch("goal.push.core.run_git"),
        patch("goal.push.core.get_staged_files", return_value=[]),
        patch("goal.push.core.get_working_tree_files", return_value=[]),
        patch("goal.push.core.get_commit_message") as commit_message,
        patch(
            "goal.push.core.get_version_info",
            return_value=("2.1.292", "2.1.293", decision),
        ),
        patch("goal.cli.version_state.format_version_decision", return_value=[]),
        patch("goal.cli.version_state.validate_version_sources") as validate_versions,
        patch("goal.push.core.run_test_stage", return_value=("Tests passed", 0)),
        patch("goal.push.core._handle_commit_phase") as commit_phase,
        patch("goal.push.core.handle_publish", return_value=(True, None)) as publish,
        patch("goal.push.core.create_tag", return_value=None) as create_tag,
        patch("goal.push.core.handle_todo_stage", return_value=True),
    ):
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            no_publish=False,
            force_publish=True,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket=None,
            abstraction=None,
            todo=False,
        )

    commit_message.assert_not_called()
    commit_phase.assert_not_called()
    validate_versions.assert_called_once_with(decision.managed_specs, "2.1.293")
    publish.assert_called_once()
    assert publish.call_args.kwargs["staged_files"] == []
    assert publish.call_args.kwargs["force_publish"] is True
    create_tag.assert_called_once_with("2.1.293", True)
    assert bootstrap_controls == ["1"]
    assert os.getenv("GOAL_SKIP_COSTS_BADGE") is None
    assert [call.args[1] for call in delivery_event.call_args_list] == [
        "started",
        "published",
    ]


def test_existing_release_tag_must_be_annotated_and_match_head() -> None:
    """A release repair may reuse only the reviewed immutable tag at HEAD."""
    from goal.push.stages.tag import reuse_exact_annotated_tag

    def result(returncode: int = 0, stdout: str = ""):
        return type("Result", (), {"returncode": returncode, "stdout": stdout})()

    with patch(
        "goal.push.stages.tag.run_git",
        side_effect=[
            result(stdout="tag\n"),
            result(stdout="abc\n"),
            result(stdout="abc\n"),
        ],
    ):
        assert reuse_exact_annotated_tag("0.16.0") == "v0.16.0"

    with (
        patch(
            "goal.push.stages.tag.run_git",
            return_value=result(stdout="commit\n"),
        ),
        pytest.raises(click.ClickException, match="is not annotated"),
    ):
        reuse_exact_annotated_tag("0.16.0")

    with (
        patch(
            "goal.push.stages.tag.run_git",
            side_effect=[
                result(stdout="tag\n"),
                result(stdout="old\n"),
                result(stdout="head\n"),
            ],
        ),
        pytest.raises(click.ClickException, match="does not point to current HEAD"),
    ):
        reuse_exact_annotated_tag("0.16.0")


def test_direct_main_retry_recovers_exact_existing_tag() -> None:
    """A clean direct-main retry routes an exact existing tag to Release repair."""
    from goal.push.core import _resolve_release_tag

    delivery = type("Delivery", (), {"mode": "direct-main"})()
    with patch(
        "goal.push.core.reuse_exact_annotated_tag",
        return_value="v0.16.0",
    ) as reuse:
        resolved = _resolve_release_tag(
            "0.16.0",
            None,
            effective_no_tag=False,
            delivery=delivery,
            clean_force_publish=True,
        )

    assert resolved == "v0.16.0"
    reuse.assert_called_once_with("0.16.0")


def test_clean_generic_direct_main_retry_keeps_existing_release_version() -> None:
    """The full retry must repair v0.16.0 instead of proposing v0.16.1."""
    from goal.cli.version_state import VersionDecision, VersionSource
    from goal.push.core import execute_push_workflow

    config = {
        "publishing": {
            "fallback": {
                "github_release": {
                    "enabled": True,
                    "owner": "wellmanifest",
                    "repo": "new-project",
                    "create_on_tag": True,
                }
            }
        }
    }
    delivery = type(
        "Delivery",
        (),
        {"mode": "direct-main", "base_branch": "main", "remote": "origin"},
    )()
    source = VersionSource(
        spec="VERSION",
        path="VERSION",
        selector="",
        value="0.16.0",
        origin="configured",
    )
    decision = VersionDecision(
        current_version="0.16.0",
        target_version="0.16.1",
        reason="normal-bump",
        sources=(source,),
        baseline_version="0.16.0",
        baseline_evidence=("git-tag:v0.16.0",),
        registry_versions=(),
        unavailable_registries=(),
        derived_paths=(),
    )
    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": config,
        "user_config": {},
        "delivery_mode": "direct-main",
    }

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "goal.governance.delivery.resolve_delivery_policy",
                return_value=delivery,
            )
        )
        stack.enter_context(
            patch("goal.governance.delivery.validate_delivery_ready")
        )
        stack.enter_context(patch("goal.governance.delivery.record_delivery_event"))
        stack.enter_context(
            patch(
                "goal.governance.delivery.authorized_push",
                return_value=nullcontext(),
            )
        )
        stack.enter_context(
            patch("goal.push.core.check_pyproject_toml", return_value=None)
        )
        stack.enter_context(patch("goal.push.core._initialize_context"))
        stack.enter_context(
            patch("goal.push.core._detect_project_types", return_value=[])
        )
        stack.enter_context(patch("goal.push.core._bootstrap_projects"))
        stack.enter_context(
            patch("goal.push.core._require_publish_bootstrap_read_only")
        )
        stack.enter_context(patch("goal.push.core.run_git"))
        stack.enter_context(
            patch("goal.push.core.get_staged_files", return_value=[])
        )
        stack.enter_context(
            patch("goal.push.core.get_diff_content", return_value="")
        )
        stack.enter_context(patch("goal.push.core.get_diff_stats", return_value={}))
        stack.enter_context(
            patch(
                "goal.push.core.get_version_info",
                return_value=("0.16.0", "0.16.1", decision),
            )
        )
        validate_versions = stack.enter_context(
            patch("goal.cli.version_state.validate_version_sources")
        )
        stack.enter_context(
            patch("goal.push.core.run_test_stage", return_value=("Tests passed", 0))
        )
        stack.enter_context(
            patch("goal.push.core.handle_todo_stage", return_value=True)
        )
        publish = stack.enter_context(
            patch("goal.push.core.handle_publish", return_value=(True, None))
        )
        create_tag = stack.enter_context(
            patch("goal.push.core.create_tag", return_value=None)
        )
        push = stack.enter_context(
            patch("goal.push.core.push_to_remote", return_value=True)
        )
        reuse = stack.enter_context(
            patch(
                "goal.push.core.reuse_exact_annotated_tag",
                return_value="v0.16.0",
            )
        )
        mirror = stack.enter_context(
            patch(
                "goal.publish.github_fallback.try_github_release_on_tag",
                return_value=True,
            )
        )
        stack.enter_context(patch("goal.push.core.output_final_summary"))
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            no_publish=False,
            force_publish=True,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket=None,
            abstraction=None,
            todo=False,
        )

    assert reuse.call_count == 2
    validate_versions.assert_called_once_with(("VERSION",), "0.16.0")
    publish.assert_called_once()
    assert publish.call_args.args[1] == "0.16.0"
    create_tag.assert_called_once_with("0.16.0", False)
    assert push.call_args.args[1] == "v0.16.0"
    assert mirror.call_args.kwargs["version"] == "0.16.0"
    assert mirror.call_args.kwargs["allow_empty_assets"] is True


@pytest.mark.parametrize(
    ("reason", "project_types", "create_on_tag"),
    [
        ("normal-bump", [], False),
        ("normal-bump", ["python"], True),
        ("already-bumped", [], True),
    ],
)
def test_existing_release_version_recovery_is_narrow(
    reason: str, project_types: list[str], create_on_tag: bool
) -> None:
    """Normal publication and package paths must not enter Release repair."""
    from goal.cli.version_state import VersionDecision
    from goal.push.core import _recover_existing_generic_release_decision

    decision = VersionDecision(
        current_version="0.16.0",
        target_version="0.16.1",
        reason=reason,
        sources=(),
        baseline_version="0.16.0",
        baseline_evidence=("git-tag:v0.16.0",),
        registry_versions=(),
        unavailable_registries=(),
        derived_paths=(),
    )
    delivery = type("Delivery", (), {"mode": "direct-main"})()
    config = {
        "publishing": {
            "fallback": {
                "github_release": {
                    "enabled": True,
                    "owner": "wellmanifest",
                    "repo": "new-project",
                    "create_on_tag": create_on_tag,
                }
            }
        }
    }

    with patch("goal.push.core.reuse_exact_annotated_tag") as reuse:
        resolved, repaired = _recover_existing_generic_release_decision(
            "0.16.0",
            decision,
            clean_force_publish=True,
            delivery=delivery,
            project_types=project_types,
            publish_config=config,
        )

    assert resolved is decision
    assert repaired is False
    reuse.assert_not_called()


def test_governed_generic_release_failure_is_terminal() -> None:
    """Configured direct-main GitHub Release failure must not report success."""
    from goal.push.core import _mirror_github_release

    delivery = type("Delivery", (), {"mode": "direct-main"})()
    release_config = type("ReleaseConfig", (), {"create_on_tag": True})()
    with (
        patch(
            "goal.publish.github_fallback.get_github_release_config",
            return_value=release_config,
        ),
        patch(
            "goal.publish.github_fallback.try_github_release_on_tag",
            return_value=False,
        ) as mirror,
        pytest.raises(click.ClickException, match="GitHub Release creation failed"),
    ):
        _mirror_github_release(
            tag_name="v0.16.0",
            effective_no_tag=False,
            delivery=delivery,
            project_types=[],
            new_version="0.16.0",
            publish_config={},
        )

    assert mirror.call_args.kwargs["allow_empty_assets"] is True
    assert mirror.call_args.kwargs["artifacts"] == []


def test_package_release_does_not_allow_empty_assets() -> None:
    """Package create-on-tag calls retain the artifact requirement."""
    from goal.push.core import _mirror_github_release

    delivery = type("Delivery", (), {"mode": "direct-main"})()
    release_config = type("ReleaseConfig", (), {"create_on_tag": True})()
    with (
        patch(
            "goal.publish.github_fallback.get_github_release_config",
            return_value=release_config,
        ),
        patch(
            "goal.publish.github_fallback.try_github_release_on_tag",
            return_value=True,
        ) as mirror,
    ):
        _mirror_github_release(
            tag_name="v2.1.298",
            effective_no_tag=False,
            delivery=delivery,
            project_types=["python"],
            new_version="2.1.298",
            publish_config={},
        )

    assert mirror.call_args.kwargs["allow_empty_assets"] is False
    assert mirror.call_args.kwargs["artifacts"] is None


def test_publish_only_aborts_when_bootstrap_mutates_source() -> None:
    """Bootstrap mutations must fail before staging, tests, commit or publish."""
    from goal.push.core import execute_push_workflow

    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": {},
        "user_config": {},
        "delivery_mode": "publish-only",
    }
    delivery = type("Delivery", (), {"mode": "publish-only"})()

    with (
        patch("goal.governance.delivery.resolve_delivery_policy", return_value=delivery),
        patch("goal.governance.delivery.validate_delivery_ready"),
        patch("goal.push.core.check_pyproject_toml", return_value=None),
        patch("goal.push.core._initialize_context"),
        patch("goal.push.core._detect_project_types", return_value=["python"]),
        patch("goal.push.core._bootstrap_projects"),
        patch("goal.push.core.get_staged_files", return_value=[]),
        patch("goal.push.core.get_working_tree_files", return_value=["README.md"]),
        patch("goal.push.core.run_git") as run_git,
        patch("goal.push.core.run_test_stage") as tests,
        patch("goal.push.core._handle_commit_phase") as commit_phase,
        patch("goal.push.core.handle_publish") as publish,
        pytest.raises(click.ClickException, match="bootstrap modified.*README.md"),
    ):
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=True,
            no_version_sync=False,
            no_publish=False,
            force_publish=True,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket=None,
            abstraction=None,
            todo=False,
        )

    run_git.assert_not_called()
    tests.assert_not_called()
    commit_phase.assert_not_called()
    publish.assert_not_called()


def test_uv_sync_preserves_test_extra_when_dev_is_not_declared(tmp_path: Path) -> None:
    """A test-only project must never fall back to a destructive plain sync."""
    from goal.package_managers import get_uv_sync_command

    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo"
[project.optional-dependencies]
test = ["pytest", "ruff", "mypy"]
""".lstrip(),
        encoding="utf-8",
    )

    assert get_uv_sync_command(tmp_path) == "uv sync --extra test"


def test_python_bootstrap_requests_dev_and_test_dependency_sets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first lockfile sync must preserve both conventional tool-set names."""
    from goal import project_bootstrap

    (tmp_path / ".venv").mkdir()
    requested: list[str] = []
    monkeypatch.setattr(
        project_bootstrap.subprocess,
        "run",
        lambda *args, **kwargs: type("Result", (), {"returncode": 0})(),
    )
    monkeypatch.setattr(project_bootstrap, "_find_python_bin", lambda _path: "python")
    monkeypatch.setattr(project_bootstrap, "_ensure_costs_installed", lambda *_: None)
    monkeypatch.setattr(
        project_bootstrap,
        "_install_python_deps_broker",
        lambda _path, extras: (requested.extend(extras) or True),
    )
    monkeypatch.setattr(
        project_bootstrap,
        "_ensure_python_test_dependency",
        lambda *_args, **_kwargs: True,
    )

    assert project_bootstrap._ensure_python_env(
        tmp_path, project_bootstrap.PROJECT_BOOTSTRAP["python"], yes=True
    )
    assert requested == ["dev", "test"]
