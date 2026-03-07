"""Push workflow stages - changelog handling."""

import click

from goal.changelog import update_changelog as _update_changelog


def handle_changelog(
    new_version: str,
    files: list,
    commit_msg: str,
    config: dict,
    no_changelog: bool
) -> None:
    """Update changelog."""
    if not no_changelog:
        _update_changelog(new_version, files, commit_msg, config=config)
        from goal.push.core import run_git_local
        run_git_local('add', 'CHANGELOG.md')
        click.echo(click.style(f"✓ Updated CHANGELOG.md", fg='green'))


def update_changelog_stage(
    new_version: str,
    files: list,
    commit_msg: str,
    config: dict
) -> None:
    """Stage for updating changelog without git add."""
    _update_changelog(new_version, files, commit_msg, config=config)
