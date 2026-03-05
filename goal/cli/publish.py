"""Publishing functions - extracted from cli.py."""

import subprocess
import shutil
from pathlib import Path
from typing import List

import click

try:
    from ..git_ops import run_command_tee
    from .version import PROJECT_TYPES
except ImportError:
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


def publish_project(project_types: List[str], version: str, yes: bool = False) -> bool:
    """Publish project to appropriate package registries."""
    success = True
    
    for ptype in project_types:
        config = PROJECT_TYPES.get(ptype, {})
        publish_cmd = config.get('publish_command', '')
        
        if not publish_cmd:
            continue
        
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
