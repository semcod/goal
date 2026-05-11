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

    click.echo(
        click.style(f"\n  📦 Installing test dependencies in {project_root}/", fg="cyan")
    )

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
            f"  💡 Fix: cd {project_root} && {python_bin} -m pip install -e .[dev]",
            fg="cyan",
        )
    )
    return False
