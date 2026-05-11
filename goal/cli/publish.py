"""Publishing functions - extracted from cli.py."""

import subprocess
import time
from pathlib import Path
from typing import Any, List

import click
import yaml

from goal.git_ops import run_command_tee
from goal.cli.version import PROJECT_TYPES
from goal.toml_validation import validate_project_toml_files


def makefile_has_target(target: str) -> bool:
    """Check if Makefile has a specific target."""
    makefile = Path('Makefile')
    if not makefile.exists() or not makefile.is_file():
        return False
    try:
        content = makefile.read_text(errors='ignore')
    except Exception:
        return False
    import re
    return re.search(rf'^\s*{re.escape(target)}\s*:', content, re.MULTILINE) is not None


def _get_project_strategy(config: Any, project_type: str) -> dict:
    """Get the configured strategy for a project type, if available."""
    if config is None:
        return {}

    if hasattr(config, 'get_strategy'):
        try:
            return config.get_strategy(project_type) or {}
        except Exception:
            return {}

    if isinstance(config, dict):
        return config.get('strategies', {}).get(project_type, {}) or {}

    return {}


def _get_configured_project_types(config: Any) -> List[str]:
    """Get project types from the active configuration without default fallbacks."""
    if config is None:
        return []

    if isinstance(config, dict):
        raw_config = config
    else:
        config_path = getattr(config, 'config_path', None)
        if not config_path:
            return []

        config_file = Path(config_path)
        if not config_file.exists():
            return []

        try:
            raw_config = yaml.safe_load(config_file.read_text(encoding='utf-8')) or {}
        except Exception:
            return []

        if not isinstance(raw_config, dict):
            return []

    project_config = raw_config.get('project', {})
    project_types = project_config.get('type', []) if isinstance(project_config, dict) else []

    if isinstance(project_types, str):
        return [project_types]

    if isinstance(project_types, list):
        return [ptype for ptype in project_types if isinstance(ptype, str)]

    return []


def _get_python_bin() -> str:
    """Get the Python binary to use for publishing."""
    # Check for venv in current directory (priority order: .venv, venv, env)
    for venv_name in ['.venv', 'venv', 'env']:
        venv_python = Path('.') / venv_name / 'bin' / 'python'
        if venv_python.exists():
            return str(venv_python.resolve())
    # Fall back to sys.executable
    import sys
    return sys.executable


