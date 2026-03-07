"""Push workflow stages - tag creation."""

from typing import Optional

import click

try:
    from ...git_ops import run_git
except ImportError:
    from goal.git_ops import run_git


def create_tag(new_version: str, no_tag: bool) -> Optional[str]:
    """Create git tag for release."""
    if no_tag:
        return None
    
    tag_name = f"v{new_version}"
    tag_exists = run_git('rev-parse', '-q', '--verify', f"refs/tags/{tag_name}")
    
    if tag_exists.returncode == 0:
        click.echo(click.style(f"Warning: Tag already exists: {tag_name}", fg='yellow'))
        return None
    
    result = run_git('tag', '-a', tag_name, '-m', f"Release {new_version}")
    if result.returncode != 0:
        click.echo(click.style(f"⚠ Warning: Could not create tag: {result.stderr}", fg='yellow'))
        return None
    
    click.echo(click.style(f"✓ Created tag: {tag_name}", fg='green'))
    return tag_name
