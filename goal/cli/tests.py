"""Test running functions - extracted from cli.py."""

import os
import shlex
import subprocess
from pathlib import Path
from typing import List, Optional

import click

from goal.git_ops import run_command
from goal.cli.version import PROJECT_TYPES
from goal.project_bootstrap import _find_python_bin
from goal.cli.tests_discovery import (
    _find_project_root,
    _has_usable_test_script,
    find_nodejs_test_dirs as _find_nodejs_test_dirs,
    find_python_test_dirs as _find_python_test_dirs,
)
from goal.cli.tests_pytest_setup import (
    check_python_venv as _check_python_venv,
    ensure_pytest_for_project as _ensure_pytest_for_project,
)


def _get_project_strategy(config: object, project_type: str) -> dict:
    """Get strategy config for a project type from GoalConfig/dict."""
    if config is None:
        return {}

    if hasattr(config, "get_strategy"):
        try:
            return config.get_strategy(project_type) or {}
        except Exception:
            return {}

    if isinstance(config, dict):
        return config.get("strategies", {}).get(project_type, {}) or {}

    return {}


def _active_venv_python() -> Optional[str]:
    """Return active virtualenv Python path when VIRTUAL_ENV is set."""
    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        return None
    candidate = Path(venv) / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return None


def _resolve_project_python(project_root: Optional[Path], fallback_python: str) -> str:
    """Resolve Python interpreter for a subproject, preferring its own virtualenv."""
    if not project_root:
        return fallback_python
    try:
        candidate = Path(_find_python_bin(project_root))
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        return str(candidate)
    except Exception:
        return fallback_python


def _coerce_python_strategy_to_project_pytest(
    test_cmd_str: str, python_bin: str
) -> Optional[List[str]]:
    """Convert common pytest strategy commands to use the resolved project Python."""
    try:
        args = shlex.split(test_cmd_str)
    except Exception:
        return None

    if not args:
        return None

    first = Path(args[0]).name
    if first in {"pytest", "py.test"}:
        return [python_bin, "-m", "pytest", *args[1:]]

    if (
        first in {"python", "python3"}
        and len(args) >= 3
        and args[1] == "-m"
        and args[2] == "pytest"
    ):
        return [python_bin, "-m", "pytest", *args[3:]]

    return None


def _display_test_error(
    result: subprocess.CompletedProcess, test_dir: str, project_type: str
) -> None:
    """Display test failure output."""
    click.echo(click.style(f"\n  ❌ Tests failed in {test_dir}/", fg="red"))
    if result.stdout:
        click.echo(click.style("  stdout:", fg="yellow"))
        for line in result.stdout.strip().split("\n")[:10]:
            click.echo(f"    {line}")
    if result.stderr:
        click.echo(click.style("  stderr:", fg="yellow"))
        for line in result.stderr.strip().split("\n")[:10]:
            click.echo(f"    {line}")
    if project_type == "nodejs":
        if not (Path(test_dir) / "node_modules").exists():
            click.echo(
                click.style(f"\n  💡 Fix: cd {test_dir} && npm install", fg="cyan")
            )
        elif "Cannot find module" in (result.stderr or ""):
            click.echo(
                click.style(f"\n  💡 Fix: cd {test_dir} && npm run compile", fg="cyan")
            )


