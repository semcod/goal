"""Tests for dependency update functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from goal.cli import main
from goal.dependency_update import _select_managers_to_update, update_project_dependencies
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
    assert _has_cli_flag(["-a", "-u"], "a", "--all") is True
    assert _has_cli_flag(["--all"], "a", "--all") is True
    assert _has_cli_flag(["push"], "a", "--all") is False


def test_au_sets_upgrade_deps_in_context() -> None:
    runner = CliRunner()
    captured = {}

    def fake_execute(ctx_obj, **kwargs):
        captured["upgrade_deps"] = ctx_obj.get("upgrade_deps")
        captured["yes"] = ctx_obj.get("yes")

    with (
        patch("goal.cli._show_goal_version_banner"),
        patch("goal.cli._warn_goal_binary_mismatch"),
        patch("goal.cli.push_cmd.execute_push_workflow", side_effect=fake_execute),
        patch("goal.push.commands.execute_push_workflow", side_effect=fake_execute),
    ):
        result = runner.invoke(main, ["-au"])

    assert result.exit_code == 0
    assert captured["upgrade_deps"] is True
    assert captured["yes"] is True
