"""Authors command for managing project authors."""

import click
from typing import Dict, Optional

from goal.cli import main
from goal.authors import AuthorsManager


def display_author_details(identifier: str, author: Optional[Dict[str, str]]) -> None:
    """Display details of a found author or indicate not found."""
    if author:
        click.echo()
        click.echo(click.style("Author Found:", fg='green', bold=True))
        click.echo(f"  Name: {author.get('name', 'Unknown')}")
        click.echo(f"  Email: {author.get('email', 'Unknown')}")
        if author.get('role'):
            click.echo(f"  Role: {author.get('role')}")
        if author.get('alias'):
            click.echo(f"  Alias: {author.get('alias')}")
    else:
        click.echo(click.style(f"Author '{identifier}' not found", fg='red'))


def display_current_author(current: Dict[str, str]) -> None:
    """Display current author's information."""
    click.echo()
    click.echo(click.style("Current Author:", fg='cyan', bold=True))
    click.echo(f"  Name: {current['name']}")
    click.echo(f"  Email: {current['email']}")


@main.group()
def authors() -> None:
    """Manage project authors and team members."""
    pass


@authors.command(name='list')
def authors_list() -> None:
    """List all project authors."""
    manager = AuthorsManager()
    manager.list_authors()


@authors.command(name='add')
@click.argument('name')
@click.argument('email')
@click.option('--role', '-r', help='Author role or title')
@click.option('--alias', '-a', help='Short alias for reference')
def authors_add(name, email, role, alias) -> None:
    """Add an author to the project."""
    manager = AuthorsManager()
    manager.add_author(name, email, role, alias)


@authors.command(name='remove')
@click.argument('email')
def authors_remove(email) -> None:
    """Remove an author from the project."""
    manager = AuthorsManager()
    manager.remove_author(email)


@authors.command(name='update')
@click.argument('email')
@click.option('--name', '-n', help='New name')
@click.option('--role', '-r', help='New role')
@click.option('--alias', '-a', help='New alias')
def authors_update(email, name, role, alias) -> None:
    """Update an author's information."""
    manager = AuthorsManager()
    manager.update_author(email, name, role, alias)


@authors.command(name='import')
def authors_import() -> None:
    """Import authors from git history."""
    manager = AuthorsManager()
    manager.import_from_git()


@authors.command(name='export')
def authors_export() -> None:
    """Export authors to CONTRIBUTORS.md."""
    manager = AuthorsManager()
    manager.export_to_contributors()


@authors.command(name='find')
@click.argument('identifier')
def authors_find(identifier) -> None:
    """Find an author by name, email, or alias."""
    manager = AuthorsManager()
    author = manager.find_author(identifier)
    display_author_details(identifier, author)


@authors.command(name='co-author')
@click.argument('name')
@click.argument('email')
def authors_co_author(name, email):
    """Generate a co-author trailer for commit messages."""
    trailer = format_co_author_trailer(name, email)
    click.echo(trailer)


@authors.command(name='current')
def authors_current():
    """Show current user's author information."""
    manager = AuthorsManager()
    current = manager.get_current_author()
    display_current_author(current)


__all__ = [
    'authors',
    'authors_list',
    'authors_add',
    'authors_remove',
    'authors_update',
    'authors_import',
    'authors_export',
    'authors_find',
    'authors_co_author',
    'authors_current',
]