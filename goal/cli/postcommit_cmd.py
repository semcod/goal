"""Post-commit command for managing post-commit actions."""

import click

from goal.cli import main
from goal.postcommit import PostCommitManager


@main.group()
def postcommit() -> None:
    """Manage post-commit actions."""
    pass


@postcommit.command(name="run")
def postcommit_run() -> None:
    """Run configured post-commit actions."""
    manager = PostCommitManager()
    if manager.run_actions():
        click.echo()
        click.echo(click.style("✓ All post-commit actions completed", fg="green"))
    else:
        click.echo()
        click.echo(click.style("⚠ Some post-commit actions failed", fg="yellow"))


@postcommit.command(name="list")
def postcommit_list() -> None:
    """List configured post-commit actions."""
    manager = PostCommitManager()
    manager.list_actions()


@postcommit.command(name="validate")
def postcommit_validate() -> None:
    """Validate post-commit action configuration."""
    manager = PostCommitManager()
    click.echo()
    click.echo(click.style("Validating post-commit actions...", fg="cyan"))
    if manager.validate_actions():
        click.echo()
        click.echo(click.style("✓ All actions are valid", fg="green"))
    else:
        click.echo()
        click.echo(click.style("✗ Some actions have configuration errors", fg="red"))


@postcommit.command(name="info")
def postcommit_info() -> None:
    """Show information about available actions."""
    from goal.postcommit import AVAILABLE_ACTIONS

    click.echo()
    click.echo(click.style("Available Post-Commit Actions:", fg="cyan", bold=True))
    click.echo("-" * 40)

    for name, action_class in AVAILABLE_ACTIONS.items():
        action = action_class({})
        click.echo()
        click.echo(click.style(f"• {name}", fg="green"))

        if name == "notification":
            click.echo("  Send desktop notification")
            click.echo("  Config: title, message")
        elif name == "webhook":
            click.echo("  Send HTTP POST request")
            click.echo("  Config: url, headers (optional)")
        elif name == "script":
            click.echo("  Run custom shell script")
            click.echo("  Config: command, working_dir (optional), timeout (optional)")
        elif name == "git_push":
            click.echo("  Automatically push to remote")
            click.echo("  Config: remote (default: origin)")


__all__ = [
    "postcommit",
    "postcommit_run",
    "postcommit_list",
    "postcommit_validate",
    "postcommit_info",
]
