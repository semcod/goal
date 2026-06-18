"""Tests for dependency update functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from goal.cli import main
from goal.dependency_update import (
    _select_managers_to_update,
    discover_dependency_project_roots,
    update_project_dependencies,
)
from goal.package_managers import get_package_manager, get_update_all_command


def test_get_update_all_command_for_uv() -> None:
    pm = get_package_manager("uv")
    command = get_update_all_command(pm, Path("."))
    assert command == "uv sync --upgrade"


def test_get_update_all_command_for_pip_with_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("click>=8.0\n")
    pm = get_package_manager("pip")
    command = get_update_all_command(pm, tmp_path)
    assert command == "pip install --upgrade -r requirements.txt"


def test_get_update_all_command_for_go() -> None:
    pm = get_package_manager("go")
    command = get_update_all_command(pm, Path("."))
    assert command == "go get -u ./..."


def test_select_managers_uses_only_highest_priority_python_lockfile(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    (tmp_path / "uv.lock").write_text("")
    (tmp_path / "poetry.lock").write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [
            get_package_manager("poetry"),
            get_package_manager("uv"),
            get_package_manager("pip"),
        ],
    )

    managers = _select_managers_to_update(str(tmp_path))
    assert [pm.name for pm in managers] == ["uv"]


def test_select_managers_uv_only_without_poetry_lock(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    (tmp_path / "uv.lock").write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [
            get_package_manager("poetry"),
            get_package_manager("uv"),
            get_package_manager("pip"),
        ],
    )

    managers = _select_managers_to_update(str(tmp_path))
    assert [pm.name for pm in managers] == ["uv"]


def test_select_managers_prefers_lockfile_manager(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    (tmp_path / "uv.lock").write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [
            get_package_manager("poetry"),
            get_package_manager("uv"),
            get_package_manager("pip"),
        ],
    )

    managers = _select_managers_to_update(str(tmp_path))
    assert [pm.name for pm in managers] == ["uv"]


def test_update_project_dependencies_dry_run(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    (tmp_path / "uv.lock").write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [get_package_manager("uv")],
    )
    monkeypatch.setattr(
        "goal.dependency_update._run_update_command",
        lambda command, cwd: (_ for _ in ()).throw(
            AssertionError("should not run in dry-run")
        ),
    )

    results = update_project_dependencies(yes=True, dry_run=True)
    assert results == []


def test_update_project_dependencies_runs_detected_manager(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
    (tmp_path / "uv.lock").write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [get_package_manager("uv")],
    )

    calls = []

    def fake_run(command, cwd):
        calls.append((command, cwd))
        from goal.dependency_update import DependencyUpdateResult

        return DependencyUpdateResult(
            manager="",
            command=command,
            success=True,
            duration_s=0.1,
        )

    monkeypatch.setattr("goal.dependency_update._run_update_command", fake_run)

    results = update_project_dependencies(yes=True, dry_run=False)
    assert len(results) == 1
    assert results[0].success is True
    assert calls == [("uv sync --upgrade", str(tmp_path.resolve()))]


def test_has_cli_flag_detects_combined_short_options() -> None:
    from goal.cli import _has_cli_flag

    assert _has_cli_flag(["-au"], "a", "--all") is True
    assert _has_cli_flag(["-au"], "u", "--upgrade-deps") is True
    assert _has_cli_flag(["-aur"], "a", "--all") is True
    assert _has_cli_flag(["-aur"], "u", "--upgrade-deps") is True
    assert _has_cli_flag(["-aur"], "r", "--recursive") is True
    assert _has_cli_flag(["-ar"], "a", "--all") is True
    assert _has_cli_flag(["-ar"], "r", "--recursive") is True
    assert _has_cli_flag(["-a", "-u"], "a", "--all") is True
    assert _has_cli_flag(["--all"], "a", "--all") is True
    assert _has_cli_flag(["push"], "a", "--all") is False


def test_discover_dependency_project_roots_finds_subprojects(
    tmp_path: Path, monkeypatch
) -> None:
    root_pkg = tmp_path / "packages" / "backend"
    root_pkg.mkdir(parents=True)
    (root_pkg / "pyproject.toml").write_text("[project]\nname='backend'\n")
    (root_pkg / "uv.lock").write_text("")

    other_pkg = tmp_path / "packages" / "frontend"
    other_pkg.mkdir(parents=True)
    (other_pkg / "pyproject.toml").write_text("[project]\nname='frontend'\n")
    (other_pkg / "uv.lock").write_text("")

    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [get_package_manager("uv")],
    )

    roots = discover_dependency_project_roots(str(tmp_path), recursive=False)
    assert {path.name for path in roots} == {"backend", "frontend"}


def test_discover_dependency_project_roots_respects_recursive_flag(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='root'\n")
    (tmp_path / "uv.lock").write_text("")

    sub_pkg = tmp_path / "packages" / "worker"
    sub_pkg.mkdir(parents=True)
    (sub_pkg / "pyproject.toml").write_text("[project]\nname='worker'\n")
    (sub_pkg / "uv.lock").write_text("")

    monkeypatch.setattr(
        "goal.dependency_update.get_available_package_managers",
        lambda project_path: [get_package_manager("uv")],
    )

    roots = discover_dependency_project_roots(str(tmp_path), recursive=False)
    assert [path.name for path in roots] == [tmp_path.name]

    roots_recursive = discover_dependency_project_roots(str(tmp_path), recursive=True)
    assert {path.name for path in roots_recursive} == {tmp_path.name, "worker"}


def test_aur_sets_recursive_and_upgrade_deps_in_context() -> None:
    import goal.cli.push_cmd as push_cmd

    runner = CliRunner()
    captured = {}

    def fake_execute(ctx_obj, **kwargs):
        captured["upgrade_deps"] = ctx_obj.get("upgrade_deps")
        captured["recursive"] = ctx_obj.get("recursive")
        captured["yes"] = ctx_obj.get("yes")

    with (
        patch("goal.cli._show_goal_version_banner"),
        patch("goal.cli._warn_goal_binary_mismatch"),
        patch.object(push_cmd, "execute_push_workflow", side_effect=fake_execute) as mock_execute,
        patch("goal.push.core.execute_push_workflow", side_effect=fake_execute),
    ):
        result = runner.invoke(main, ["-aur"])

    assert mock_execute.called, "execute_push_workflow mock was not invoked"
    assert result.exit_code == 0, result.output
    assert captured["upgrade_deps"] is True
    assert captured["recursive"] is True
    assert captured["yes"] is True


def test_ar_sets_recursive_in_context() -> None:
    import goal.cli.push_cmd as push_cmd

    runner = CliRunner()
    captured = {}

    def fake_execute(ctx_obj, **kwargs):
        captured["recursive"] = ctx_obj.get("recursive")
        captured["yes"] = ctx_obj.get("yes")

    with (
        patch("goal.cli._show_goal_version_banner"),
        patch("goal.cli._warn_goal_binary_mismatch"),
        patch.object(push_cmd, "execute_push_workflow", side_effect=fake_execute),
        patch("goal.push.core.execute_push_workflow", side_effect=fake_execute),
    ):
        result = runner.invoke(main, ["-ar"])

    assert result.exit_code == 0, result.output
    assert captured["recursive"] is True
    assert captured["yes"] is True


def test_upgrade_deps_runs_before_bootstrap(monkeypatch) -> None:
    """Dependency updates must run before uv sync, which can remove goal from the venv."""
    from goal.push import core as push_core

    call_order: list[str] = []

    monkeypatch.setattr(
        push_core,
        "_detect_project_types",
        lambda: (call_order.append("detect") or ["python"]),
    )
    monkeypatch.setattr(
        push_core,
        "_bootstrap_projects",
        lambda project_types, dry_run, yes: call_order.append("bootstrap"),
    )
    monkeypatch.setattr(
        push_core,
        "refresh_test_dependencies",
        lambda *args, **kwargs: call_order.append("refresh"),
    )

    import goal.dependency_update as dependency_update

    monkeypatch.setattr(
        dependency_update,
        "update_project_dependencies",
        lambda **kwargs: (call_order.append("upgrade") or []),
    )

    ctx_obj = {
        "yes": True,
        "upgrade_deps": True,
        "no_publish": True,
        "markdown": False,
        "message": None,
        "user_config": {},
    }

    with (
        patch("goal.push.core._validate_toml_or_exit"),
        patch("goal.push.core._initialize_context"),
        patch("goal.push.core.handle_todo_stage", return_value=True),
        patch("goal.push.core.get_staged_files", return_value=[]),
        patch("goal.push.core._handle_no_files", return_value=True),
    ):
        push_core.execute_push_workflow(
            ctx_obj,
            bump="patch",
            no_tag=True,
            no_changelog=True,
            no_version_sync=True,
            message=None,
            dry_run=True,
            yes=True,
            markdown=False,
            split=False,
            ticket=None,
            abstraction=None,
            todo=False,
            no_publish=True,
        )

    assert call_order[:3] == ["detect", "upgrade", "bootstrap"]
    assert call_order[-1] == "refresh"


def test_au_sets_upgrade_deps_in_context() -> None:
    import goal.cli.push_cmd as push_cmd

    runner = CliRunner()
    captured = {}

    def fake_execute(ctx_obj, **kwargs):
        captured["upgrade_deps"] = ctx_obj.get("upgrade_deps")
        captured["yes"] = ctx_obj.get("yes")

    with (
        patch("goal.cli._show_goal_version_banner"),
        patch("goal.cli._warn_goal_binary_mismatch"),
        patch.object(push_cmd, "execute_push_workflow", side_effect=fake_execute) as mock_execute,
        patch("goal.push.core.execute_push_workflow", side_effect=fake_execute),
    ):
        result = runner.invoke(main, ["-au"])

    assert mock_execute.called, "execute_push_workflow mock was not invoked"
    assert result.exit_code == 0, result.output
    assert captured["upgrade_deps"] is True
    assert captured["yes"] is True


def test_au_sets_markdown_in_context() -> None:
    import goal.cli.push_cmd as push_cmd

    runner = CliRunner()
    captured = {}

    def fake_execute(ctx_obj, **kwargs):
        captured["markdown_ctx"] = ctx_obj.get("markdown")
        captured["markdown_kw"] = kwargs.get("markdown")

    with (
        patch("goal.cli._show_goal_version_banner"),
        patch("goal.cli._warn_goal_binary_mismatch"),
        patch.object(push_cmd, "execute_push_workflow", side_effect=fake_execute),
        patch("goal.push.core.execute_push_workflow", side_effect=fake_execute),
    ):
        result = runner.invoke(main, ["-au"])

    assert result.exit_code == 0, result.output
    assert captured["markdown_ctx"] is True
    assert captured["markdown_kw"] is True


def test_all_with_ascii_keeps_ascii_output() -> None:
    import goal.cli.push_cmd as push_cmd

    runner = CliRunner()
    captured = {}

    def fake_execute(ctx_obj, **kwargs):
        captured["markdown_ctx"] = ctx_obj.get("markdown")
        captured["markdown_kw"] = kwargs.get("markdown")

    with (
        patch("goal.cli._show_goal_version_banner"),
        patch("goal.cli._warn_goal_binary_mismatch"),
        patch.object(push_cmd, "execute_push_workflow", side_effect=fake_execute),
        patch("goal.push.core.execute_push_workflow", side_effect=fake_execute),
    ):
        result = runner.invoke(main, ["-a", "--ascii", "push"])

    assert result.exit_code == 0, result.output
    assert captured["markdown_ctx"] is False
    assert captured["markdown_kw"] is False
