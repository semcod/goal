"""Environment installation and setup - extracted from project_bootstrap.py."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import click

from goal.bootstrap.templates import PROJECT_TEMPLATES, ProjectTemplate
from goal.bootstrap.configurator import _find_python_bin
from goal.bootstrap.costs_badge import (
    _MIN_COSTS_VERSION,
    _costs_version_satisfies_minimum,
    _install_costs_requirement,
)
from goal.installers import PackageManagerBroker
from goal.installers.env import isolated_env
from goal.pyenv_health import diagnose as _diagnose_python_env
from goal.pyenv_health import repair as _repair_python_env


def _python_install_command(
    project_dir: Path, python_bin: str, *arguments: str
) -> list[str]:
    """Select the installer that owns the target Python environment.

    uv-created virtual environments normally have no ``pip`` module.  For a
    project with ``uv.lock`` use ``uv pip --python``; otherwise use the
    interpreter's regular ``python -m pip``.
    """
    uv_bin = shutil.which("uv")
    if uv_bin and (project_dir / "uv.lock").exists():
        return [uv_bin, "pip", "install", "--python", python_bin, *arguments]
    return [python_bin, "-m", "pip", "install", *arguments]


def _match_marker(base: Path, pattern: str) -> bool:
    """Check if a marker file/pattern exists under *base*."""
    if "*" in pattern:
        return bool(list(base.glob(pattern)))
    return (base / pattern).exists()


def _should_skip_install(project_dir: Path, markers: List[str]) -> bool:
    """Check if dependency installation can be skipped based on file modification times."""
    venv_dir = project_dir / ".venv"
    if not venv_dir.exists():
        return False

    sync_marker = venv_dir / ".goal_deps_ok"
    if not sync_marker.exists():
        return False

    marker_mtime = sync_marker.stat().st_mtime
    for marker in markers:
        config_file = project_dir / marker
        if config_file.exists() and config_file.stat().st_mtime > marker_mtime:
            return False

    return True


def _ensure_costs_installed(project_dir: Path, python_bin: str) -> bool:
    """Ensure the costs package is installed for AI tracking."""
    result = subprocess.run(
        [python_bin, "-c", "import costs; print(costs.__version__)"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )
    if result.returncode == 0:
        installed_version = result.stdout.strip()
        if _costs_version_satisfies_minimum(installed_version):
            return True
        click.echo(
            click.style(
                f"  Upgrading costs package ({installed_version} < {_MIN_COSTS_VERSION})...",
                fg="cyan",
            )
        )
    else:
        click.echo(click.style("  Installing costs package...", fg="cyan"))

    if _install_costs_requirement(project_dir, python_bin):
        click.echo(click.style("  ✓ costs installed", fg="green"))
        return True
    return False


def _install_python_deps_legacy(
    project_dir: Path, cfg: ProjectTemplate, python_bin: str
) -> None:
    """Legacy dependency installation using config-based commands."""
    marker_files = (
        cfg.marker_files
        if isinstance(cfg, ProjectTemplate)
        else cfg.get("marker_files", [])
    )
    if _should_skip_install(project_dir, marker_files):
        return

    has_uv = bool(shutil.which("uv"))
    dep_commands = (
        cfg.dep_install_commands
        if isinstance(cfg, ProjectTemplate)
        else cfg.get("dep_install_commands", [])
    )

    for dep_cfg in dep_commands:
        condition = dep_cfg["condition"]
        if not _match_marker(project_dir, condition):
            continue

        cmd = dep_cfg["cmd"].format(python=python_bin)

        # Optimize with uv if available
        if has_uv and "-m pip install" in cmd:
            cmd = cmd.replace(f"{python_bin} -m pip install", "uv pip install")
            if not cmd.startswith("uv"):
                cmd = f"uv pip install {cmd.split('install ', 1)[1]}"

        click.echo(click.style(f"  Installing deps: {cmd}", fg="cyan"))
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            env=isolated_env(str(project_dir)),
        )

        if result.returncode != 0:
            fallback = dep_cfg.get("fallback")
            if fallback:
                cmd = fallback.format(python=python_bin)
                click.echo(click.style(f"  Retrying: {cmd}", fg="yellow"))
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(project_dir),
                    capture_output=True,
                    text=True,
                    env=isolated_env(str(project_dir)),
                )

            if result.returncode != 0:
                click.echo(
                    click.style(
                        f"  ⚠  Dependency install had issues (exit {result.returncode})",
                        fg="yellow",
                    )
                )
                if result.stderr:
                    click.echo(
                        click.style(
                            f"    Error: {result.stderr.strip().splitlines()[-1]}",
                            fg="red",
                        )
                    )
                return

        # Mark as synced
        venv_dir = project_dir / ".venv"
        if venv_dir.exists():
            (venv_dir / ".goal_deps_ok").touch()

        click.echo(click.style("  ✓ Dependencies installed", fg="green"))
        break  # Only run the first matching dep install


def _install_python_deps_broker(
    project_dir: Path, extras: Optional[List[str]] = None
) -> bool:
    """Install Python dependencies using PackageManagerBroker.

    Delegates to intelligent broker that auto-detects and prioritizes
    fast package managers (uv, pdm, poetry) with pip as fallback.

    Args:
        project_dir: Project root directory
        extras: Optional list of extra dependency groups (e.g., ["dev", "test"])

    Returns:
        True if installation succeeded, False otherwise
    """
    broker = PackageManagerBroker(str(project_dir))
    try:
        # Lockfile-aware selection: poetry.lock → poetry, uv.lock → uv, etc.
        # Without this, uv (highest priority) is chosen even for Poetry projects,
        # and Poetry dependency *groups* (e.g. dev → pytest-asyncio) never install.
        result = broker.install_smart(extras=extras, auto_install_uv=True)
        return result.success
    except RuntimeError as e:
        click.echo(click.style(f"  ⚠  {e}", fg="yellow"))
        return False


def _pytest_addopts_satisfied(project_dir: Path, python_bin: str) -> bool:
    """Check pytest can actually collect, not just import.

    `import pytest` succeeding doesn't mean pytest can run: pyproject.toml's
    own `addopts` (e.g. `-n auto`) can require a plugin (pytest-xdist) that
    lives under `[project.optional-dependencies] dev` rather than being a
    hard dependency. A bare uv/pip sync that skips extras leaves `pytest`
    importable but every actual test run failing with argparse's
    "unrecognized arguments" before a single test collects -- reported here
    as a false "test dependency ready" (2026-07-06: code2llm's `-n auto`
    addopts silently broke `goal -a -y` this way after a plain `uv sync`).
    """
    probe = subprocess.run(
        [python_bin, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        timeout=60,
    )
    return "unrecognized arguments" not in probe.stderr


def _ensure_python_test_dependency(
    project_dir: Path, python_bin: str, test_dep: Optional[str]
) -> bool:
    """Ensure the Python test runner dependency is available in the project venv."""
    if not test_dep:
        return True

    def addopts_ok() -> bool:
        return test_dep != "pytest" or _pytest_addopts_satisfied(
            project_dir, python_bin
        )

    check_result = subprocess.run(
        [python_bin, "-c", f"import {test_dep}; print({test_dep}.__version__)"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )
    if check_result.returncode == 0 and addopts_ok():
        version = check_result.stdout.strip()
        if version:
            click.echo(
                click.style(f"  ✓ {test_dep} already installed ({version})", fg="green")
            )
        else:
            click.echo(click.style(f"  ✓ {test_dep} already installed", fg="green"))
        return True

    click.echo(click.style(f"  Installing test dependency: {test_dep}", fg="cyan"))
    install_result = subprocess.run(
        _python_install_command(project_dir, python_bin, test_dep),
        capture_output=True,
        text=True,
        cwd=str(project_dir),
        env=isolated_env(str(project_dir)),
    )
    if install_result.returncode == 0 and not addopts_ok():
        # pytest itself is fine, but the project's own addopts still can't
        # run -- a required plugin lives in a dev/optional extras group
        # that the bare install above doesn't pull in. Pull the full group.
        install_result = subprocess.run(
            _python_install_command(project_dir, python_bin, "-e", ".[dev]"),
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            env=isolated_env(str(project_dir)),
        )
        if install_result.returncode == 0 and not addopts_ok():
            click.echo(
                click.style(
                    f"  ⚠ {test_dep} installed but the project's own pytest addopts "
                    "still fail to run (check for a missing plugin under "
                    "[project.optional-dependencies] in pyproject.toml)",
                    fg="yellow",
                )
            )
            return False

    if install_result.returncode != 0:
        error = (install_result.stderr or install_result.stdout or "").strip()
        click.echo(
            click.style(
                f"  ⚠ Could not install test dependency: {test_dep}", fg="yellow"
            )
        )
        if error:
            click.echo(click.style(f"    {error.splitlines()[-1]}", fg="yellow"))
        return False

    click.echo(click.style(f"  ✓ Test dependency installed ({test_dep})", fg="green"))
    return True


def _ensure_venv_pyvenv_cfg_is_healthy(venv_path: Path) -> None:
    """Proactively catch/fix a venv whose pyvenv.cfg disagrees with its own
    interpreter -- before any pip install is attempted against it.

    This is the exact failure mode behind pip (and anything else importing
    ctypes) segfaulting for no apparent reason inside a seemingly-fine venv:
    the declared base Python build doesn't match the interpreter the venv's
    own bin/python actually resolves to, so compiled stdlib extensions load
    from the wrong build. Left undetected, every dependency install below
    (costs, the package manager broker, the test runner) fails the same way
    and each looks like an unrelated, unexplained error.
    """
    diagnosis = _diagnose_python_env(str(venv_path))
    if not diagnosis:
        return
    click.echo(click.style(f"\n⚠  {diagnosis}", fg="yellow"))
    click.echo(click.style("  Próbuję naprawić automatycznie...", fg="cyan"))
    if _repair_python_env(str(venv_path)):
        click.echo(
            click.style(
                "  ✓ Naprawiono pyvenv.cfg (dopasowano do rzeczywistego interpretera)",
                fg="green",
            )
        )
    else:
        click.echo(
            click.style(
                "  ⚠  Nie udało się naprawić automatycznie. Ostatnia deska ratunku: "
                f"usuń i odtwórz venv:\n    rm -rf {venv_path} && python3 -m venv {venv_path}",
                fg="yellow",
            )
        )


def _ensure_python_env(project_dir: Path, cfg: ProjectTemplate, yes: bool) -> bool:
    """Set up Python project environment: venv, pip, costs, deps, test deps."""
    venv_path = project_dir / ".venv"
    if not venv_path.exists():
        if not yes:
            click.echo(
                click.style(
                    f"\n⚠  No virtual environment found in {project_dir}", fg="yellow"
                )
            )
            if not click.confirm(
                click.style("Create .venv and install dependencies?", fg="cyan"),
                default=True,
            ):
                return True  # user declined, not a failure
        click.echo(click.style(f"  Creating .venv in {project_dir} ...", fg="cyan"))
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            click.echo(
                click.style(
                    f"  ✗ Failed to create venv: {result.stderr.strip()}", fg="red"
                )
            )
            return False
        click.echo(click.style("  ✓ Created .venv", fg="green"))

    python_bin = _find_python_bin(project_dir)
    _ensure_venv_pyvenv_cfg_is_healthy(venv_path)

    # Upgrade pip
    subprocess.run(
        [python_bin, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )

    # Install costs package for AI tracking
    _ensure_costs_installed(project_dir, python_bin)

    # Install deps using broker (preferred) or legacy method
    broker_success = _install_python_deps_broker(project_dir, extras=["dev"])
    if not broker_success:
        # Fallback to legacy method
        _install_python_deps_legacy(project_dir, cfg, python_bin)

    test_dep = cfg.test_dep if isinstance(cfg, ProjectTemplate) else cfg.get("test_dep")
    test_dep_ok = _ensure_python_test_dependency(project_dir, python_bin, test_dep)
    if test_dep_ok:
        return True

    # In non-interactive/automation mode, keep bootstrap successful even if
    # registry/network access prevents installing optional test tooling.
    if yes:
        click.echo(
            click.style(
                "  ⚠ Continuing bootstrap without test dependency (non-interactive mode).",
                fg="yellow",
            )
        )
        return True

    return False


def _needs_install(project_dir: Path, cfg: ProjectTemplate) -> bool:
    """Check if dependency installation is needed for a non-Python project."""
    env_dir = cfg.env_dir if isinstance(cfg, ProjectTemplate) else cfg.get("env_dir")
    if env_dir and (project_dir / env_dir).exists():
        return False  # Already set up

    if env_dir and not (project_dir / env_dir).exists():
        return True

    dep_commands = (
        cfg.dep_install_commands
        if isinstance(cfg, ProjectTemplate)
        else cfg.get("dep_install_commands", [])
    )
    for dep_cfg in dep_commands:
        condition = (
            dep_cfg["condition"]
            if isinstance(dep_cfg, dict)
            else dep_cfg.get("condition")
        )
        if _match_marker(project_dir, condition):
            return True

    return False


def _run_dep_install(project_dir: Path, dep_cfg: dict) -> bool:
    """Run a single dependency install command. Returns True if successful."""
    cmd = dep_cfg["cmd"] if isinstance(dep_cfg, dict) else dep_cfg.get("cmd")
    tool = cmd.split()[0]
    if not shutil.which(tool):
        click.echo(
            click.style(f"  ⚠  '{tool}' not found in PATH, skipping", fg="yellow")
        )
        return False

    click.echo(click.style(f"  Installing deps: {cmd}", fg="cyan"))
    result = subprocess.run(
        cmd, shell=True, cwd=str(project_dir), capture_output=True, text=True
    )
    if result.returncode == 0:
        click.echo(click.style("  ✓ Dependencies installed", fg="green"))
        return True
    else:
        click.echo(
            click.style(
                f"  ⚠  Install had issues (exit {result.returncode})", fg="yellow"
            )
        )
        return False


def _get_matching_dep_command(project_dir: Path, dep_commands: list) -> Optional[dict]:
    """Find the first dependency install command that matches the project."""
    for dep_cfg in dep_commands:
        condition = (
            dep_cfg["condition"]
            if isinstance(dep_cfg, dict)
            else dep_cfg.get("condition")
        )
        if _match_marker(project_dir, condition):
            return dep_cfg
    return None


def _ensure_generic_env(
    project_dir: Path, project_type: str, cfg: ProjectTemplate, yes: bool
) -> bool:
    """Set up a non-Python project environment (Node, Rust, Go, etc.)."""
    if not _needs_install(project_dir, cfg):
        return True

    if not yes:
        click.echo(
            click.style(
                f"\n⚠  Dependencies not installed for {project_type} project in {project_dir}",
                fg="yellow",
            )
        )
        if not click.confirm(
            click.style("Install dependencies?", fg="cyan"), default=True
        ):
            return True

    dep_commands = (
        cfg.dep_install_commands
        if isinstance(cfg, ProjectTemplate)
        else cfg.get("dep_install_commands", [])
    )
    dep_cfg = _get_matching_dep_command(project_dir, dep_commands)
    if dep_cfg:
        _run_dep_install(project_dir, dep_cfg)

    return True


def ensure_project_environment(
    project_dir: Path, project_type: str, yes: bool = False
) -> bool:
    """Ensure the project environment is properly set up.

    For Python: creates .venv if missing, installs dependencies.
    For Node: runs npm/yarn/pnpm install if node_modules missing.
    For others: runs the appropriate dependency install command.

    Returns True if environment is ready, False on failure.
    """
    cfg = PROJECT_TEMPLATES.get(project_type)
    if not cfg:
        return True

    project_dir = project_dir.resolve()

    if project_type == "python":
        return _ensure_python_env(project_dir, cfg, yes)
    return _ensure_generic_env(project_dir, project_type, cfg, yes)
