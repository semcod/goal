"""Authentication error recovery strategy."""

import os
import re
import subprocess
import click

from .base import RecoveryStrategy


class AuthErrorStrategy(RecoveryStrategy):
    """Handles authentication errors."""

    def can_handle(self, error_output: str) -> bool:
        """Check if error is authentication related."""
        auth_patterns = [
            r"authentication failed",
            r"invalid credentials",
            r"invalid username or password",
            r"permission denied",
            r"401",
            r"403",
            r"support for password authentication was removed",
            r"could not read Username",
            r"fatal: Authentication failed",
        ]
        return any(
            re.search(pattern, error_output, re.IGNORECASE) for pattern in auth_patterns
        )

    def recover(self, error_output: str) -> bool:
        """Attempt to recover from authentication error."""
        click.echo(
            click.style("\n🔐 Authentication error detected", fg="yellow", bold=True)
        )
        click.echo("Attempting to recover...")

        # Try to check if we have a GitHub token
        if "GITHUB_TOKEN" in os.environ:
            click.echo("✓ Found GITHUB_TOKEN environment variable")
            # Update remote URL to use token
            try:
                remote_url = self.run_git_with_output("remote", "get-url", "origin")
                if "github.com" in remote_url:
                    # Convert to token-based URL
                    if remote_url.startswith("https://"):
                        token_url = remote_url.replace(
                            "https://", f"https://{os.environ['GITHUB_TOKEN']}@"
                        )
                        self.run_git("remote", "set-url", "origin", token_url)
                        click.echo("✓ Updated remote URL with token")
                        return True
            except Exception as e:
                click.echo(click.style(f"✗ Failed to update remote URL: {e}", fg="red"))

        # Try to use gh CLI authentication
        try:
            self.run_git("credential", "fill", check=False)
            result = self.run_git("ls-remote", "--heads", "origin", check=False)
            if result.returncode == 0:
                click.echo("✓ Git credentials are valid")
                return True
        except:
            pass

        # Check if gh CLI is available and authenticated
        try:
            subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
            click.echo("✓ GitHub CLI (gh) is authenticated")
            # Try to clone using gh
            return True
        except:
            pass

        click.echo(click.style("\n❌ Could not resolve authentication issue", fg="red"))
        click.echo("\nPossible solutions:")
        click.echo("1. Set GITHUB_TOKEN environment variable")
        click.echo("2. Run 'gh auth login' to authenticate with GitHub CLI")
        click.echo(
            "3. Update your git credentials with 'git config --global credential.helper store'"
        )

        return False
