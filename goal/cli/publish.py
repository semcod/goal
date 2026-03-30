"""Publishing functions - extracted from cli.py."""

import subprocess
from pathlib import Path
from typing import Any, List

import click

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


def publish_project(
    project_types: List[str],
    version: str,
    yes: bool = False,
    config: Any = None,
) -> bool:
    """Publish project to appropriate package registries."""
    # Early TOML validation for clear error messages
    all_valid, errors = validate_project_toml_files()
    if not all_valid:
        for error in errors:
            click.echo(click.style(error, fg='red', bold=True), err=True)
        click.echo(click.style("\nFix the TOML syntax error(s) before publishing.", fg='yellow'), err=True)
        return False
    
    success = True

    for ptype in project_types:
        strategy = _get_project_strategy(config, ptype)
        if strategy.get('publish_enabled') is False:
            click.echo(click.style(f"  Skipping {ptype} publish (disabled in config)", fg='yellow'))
            continue

        publish_cmd = strategy.get('publish', '') or PROJECT_TYPES.get(ptype, {}).get('publish_command', '')

        if not publish_cmd:
            continue

        # Handle Python projects specially to ensure deps are available
        if ptype == 'python':
            python_bin = _get_python_bin()
            click.echo(click.style(f"  Using Python: {python_bin}", fg='cyan'))
            if not _ensure_publish_deps(python_bin):
                success = False
                continue

            build_cmd = strategy.get('build', '') or 'python -m build'
            if build_cmd:
                build_cmd = build_cmd.replace('python ', f'{python_bin} ')
                click.echo(click.style(f"  Build command: {build_cmd}", fg='cyan'))
                build_result = run_command_tee(build_cmd)
                if build_result.returncode != 0:
                    click.echo(click.style(
                        f"  Build failed with exit code {build_result.returncode}",
                        fg='red'
                    ), err=True)
                    if build_result.stderr:
                        click.echo(click.style(f"  stderr: {build_result.stderr}", fg='red'), err=True)
                    if build_result.stdout:
                        click.echo(click.style(f"  stdout: {build_result.stdout}", fg='yellow'), err=True)
                    success = False
                    continue

            # Replace 'python' with the actual Python path in the command
            publish_cmd = publish_cmd.replace('python ', f'{python_bin} ')
            click.echo(click.style(f"  Command: {publish_cmd}", fg='cyan'))

        # Skip if dry-run would be triggered
        if '{version}' in publish_cmd:
            publish_cmd = publish_cmd.replace('{version}', version)

        click.echo(f"  Publishing {ptype}: {publish_cmd}")

        try:
            # Use run_command_tee to show output in real-time
            result = run_command_tee(publish_cmd)
            if result.returncode != 0:
                already_exists_msg = "File already exists"
                combined_output = f"{result.stdout or ''}\n{result.stderr or ''}"
                if already_exists_msg in combined_output:
                    click.echo(click.style(
                        "  ⚠  Artifact already exists on registry; skipping upload.",
                        fg='yellow',
                    ))
                    continue
                click.echo(click.style(f"  Publish failed with exit code {result.returncode}", fg='red'), err=True)
                if result.stderr:
                    click.echo(click.style(f"  stderr: {result.stderr}", fg='red'), err=True)
                if result.stdout:
                    click.echo(click.style(f"  stdout: {result.stdout}", fg='yellow'), err=True)
                success = False
            else:
                click.echo(click.style(f"  ✓ Published {ptype} successfully", fg='green'))
        except Exception as e:
            click.echo(click.style(f"  Publish exception: {e}", fg='red'), err=True)
            success = False

    return success


__all__ = [
    'makefile_has_target',
    'publish_project',
]
