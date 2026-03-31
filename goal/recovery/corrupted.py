"""Corrupted git objects recovery strategy."""

import re
import subprocess
import click

from .base import RecoveryStrategy


class CorruptedObjectStrategy(RecoveryStrategy):
    """Handles corrupted git objects."""
    
    def can_handle(self, error_output: str) -> bool:
        """Check if error is related to corrupted objects."""
        patterns = [
            r'corrupted',
            r'bad object',
            r'invalid object',
            r'object.*corrupt',
            r'loose object.*invalid',
            r'packfile.*invalid'
        ]
        return any(re.search(pattern, error_output, re.IGNORECASE) for pattern in patterns)
    
    def recover(self, error_output: str) -> bool:
        """Attempt to recover from corrupted objects."""
        click.echo(click.style("\n💥 Corrupted git objects detected", fg='yellow', bold=True))
        
        # Try to repair the repository
        repairs = [
            ("Checking repository integrity", ['git', 'fsck', '--full']),
            ("Removing corrupted loose objects", ['git', 'prune', '--now']),
            ("Repacking objects", ['git', 'repack', '-a', '-d']),
            ("Garbage collection", ['git', 'gc', '--aggressive', '--prune=now']),
        ]
        
        for desc, cmd in repairs:
            click.echo(f"{desc}...")
            try:
                subprocess.run(cmd, cwd=self.repo_path, check=True, capture_output=True)
                click.echo(f"✓ {desc} completed")
            except subprocess.CalledProcessError as e:
                click.echo(f"⚠ {desc} failed: {e}")
        
        # Test if repository is fixed
        try:
            self.run_git('status')
            click.echo(click.style("✓ Repository appears to be repaired", fg='green'))
            return True
        except:
            click.echo(click.style("❌ Repository still corrupted", fg='red'))
            click.echo("You may need to clone the repository again")
            return False
