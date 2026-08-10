"""Regression coverage for ticket-024 delivery integrity boundaries."""

from pathlib import Path
from unittest.mock import patch

import click
import pytest


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
    ):
        with pytest.raises(click.ClickException, match="Git remote push failed"):
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
