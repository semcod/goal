"""Author management for multi-author projects."""

from typing import Dict, List, Optional, Any
from pathlib import Path

import click

from goal.config import ensure_config
from goal.user_config import UserConfig


class AuthorsManager:
    """Manages project authors and team members."""

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize authors manager.

        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.config = ensure_config()

    def get_authors(self) -> List[Dict[str, Any]]:
        """Get list of project authors.

        Returns:
            List of author dictionaries with name, email, role, etc.
        """
        authors = self.config.get("authors", [])

        # Ensure it's a list
        if not isinstance(authors, list):
            authors = []

        return authors

    def add_author(
        self,
        name: str,
        email: str,
        role: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> bool:
        """Add an author to the project.

        Args:
            name: Author's full name
            email: Author's email
            role: Author's role (optional)
            alias: Short alias for quick reference (optional)

        Returns:
            True if author was added
        """
        authors = self.get_authors()

        # Check if author already exists
        for author in authors:
            if author.get("email", "").lower() == email.lower():
                click.echo(
                    click.style(
                        f"⚠ Author with email {email} already exists", fg="yellow"
                    )
                )
                return False

        # Create new author
        new_author = {
            "name": name,
            "email": email,
        }

        if role:
            new_author["role"] = role

        if alias:
            new_author["alias"] = alias
        else:
            # Generate alias from name
            alias = name.lower().replace(" ", ".")
            new_author["alias"] = alias

        authors.append(new_author)

        # Save to config
        self.config.set("authors", authors)
        self.config.save()

        click.echo(click.style(f"✓ Added author: {name} <{email}>", fg="green"))
        return True

    def remove_author(self, email: str) -> bool:
        """Remove an author from the project.

        Args:
            email: Author's email to remove

        Returns:
            True if author was removed
        """
        authors = self.get_authors()

        # Find and remove author
        for i, author in enumerate(authors):
            if author.get("email", "").lower() == email.lower():
                removed = authors.pop(i)
                self.config.set("authors", authors)
                self.config.save()

                click.echo(
                    click.style(
                        f"✓ Removed author: {removed.get('name')} <{removed.get('email')}>",
                        fg="green",
                    )
                )
                return True

        click.echo(click.style(f"✗ Author with email {email} not found", fg="red"))
        return False

    def update_author(
        self,
        email: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> bool:
        """Update an author's information.

        Args:
            email: Author's email
            name: New name (optional)
            role: New role (optional)
            alias: New alias (optional)

        Returns:
            True if author was updated
        """
        authors = self.get_authors()

        # Find author
        for author in authors:
            if author.get("email", "").lower() == email.lower():
                if name:
                    author["name"] = name
                if role:
                    author["role"] = role
                if alias:
                    author["alias"] = alias

                self.config.set("authors", authors)
                self.config.save()

                click.echo(
                    click.style(
                        f"✓ Updated author: {author['name']} <{author['email']}>",
                        fg="green",
                    )
                )
                return True

        click.echo(click.style(f"✗ Author with email {email} not found", fg="red"))
        return False

    def find_author(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find an author by email, name, or alias.

        Args:
            identifier: Email, name, or alias

        Returns:
            Author dictionary or None if not found
        """
        authors = self.get_authors()
        identifier = identifier.lower()

        for author in authors:
            # Check email
            if author.get("email", "").lower() == identifier:
                return author

            # Check name
            if author.get("name", "").lower() == identifier:
                return author

            # Check alias
            if author.get("alias", "").lower() == identifier:
                return author

        return None

    def list_authors(self) -> None:
        """List all project authors."""
        authors = self.get_authors()

        if not authors:
            click.echo(
                click.style("No authors configured for this project", fg="yellow")
            )
            click.echo("Use 'goal authors add' to add authors")
            return

        click.echo()
        click.echo(click.style("Project Authors:", fg="cyan", bold=True))
        click.echo("-" * 40)

        # Get current user
        user_config = UserConfig()
        current_email = user_config.get("author_email", "").lower()

        for author in authors:
            is_current = author.get("email", "").lower() == current_email

            name = author.get("name", "Unknown")
            email = author.get("email", "unknown@example.com")
            role = author.get("role", "")
            alias = author.get("alias", "")

            # Format output
            line = f"  {click.style(name, fg='green' if is_current else 'white')} <{email}>"
            if alias:
                line += f" ({click.style(alias, fg='cyan')})"
            if role:
                line += f" - {role}"
            if is_current:
                line += " " + click.style("[you]", fg="yellow", bold=True)

            click.echo(line)

    def get_current_author(self) -> Dict[str, str]:
        """Get the current user's author information.

        Returns:
            Dictionary with name and email
        """
        user_config = UserConfig()

        return {
            "name": user_config.get("author_name", "Unknown Author"),
            "email": user_config.get("author_email", "unknown@example.com"),
        }

    def import_from_git(self) -> int:
        """Import authors from git history.

        Returns:
            Number of new authors added
        """
        import subprocess

        # Get all commit authors
        result = subprocess.run(
            ["git", "log", "--format=%an|%ae"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse authors
        git_authors = set()
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                name, email = line.split("|", 1)
                git_authors.add((name.strip(), email.strip()))

        # Add new authors
        added = 0
        for name, email in git_authors:
            if not self.find_author(email):
                self.add_author(name, email, role="Contributor")
                added += 1

        if added > 0:
            click.echo(
                click.style(f"✓ Imported {added} authors from git history", fg="green")
            )
        else:
            click.echo(click.style("No new authors found in git history", fg="yellow"))

        return added

    def export_to_contributors(self) -> None:
        """Export authors to CONTRIBUTORS.md file."""
        authors = self.get_authors()

        if not authors:
            click.echo(click.style("No authors to export", fg="yellow"))
            return

        # Create CONTRIBUTORS.md
        content = "# Contributors\n\n"
        content += "This project exists thanks to all the people who contribute:\n\n"

        # Sort by name
        authors_sorted = sorted(authors, key=lambda a: a.get("name", "").lower())

        for author in authors_sorted:
            name = author.get("name", "Unknown")
            email = author.get("email", "")
            role = author.get("role", "Contributor")

            content += f"- **{name}**"
            if email:
                content += f" <{email}>"
            content += f" - {role}\n"

        # Write file
        contributors_file = self.project_dir / "CONTRIBUTORS.md"
        contributors_file.write_text(content, encoding="utf-8")

        click.echo(click.style("✓ Exported authors to CONTRIBUTORS.md", fg="green"))


def get_project_authors(project_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Get all authors for a project.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        List of author dictionaries
    """
    manager = AuthorsManager(project_dir)
    return manager.get_authors()


def add_project_author(
    name: str,
    email: str,
    role: Optional[str] = None,
    alias: Optional[str] = None,
    project_dir: Optional[Path] = None,
) -> bool:
    """Add an author to a project.

    Args:
        name: Author's full name
        email: Author's email
        role: Author's role (optional)
        alias: Short alias (optional)
        project_dir: Project directory (defaults to current directory)

    Returns:
        True if author was added
    """
    manager = AuthorsManager(project_dir)
    return manager.add_author(name, email, role, alias)