def _run_python_test(test_dir: str, base_cmd: List[str]) -> tuple[bool, bool]:
    """Run Python tests in a subdirectory. Returns (success, skipped)."""
    project_root = _find_project_root(Path(test_dir), "python")
    if not project_root:
        return True, True

    has_venv, _ = _check_python_venv(project_root)
    if not has_venv:
        click.echo(
            click.style(
                f"  ⏭️  Skipping {project_root.name}/ - no virtual environment (run 'goal doctor' to set up)",
                fg="yellow",
            )
        )
        return True, True

    python_bin = _resolve_project_python(project_root, base_cmd[0])
    if not _ensure_pytest_for_project(project_root, python_bin):
        click.echo(
            click.style(f"\n  ⏭️  Skipping {project_root.name}/ tests", fg="yellow")
        )
        return True, True

    subdir_cmd = [python_bin, "-m", "pytest"]
    result = subprocess.run(
        subdir_cmd + [test_dir], capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        _display_test_error(result, test_dir, "python")
        return False, False
    return True, False


def _run_nodejs_test(test_dir: str, base_cmd: List[str]) -> bool:
    """Run Node.js tests in a subdirectory. Returns True on success."""
    result = subprocess.run(
        base_cmd, cwd=test_dir, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        _display_test_error(result, test_dir, "nodejs")
        return False
    return True


def _run_subdir_test(project_type: str, base_cmd: List[str], test_dir: str) -> bool:
    """Run a single sub-directory test. Returns True on success."""
    try:
        if project_type == "python":
            success, _ = _run_python_test(test_dir, base_cmd)
            return success
        else:
            return _run_nodejs_test(test_dir, base_cmd)
    except Exception as e:
        click.echo(
            click.style(f"\n  ❌ Error running tests in {test_dir}/: {e}", fg="red")
        )
        return False


def _run_tests_in_subdirs(project_type: str, base_cmd: List[str]) -> bool:
    """Run tests in subdirectories (monorepo support)."""
    finders = {"python": _find_python_test_dirs, "nodejs": _find_nodejs_test_dirs}
    finder = finders.get(project_type)
    if not finder:
        return True

    test_dirs = finder()
    if not test_dirs:
        return True

    if test_dirs:
        click.echo(
            click.style(
                f"  📁 Running tests in {len(test_dirs)} subproject(s): {', '.join(test_dirs[:5])}",
                fg="cyan",
            )
        )

    return all(_run_subdir_test(project_type, base_cmd, d) for d in test_dirs[:5])


def _resolve_root_python() -> str:
    """Resolve python executable for root test run."""
    active_python = _active_venv_python()
    if active_python:
        return active_python
    detected_python = Path(_find_python_bin(Path.cwd()))
    if not detected_python.is_absolute():
        detected_python = (Path.cwd() / detected_python).resolve()
    return str(detected_python)


def _build_python_test_command(
    test_cmd_str: str, strategy_test_cmd: str
) -> tuple[List[str], bool, str]:
    """Build python test command and execution mode."""
    python_bin = _resolve_root_python()
    use_subprocess = True
    if strategy_test_cmd:
        coerced_cmd = _coerce_python_strategy_to_project_pytest(
            test_cmd_str, python_bin
        )
        if coerced_cmd is not None:
            return coerced_cmd, use_subprocess, python_bin
        return test_cmd_str.split(), False, python_bin
    return [python_bin, "-m", "pytest"], use_subprocess, python_bin


def _ensure_root_pytest_or_mark_failed(
    python_bin: str,
    run_subdir_scan: bool,
    ptype: str,
    test_cmd: List[str],
) -> bool:
    """Ensure root pytest is available; optionally continue with subdir diagnostics."""
    if _ensure_pytest_for_project(Path.cwd(), python_bin):
        return True
    click.echo(
        click.style("\n  ❌ Root python environment is missing pytest.", fg="red")
    )
    if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
        return False
    return False


def _run_root_test(
    test_cmd: List[str], test_cmd_str: str, use_subprocess: bool
) -> bool:
    """Run root project tests."""
    if use_subprocess:
        result = subprocess.run(
            test_cmd,
            capture_output=False,
            text=True,
        )
    else:
        result = run_command(test_cmd_str, capture=False)
    return result.returncode == 0


def _run_project_type_tests(ptype: str, config: object) -> bool:
    """Run tests for a single detected project type."""
    project_config = PROJECT_TYPES.get(ptype, {})
    strategy = _get_project_strategy(config, ptype)
    strategy_test_cmd = strategy.get("test", "") if isinstance(strategy, dict) else ""
    if not isinstance(strategy_test_cmd, str):
        strategy_test_cmd = ""
    test_cmd_str = strategy_test_cmd or project_config.get("test_command", "")
    run_subdir_scan = not bool(strategy_test_cmd)
    if not test_cmd_str:
        return True

    if ptype == "nodejs" and not _has_usable_test_script(Path("."), "nodejs"):
        return True

    if ptype == "python":
        test_cmd, use_subprocess, python_bin = _build_python_test_command(
            test_cmd_str, strategy_test_cmd
        )
        if not _ensure_root_pytest_or_mark_failed(
            python_bin, run_subdir_scan, ptype, test_cmd
        ):
            return False
    else:
        test_cmd = test_cmd_str.split()
        use_subprocess = False

    ok = _run_root_test(test_cmd, test_cmd_str, use_subprocess)
    if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
        ok = False
    return ok


def run_tests(project_types: List[str], config: object = None) -> bool:
    """Run tests for detected project types."""
    success = True

    for ptype in project_types:
        try:
            if not _run_project_type_tests(ptype, config):
                success = False
        except Exception:
            success = False

    return success


__all__ = [
    "_has_usable_test_script",
    "_run_tests_in_subdirs",
    "run_tests",
]
