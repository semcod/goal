"""Push workflow stages - publishing."""

import click

try:
    from ....cli.publish import publish_project
    from ....cli import confirm
except ImportError:
    from goal.cli.publish import publish_project
    from goal.cli import confirm


def handle_publish(
    project_types: list,
    new_version: str,
    yes: bool
) -> bool:
    """Publish to package registries."""
    if not yes:
        if not confirm(f"Publish version {new_version}?"):
            click.echo(click.style("  🤖 AUTO: Skipping publish (user chose N)", fg='yellow'))
            return False
    else:
        click.echo(click.style(f"\n🤖 AUTO: Publishing version {new_version} (--all mode)", fg='cyan'))
    
    try:
        publish_success = publish_project(project_types, new_version, yes)
        if publish_success:
            click.echo(click.style(f"\n✓ Published version {new_version}", fg='green', bold=True))
        else:
            click.echo(click.style("⚠ Publish failed. Continuing with remaining tasks.", fg='yellow'))
        return publish_success
    except Exception as e:
        click.echo(click.style(f"⚠ Publish error: {str(e)}. Continuing...", fg='yellow'))
        return False
