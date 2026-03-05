"""Publish command - extracted from cli.py."""

import click
import shutil
from pathlib import Path

try:
    from ..git_ops import run_command_tee
    from . import main
    from .version import get_current_version, detect_project_types
    from .publish import makefile_has_target, publish_project
except ImportError:
    from goal.git_ops import run_command_tee
    from goal.cli import main
    from goal.cli.version import get_current_version, detect_project_types
    from goal.cli.publish import makefile_has_target, publish_project


@main.command()
@click.option('--make/--no-make', 'use_make', default=True, help='Use Makefile publish target if available')
@click.option('--target', default='publish', help='Make target to run when using --make')
@click.option('--version', 'version_arg', default=None, help='Version to publish when not using Makefile')
@click.pass_context
def publish(ctx, use_make, target, version_arg):
    """Publish the current project (optionally using Makefile)."""
    project_types = detect_project_types()

    if use_make and shutil.which('make') and makefile_has_target(target):
        cmd = f"make {target}"
        click.echo(f"\n{click.style('Publishing:', fg='cyan', bold=True)} {cmd}")
        result = run_command_tee(cmd)
        if result.returncode != 0:
            import sys
            sys.exit(result.returncode)
        return

    if version_arg is None:
        version_arg = get_current_version()

    if not publish_project(project_types, version_arg, False):
        click.echo(click.style("Publish failed. Continuing.", fg='yellow'))


__all__ = ['publish']
