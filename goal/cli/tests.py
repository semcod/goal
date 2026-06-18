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


def _pytest_importable(python_bin: str, project_root: Optional[Path] = None) -> bool:
    """Return True when pytest imports successfully in the given interpreter."""
    cwd = project_root or Path.cwd()
    result = subprocess.run(
        [python_bin, "-c", "import pytest"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _prefer_uv_run(python_bin: str, has_uv: bool) -> bool:
    """Use uv run only when the resolved interpreter cannot execute pytest."""
    if not has_uv:
        return False
    return not _pytest_importable(python_bin)


def _rewrite_bash_pytest_for_uv(
    test_cmd_str: str, has_uv: bool, python_bin: str
) -> Optional[str]:
    """Rewrite bash-wrapped venv pytest commands to uv run for uv-managed projects."""
    if not _prefer_uv_run(python_bin, has_uv) or "-m pytest" not in test_cmd_str:
        return None

    import re

    match = re.search(r"-m\s+pytest(?:\s+(.+?))?(?:'|\"|$)", test_cmd_str)
    if not match:
        return None

    args = (match.group(1) or "").strip().strip("'\"")
    return f"uv run pytest {args}".strip()


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


_last_test_wall_time = 0.0


def _has_package(python_bin: str, package_name: str) -> bool:
    """Check if a package is available in the specified python interpreter."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        return False
    try:
        res = subprocess.run(
            [python_bin, "-c", f"import {package_name}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False


def _run_python_test(test_dir: str, base_cmd: List[str]) -> tuple[bool, bool]:
    """Run Python tests in a subdirectory. Returns (success, skipped)."""
    import shutil
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
    
    # Check if project is managed by uv - if so, skip pip-based pytest installation
    has_uv = bool(shutil.which("uv")) and "PYTEST_CURRENT_TEST" not in os.environ
    uv_lock = project_root / "uv.lock"
    pyproject_toml = project_root / "pyproject.toml"
    is_uv_project = has_uv and (uv_lock.exists() or pyproject_toml.exists())
    
    if not is_uv_project:
        if not _ensure_pytest_for_project(project_root, python_bin):
            click.echo(
                click.style(f"\n  ⏭️  Skipping {project_root.name}/ tests", fg="yellow")
            )
            return True, True
    if has_uv:
        subdir_cmd = ["uv", "run", "pytest"]
    else:
        subdir_cmd = [python_bin, "-m", "pytest"]

    # Automatically enable parallel testing if xdist is installed
    if _has_package(python_bin, "xdist"):
        subdir_cmd += ["-n", "auto", "--dist", "loadscope"]

    # Automatically enable incremental testing if testmon is installed
    if _has_package(python_bin, "testmon"):
        subdir_cmd += ["--testmon"]

    # Enable JUnit XML report to measure individual test durations
    if "PYTEST_CURRENT_TEST" not in os.environ:
        subdir_cmd += ["--junitxml=.goal_test_report.xml"]

    import time
    start_time = time.time()
    result = subprocess.run(
        subdir_cmd + [test_dir], capture_output=True, text=True, timeout=120
    )
    elapsed = time.time() - start_time
    global _last_test_wall_time
    _last_test_wall_time = elapsed
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
    import shutil
    python_bin = _resolve_root_python()
    use_subprocess = True
    has_uv = bool(shutil.which("uv")) and "PYTEST_CURRENT_TEST" not in os.environ
    use_uv_run = _prefer_uv_run(python_bin, has_uv)

    if strategy_test_cmd:
        coerced_cmd = _coerce_python_strategy_to_project_pytest(
            test_cmd_str, python_bin
        )
        if coerced_cmd is not None:
            if use_uv_run:
                if coerced_cmd[0] == python_bin and coerced_cmd[1:3] == ["-m", "pytest"]:
                    coerced_cmd = ["uv", "run", "pytest"] + coerced_cmd[3:]
            return coerced_cmd, use_subprocess, python_bin
        uv_cmd = _rewrite_bash_pytest_for_uv(test_cmd_str, has_uv, python_bin)
        if uv_cmd:
            return uv_cmd.split(), False, python_bin
        return test_cmd_str.split(), False, python_bin

    # Default command
    if use_uv_run:
        cmd = ["uv", "run", "pytest"]
    else:
        cmd = [python_bin, "-m", "pytest"]

    # Automatically enable parallel testing if xdist is installed
    if _has_package(python_bin, "xdist"):
        cmd += ["-n", "auto", "--dist", "loadscope"]

    # Automatically enable incremental testing if testmon is installed
    if _has_package(python_bin, "testmon"):
        cmd += ["--testmon"]

    return cmd, use_subprocess, python_bin


def _ensure_root_pytest_or_mark_failed(
    python_bin: str,
    run_subdir_scan: bool,
    ptype: str,
    test_cmd: List[str],
) -> bool:
    """Ensure root pytest is available; optionally continue with subdir diagnostics."""
    import shutil
    
    # Check if project is managed by uv - if so, skip pip-based pytest installation
    has_uv = bool(shutil.which("uv")) and "PYTEST_CURRENT_TEST" not in os.environ
    uv_lock = Path.cwd() / "uv.lock"
    pyproject_toml = Path.cwd() / "pyproject.toml"
    is_uv_project = has_uv and (uv_lock.exists() or pyproject_toml.exists())

    if _pytest_importable(python_bin):
        return True

    if is_uv_project:
        if _ensure_pytest_for_project(Path.cwd(), python_bin):
            return True
    elif _ensure_pytest_for_project(Path.cwd(), python_bin):
        return True
    click.echo(
        click.style("\n  ❌ Root python environment is missing pytest.", fg="red")
    )
    if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
        return False
    return False


def _run_root_test(
    test_cmd: List[str], test_cmd_str: str, use_subprocess: bool, *, markdown: bool = False
) -> bool:
    """Run root project tests."""
    import time

    from goal.io.stdio import echo_command_block, echo_output_block, use_markdown_stdio

    # Ensure --junitxml is added to capture test durations
    if use_subprocess and "pytest" in test_cmd_str and "PYTEST_CURRENT_TEST" not in os.environ:
        if "--junitxml=.goal_test_report.xml" not in test_cmd:
            test_cmd = test_cmd + ["--junitxml=.goal_test_report.xml"]

    if markdown and use_markdown_stdio():
        echo_command_block(" ".join(test_cmd), language="bash")

    start_time = time.time()
    if use_subprocess:
        capture = markdown and use_markdown_stdio()
        result = subprocess.run(
            test_cmd,
            capture_output=capture,
            text=True,
        )
        if capture:
            combined = (result.stdout or "") + (result.stderr or "")
            echo_output_block(combined, language="pytest")
    else:
        result = run_command(test_cmd_str, capture=False)
    elapsed = time.time() - start_time

    global _last_test_wall_time
    _last_test_wall_time = elapsed

    return result.returncode == 0


def _run_project_type_tests(ptype: str, config: object, *, markdown: bool = False) -> bool:
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

    ok = _run_root_test(test_cmd, test_cmd_str, use_subprocess, markdown=markdown)
    if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
        ok = False
    return ok


def run_tests(
    project_types: List[str], config: object = None, *, markdown: bool = False
) -> bool:
    """Run tests for detected project types."""
    success = True

    for ptype in project_types:
        try:
            if not _run_project_type_tests(ptype, config, markdown=markdown):
                success = False
        except Exception:
            success = False

    return success


def get_test_execution_details() -> dict:
    """Parse .goal_test_report.xml to extract execution details, test durations, and startup overhead."""
    import xml.etree.ElementTree as ET
    from pathlib import Path

    report_path = Path(".goal_test_report.xml")
    details = {
        "wall_time": globals().get("_last_test_wall_time", 0.0),
        "total_test_time": 0.0,
        "startup_overhead": 0.0,
        "slow_tests": []
    }

    if not report_path.exists():
        return details

    try:
        tree = ET.parse(report_path)
        root = tree.getroot()

        # Get total test execution time
        total_time = 0.0
        test_cases = []

        # Find all test cases in the XML
        for tc in root.iter("testcase"):
            name = tc.get("name", "unknown")
            classname = tc.get("classname", "unknown")
            try:
                tc_time = float(tc.get("time", 0.0))
            except (ValueError, TypeError):
                tc_time = 0.0

            total_time += tc_time
            test_cases.append({
                "name": name,
                "classname": classname,
                "duration": tc_time
            })

        # Sort test cases by duration descending
        test_cases.sort(key=lambda x: x["duration"], reverse=True)

        details["total_test_time"] = total_time
        # Startup overhead is wall-clock time minus sum of test execution times
        details["startup_overhead"] = max(0.0, details["wall_time"] - total_time)
        details["slow_tests"] = test_cases

        # Clean up the XML report
        try:
            report_path.unlink()
        except Exception:
            pass

    except Exception:
        pass

    return details


__all__ = [
    "_has_usable_test_script",
    "_run_tests_in_subdirs",
    "run_tests",
    "get_test_execution_details",
]
