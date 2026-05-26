"""Pytest availability checks for CLI test runs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

import click


def check_python_venv(project_root: Optional[Path]) -> tuple[bool, Optional[Path]]:
    """Check if Python project has a virtual environment. Returns (has_venv, project_root)."""
    if not project_root:
        return False, None
    venv_paths = [
        project_root / ".venv",
        project_root / "venv",
        project_root / "env",
    ]
    has_venv = any(v.exists() for v in venv_paths)
    return has_venv, project_root


def _is_uv_project(project_root: Path) -> bool:
    """Check if project is managed by uv."""
    return (project_root / "uv.lock").exists()


def _try_uv_install(project_root: Path) -> bool:
    """Try to install dependencies using uv sync."""
    result = subprocess.run(
        ["uv", "sync"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return False
    verify = subprocess.run(
        ["uv", "run", "python", "-c", "import pytest"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    return verify.returncode == 0


def ensure_pytest_for_project(project_root: Path, python_bin: str) -> bool:
    """Ensure pytest is available in the subproject environment."""
    check_result = subprocess.run(
        [python_bin, "-c", "import pytest"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if check_result.returncode == 0:
        return True

    # For uv-managed projects, also check via uv run
    if _is_uv_project(project_root):
        uv_check = subprocess.run(
            ["uv", "run", "python", "-c", "import pytest"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if uv_check.returncode == 0:
            return True

    click.echo(
        click.style(
            f"\n  📦 Installing test dependencies in {project_root}/", fg="cyan"
        )
    )

    # For uv-managed projects, use uv sync first
    if _is_uv_project(project_root):
        if _try_uv_install(project_root):
            return True

    install_attempts = [
        [python_bin, "-m", "pip", "install", "-e", ".[dev]"],
        [python_bin, "-m", "pip", "install", "-e", "."],
        [python_bin, "-m", "pip", "install", "pytest", "pytest-cov"],
    ]

    for cmd in install_attempts:
        install_result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if install_result.returncode != 0:
            continue

        verify = subprocess.run(
            [python_bin, "-c", "import pytest"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if verify.returncode == 0:
            return True

    click.echo(
        click.style(
            f"\n  ❌ Failed to install test dependencies in {project_root}/", fg="red"
        )
    )
    click.echo(
        click.style(
            f"  💡 Fix: cd {project_root} && uv sync",
            fg="cyan",
        )
    )
    return False
