"""Push workflow stages - remote push."""

import sys
from typing import Optional

import click

try:
    from ...git_ops import run_git, ensure_remote, get_remote_branch, _echo_cmd
    from ....cli import confirm
except ImportError:
    from goal.git_ops import run_git, ensure_remote, get_remote_branch, _echo_cmd
    from goal.cli import confirm


def push_to_remote(
    branch: str,
    tag_name: Optional[str],
    no_tag: bool,
    yes: bool
) -> bool:
    """Push commits and tags to remote."""
    has_remote = ensure_remote(auto=yes)
    
    if not has_remote:
        click.echo(click.style("  ℹ  No remote configured — commit saved locally.", fg='yellow'))
        return False
    
    if not yes:
        if not confirm("Push to remote?"):
            click.echo(click.style("  Skipping push (user chose N).", fg='yellow'))
            return False
    
    if not yes:
        click.echo(click.style("Pushing to remote...", fg='cyan'))
    else:
        click.echo(click.style("🤖 AUTO: Pushing to remote (--all mode)", fg='cyan'))
    
    try:
        _echo_cmd(['git', 'push', 'origin', branch])
        result = run_git('push', 'origin', branch, capture=False)
        if result.returncode != 0:
            click.echo(click.style(f"✗ Push failed (exit {result.returncode}). Check remote access.", fg='red'))
            if not yes:
                sys.exit(1)
            return False
        
        if tag_name and not no_tag:
            _echo_cmd(['git', 'push', 'origin', tag_name])
            result = run_git('push', 'origin', tag_name, capture=False)
            if result.returncode != 0:
                click.echo(click.style(f"⚠  Could not push tag {tag_name}.", fg='yellow'))
        
        click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
        return True
    except Exception as e:
        click.echo(click.style(f"✗ Push error: {e}", fg='red'))
        if not yes:
            sys.exit(1)
        return False
