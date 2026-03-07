"""Publishing functions - extracted from cli.py."""

import subprocess
import shutil
from pathlib import Path
from typing import List

import click

from goal.git_ops import run_command_tee
from goal.cli.version import PROJECT_TYPES


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


def _get_python_bin() -> str:
    """Get the Python binary to use for publishing."""
    try:
        from goal.project_bootstrap import _find_python_bin
        return _find_python_bin(Path('.'))
    except ImportError:
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
            [python_bin, '-m', 'pip', 'install', 'build'],
            capture_output=True, text=True
        )
        if install_result.returncode != 0:
            click.echo(click.style(f"  ✗ Failed to install build module", fg='red'))
            return False

    # Check if twine is available
    result = subprocess.run(
        [python_bin, '-m', 'twine', '--help'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        click.echo(click.style(f"  Installing twine...", fg='cyan'))
        install_result = subprocess.run(
            [python_bin, '-m', 'pip', 'install', 'twine'],
            capture_output=True, text=True
        )
        if install_result.returncode != 0:
            click.echo(click.style(f"  ✗ Failed to install twine", fg='red'))
            return False

    return True


def publish_project(project_types: List[str], version: str, yes: bool = False) -> bool:
    """Publish project to appropriate package registries."""
    success = True

    for ptype in project_types:
        config = PROJECT_TYPES.get(ptype, {})
        publish_cmd = config.get('publish_command', '')

        if not publish_cmd:
            continue

        # Handle Python projects specially to ensure deps are available
        if ptype == 'python':
            python_bin = _get_python_bin()
            if not _ensure_publish_deps(python_bin):
                success = False
                continue
            # Replace 'python' with the actual Python path in the command
            publish_cmd = publish_cmd.replace('python ', f'{python_bin} ')

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
