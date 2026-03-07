"""Push workflow CLI commands."""

import click
from typing import Any

try:
    from ..cli import main, confirm, apply_ticket_prefix, stage_paths, split_paths_by_type
    from .core import execute_push_workflow
except ImportError:
    from goal.cli import main, confirm, apply_ticket_prefix, stage_paths, split_paths_by_type
    from goal.push.core import execute_push_workflow


@main.command()
@click.option('--bump', default='patch', help='Version bump type (major, minor, patch)')
@click.option('--no-tag', is_flag=True, help='Skip creating git tag')
@click.option('--no-changelog', is_flag=True, help='Skip updating CHANGELOG.md')
@click.option('--no-version-sync', is_flag=True, help='Skip syncing version to all files')
@click.option('--message', '-m', default=None, help='Custom commit message')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all prompts')
@click.option('--markdown/--ascii', default=False, help='Output format')
@click.option('--split', is_flag=True, help='Split commits by file type')
@click.option('--ticket', default=None, help='Ticket ID for commit prefix')
@click.option('--abstraction', default=None, help='Abstraction level for commit message')
@click.option('--todo', '-t', is_flag=True, help='Create TODO.md with detected issues')
@click.pass_context
def push(ctx, bump, no_tag, no_changelog, no_version_sync, message, dry_run, yes, 
         markdown, split, ticket, abstraction, todo):
    """Add, commit, tag, and push changes to remote."""
    execute_push_workflow(
        ctx_obj=ctx.obj,
        bump=bump,
        no_tag=no_tag,
        no_changelog=no_changelog,
        no_version_sync=no_version_sync,
        message=message,
        dry_run=dry_run,
        yes=yes,
        markdown=markdown,
        split=split,
        ticket=ticket,
        abstraction=abstraction,
        todo=todo
    )
