"""Git LFS issue recovery strategy."""

import re
import subprocess
import click

from .base import RecoveryStrategy


class LFSIssueStrategy(RecoveryStrategy):
    """Handles Git LFS issues."""
    
    def can_handle(self, error_output: str) -> bool:
        """Check if error is related to LFS."""
        patterns = [
            r'lfs',
            r'pointer file',
            r'filter.*lfs',
            r'smudge.*lfs',
            r'clean.*lfs'
        ]
        return any(re.search(pattern, error_output, re.IGNORECASE) for pattern in patterns)
    
    def recover(self, error_output: str) -> bool:
        """Attempt to recover from LFS issues."""
        click.echo(click.style("\n📦 Git LFS issue detected", fg='yellow', bold=True))
        
        # Check if LFS is installed
        try:
            subprocess.run(['git', 'lfs', 'version'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            click.echo(click.style("❌ Git LFS is not installed", fg='red'))
            if click.confirm("Install Git LFS?"):
                try:
                    subprocess.run(['git', 'lfs', 'install'], check=True)
                    click.echo(click.style("✓ Git LFS installed", fg='green'))
                except:
                    click.echo(click.style("❌ Failed to install Git LFS", fg='red'))
                    return False
            else:
                return False
        
        # Reinstall LFS hooks
        try:
            self.run_git('lfs', 'install', '--force')
            click.echo("✓ LFS hooks reinstalled")
        except Exception as e:
            click.echo(click.style(f"✗ Failed to reinstall LFS hooks: {e}", fg='red'))
        
        # Pull LFS files
        try:
            self.run_git('lfs', 'pull')
            click.echo("✓ LFS files pulled")
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Failed to pull LFS files: {e}", fg='red'))
            return False