def _ensure_publish_deps(python_bin: str) -> bool:
    """Ensure build and twine are installed for publishing."""
    # Check if build is available
    result = subprocess.run(
        [python_bin, '-m', 'build', '--help'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        click.echo(click.style(f"  Installing build module...", fg='cyan'))
        install_result = subprocess.run(
            [python_bin, '-m', 'pip', 'install', '--quiet', 'build'],
            capture_output=True, text=True,
            cwd=str(Path('.'))
        )
        if install_result.returncode != 0:
            click.echo(click.style(f"  ✗ Failed to install build module: {install_result.stderr}", fg='red'))
            return False
        click.echo(click.style(f"  ✓ build installed", fg='green'))

    # Check if twine is available
    result = subprocess.run(
        [python_bin, '-m', 'twine', '--help'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        click.echo(click.style(f"  Installing twine...", fg='cyan'))
        install_result = subprocess.run(
            [python_bin, '-m', 'pip', 'install', '--quiet', 'twine'],
            capture_output=True, text=True,
            cwd=str(Path('.'))
        )
        if install_result.returncode != 0:
            click.echo(click.style(f"  ✗ Failed to install twine: {install_result.stderr}", fg='red'))
            return False
        click.echo(click.style(f"  ✓ twine installed", fg='green'))

    return True


def _prepare_python_publish(strategy: dict) -> tuple:
    """Build the Python project and return (publish_cmd, ok). Returns ('', False) on failure."""
    python_bin = _get_python_bin()
    click.echo(click.style(f"  Using Python: {python_bin}", fg='cyan'))
    if not _ensure_publish_deps(python_bin):
        return '', False

    build_cmd = strategy.get('build', '') or 'python -m build'
    if build_cmd:
        build_cmd = build_cmd.replace('python ', f'{python_bin} ')
        click.echo(click.style(f"  Build command: {build_cmd}", fg='cyan'))
        build_result = run_command_tee(build_cmd)
        if build_result.returncode != 0:
            click.echo(click.style(f"  Build failed with exit code {build_result.returncode}", fg='red'), err=True)
            if build_result.stderr:
                click.echo(click.style(f"  stderr: {build_result.stderr}", fg='red'), err=True)
            if build_result.stdout:
                click.echo(click.style(f"  stdout: {build_result.stdout}", fg='yellow'), err=True)
            return '', False

    return python_bin, True


_RETRY_DELAYS = [60, 120, 300]


def _is_rate_limited(result) -> bool:
    """Check if a publish result indicates PyPI rate limiting (HTTP 429)."""
    combined = f"{result.stdout or ''}\n{result.stderr or ''}"
    return "429" in combined and "Too Many Requests" in combined


def _run_publish_command(ptype: str, publish_cmd: str) -> bool:
    """Execute the publish command and handle output. Returns True on success.

    Retries automatically when PyPI returns HTTP 429 (Too Many Requests),
    waiting between attempts with increasing backoff.
    """
    click.echo(f"  Publishing {ptype}: {publish_cmd}")
    attempts = 1 + len(_RETRY_DELAYS)  # first try + retries
    for attempt in range(attempts):
        try:
            result = run_command_tee(publish_cmd)
            if result.returncode == 0:
                click.echo(click.style(f"  ✓ Published {ptype} successfully", fg='green'))
                return True
            combined_output = f"{result.stdout or ''}\n{result.stderr or ''}"
            if "File already exists" in combined_output:
                click.echo(click.style("  ⚠  Artifact already exists on registry; skipping upload.", fg='yellow'))
                return True  # Not a failure
            if _is_rate_limited(result) and attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                click.echo(click.style(
                    f"  ⏳ PyPI rate limit (429). Retrying in {delay}s "
                    f"(attempt {attempt + 2}/{attempts})...",
                    fg='yellow',
                ))
                time.sleep(delay)
                continue
            click.echo(click.style(f"  Publish failed with exit code {result.returncode}", fg='red'), err=True)
            if result.stderr:
                click.echo(click.style(f"  stderr: {result.stderr}", fg='red'), err=True)
            if result.stdout:
                click.echo(click.style(f"  stdout: {result.stdout}", fg='yellow'), err=True)
            return False
        except Exception as e:
            click.echo(click.style(f"  Publish exception: {e}", fg='red'), err=True)
            return False
    click.echo(click.style(
        f"  ✗ Publish failed after {attempts} attempts due to PyPI rate limiting.",
        fg='red',
    ), err=True)
    return False


def publish_project(
    project_types: List[str],
    version: str,
    yes: bool = False,
    config: Any = None,
) -> bool:
    """Publish project to appropriate package registries."""
    all_valid, errors = validate_project_toml_files()
    if not all_valid:
        for error in errors:
            click.echo(click.style(error, fg='red', bold=True), err=True)
        click.echo(click.style("\nFix the TOML syntax error(s) before publishing.", fg='yellow'), err=True)
        return False

    success = True
    configured_project_types = _get_configured_project_types(config)

    for ptype in project_types:
        strategy = _get_project_strategy(config, ptype)
        if strategy.get('publish_enabled') is False:
            click.echo(click.style(f"  Skipping {ptype} publish (disabled in config)", fg='yellow'))
            continue

        if ptype == 'nodejs' and 'nodejs' not in configured_project_types:
            click.echo(click.style(
                "  Skipping nodejs publish (npm publish not configured for this project)",
                fg='yellow'
            ))
            continue

        publish_cmd = strategy.get('publish', '') or PROJECT_TYPES.get(ptype, {}).get('publish_command', '')
        if not publish_cmd:
            continue

        if ptype == 'python':
            python_bin, ok = _prepare_python_publish(strategy)
            if not ok:
                success = False
                continue
            publish_cmd = publish_cmd.replace('python ', f'{python_bin} ')
            click.echo(click.style(f"  Command: {publish_cmd}", fg='cyan'))

        if '{version}' in publish_cmd:
            publish_cmd = publish_cmd.replace('{version}', version)

        if not _run_publish_command(ptype, publish_cmd):
            success = False

    return success


__all__ = [
    'makefile_has_target',
    'publish_project',
]
