"""Divergent history recovery strategy."""

import re
import click

from .base import RecoveryStrategy


class DivergentHistoryStrategy(RecoveryStrategy):
    """Handles divergent history errors."""
    
    def can_handle(self, error_output: str) -> bool:
        """Check if error is related to divergent history."""
        patterns = [
            r'non-fast-forward',
            r'divergent branches',
            r'fetch first',
            r'behind.*tip',
            r'updates were rejected',
            r'pull before you push',
            r'failed to push some refs',
            r'rejected.*push'
        ]
        return any(re.search(pattern, error_output, re.IGNORECASE) for pattern in patterns)
    
    def recover(self, error_output: str) -> bool:
        """Attempt to recover from divergent history."""
        click.echo(click.style("\n🌿 Divergent history detected", fg='yellow', bold=True))
        
        # Fetch latest changes
        try:
            click.echo("Fetching latest changes from remote...")
            self.run_git('fetch', 'origin')
            click.echo("✓ Fetch completed")
        except Exception as e:
            click.echo(click.style(f"✗ Failed to fetch: {e}", fg='red'))
            return False
        
        # Get current branch
        current_branch = self.run_git_with_output('branch', '--show-current')
        
        # Check if we have commits that remote doesn't have
        try:
            ahead_count = self.run_git_with_output('rev-list', '--count', f'origin/{current_branch}..HEAD')
            behind_count = self.run_git_with_output('rev-list', '--count', f'HEAD..origin/{current_branch}')
        except:
            click.echo(click.style("❌ Could not determine branch status", fg='red'))
            return False
        
        click.echo(f"Branch status: {ahead_count} ahead, {behind_count} behind")
        
        if int(ahead_count) > 0 and int(behind_count) > 0:
            # Both have diverged - need to rebase
            click.echo("\nRecovery options:")
            click.echo("1. Rebase your changes on top of remote (recommended)")
            click.echo("2. Merge remote changes")
            click.echo("3. Force push (not recommended)")
            
            choice = click.prompt("Choose option [1/2/3]", type=int, default=1)
            
            if choice == 1:
                return self._rebase_changes(current_branch)
            elif choice == 2:
                return self._merge_changes(current_branch)
            elif choice == 3:
                return self._force_push()
        
        elif int(behind_count) > 0:
            # Just need to pull
            return self._pull_changes()
        
        return False
    
    def _rebase_changes(self, branch: str) -> bool:
        """Rebase changes on top of remote."""
        try:
            click.echo("Rebasing changes...")
            self.run_git('rebase', f'origin/{branch}')
            click.echo(click.style("✓ Rebase successful", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Rebase failed: {e}", fg='red'))
            click.echo("You may need to resolve conflicts manually")
            return False
    
    def _merge_changes(self, branch: str) -> bool:
        """Merge remote changes."""
        try:
            click.echo("Merging remote changes...")
            self.run_git('merge', f'origin/{branch}')
            click.echo(click.style("✓ Merge successful", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Merge failed: {e}", fg='red'))
            click.echo("You may need to resolve conflicts manually")
            return False
    
    def _pull_changes(self) -> bool:
        """Pull changes from remote."""
        try:
            click.echo("Pulling changes...")
            self.run_git('pull', '--rebase')
            click.echo(click.style("✓ Pull successful", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Pull failed: {e}", fg='red'))
            return False
    
    def _force_push(self) -> bool:
        """Force push to remote."""
        if click.confirm(click.style("Force push may overwrite remote changes. Continue?", fg='red')):
            try:
                self.run_git('push', '--force-with-lease')
                click.echo(click.style("✓ Force push successful", fg='green'))
                return True
            except Exception as e:
                click.echo(click.style(f"✗ Force push failed: {e}", fg='red'))
                return False
        return False
