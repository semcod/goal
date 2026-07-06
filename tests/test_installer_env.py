"""Tests for project-venv environment isolation (installers.env)."""

import os

from goal.installers.env import isolated_env


def test_points_virtualenv_at_project_venv(tmp_path, monkeypatch):
    """When <project>/.venv exists, VIRTUAL_ENV is scoped to it, not the ambient one."""
    project = tmp_path / "proj"
    venv = project / ".venv" / "bin"
    venv.mkdir(parents=True)
    monkeypatch.setenv("VIRTUAL_ENV", "/some/outer/venv")

    env = isolated_env(str(project))

    assert env["VIRTUAL_ENV"] == str(project / ".venv")
    assert env["PATH"].startswith(str(project / ".venv" / "bin") + os.pathsep)


def test_drops_conda_prefix(tmp_path, monkeypatch):
    """CONDA_PREFIX is always removed so conda base envs don't interfere."""
    (tmp_path / ".venv").mkdir()
    monkeypatch.setenv("CONDA_PREFIX", "/opt/conda")

    env = isolated_env(str(tmp_path))

    assert "CONDA_PREFIX" not in env


def test_removes_ambient_virtualenv_when_no_project_venv(tmp_path, monkeypatch):
    """With no project .venv, an ambient VIRTUAL_ENV is removed (not inherited)."""
    monkeypatch.setenv("VIRTUAL_ENV", "/some/outer/venv")

    env = isolated_env(str(tmp_path))  # tmp_path has no .venv

    assert "VIRTUAL_ENV" not in env


def test_defaults_to_cwd(tmp_path, monkeypatch):
    """Without an explicit project_dir, the current working directory is used."""
    (tmp_path / ".venv").mkdir()
    monkeypatch.chdir(tmp_path)

    env = isolated_env()

    assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")
