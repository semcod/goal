"""Force push recovery strategy."""

import re
import click

from .base import RecoveryStrategy


class ForcePushStrategy(RecoveryStrategy):
    """Handles force push recovery scenarios."""

    def can_handle(self, error_output: str) -> bool:
        """Check if error requires force push."""
        patterns = [
            r"protected branch",
            r"force push",
            r"push --force",
            r"update --force",
        ]
        return any(
            re.search(pattern, error_output, re.IGNORECASE) for pattern in patterns
        )

    def recover(self, error_output: str) -> bool:
        """Attempt to recover with force push."""
        click.echo(
            click.style("\n💪 Force push may be required", fg="yellow", bold=True)
        )

        if click.confirm(
            click.style("Force push may overwrite remote changes. Continue?", fg="red")
        ):
            try:
                # Use force-with-lease for safety
                self.run_git("push", "--force-with-lease")
                click.echo(click.style("✓ Force push successful", fg="green"))
                return True
            except Exception as e:
                click.echo(click.style(f"✗ Force push failed: {e}", fg="red"))

                # Try with regular force as last resort
                if click.confirm("Try with regular force push?"):
                    try:
                        self.run_git("push", "--force")
                        click.echo(click.style("✓ Force push successful", fg="green"))
                        return True
                    except Exception as e2:
                        click.echo(click.style(f"✗ Force push failed: {e2}", fg="red"))
                        return False

        return False
