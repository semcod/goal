"""Recovery command for Goal CLI."""

import os
import sys
from typing import Optional
import click

from ..recovery import RecoveryManager
from ..git_ops import run_git


@click.command()
@click.option(
    '--full', '-f',
    is_flag=True,
    help='Run full recovery workflow using clean clone method'
)
@click.option(
    '--error-file', '-e',
    type=click.Path(exists=True),
    help='Read error from file instead of last git push output'
)
@click.option(
    '--error-message', '-m',
    help='Provide error message directly'
)
@click.option(
    '--no-backup',
    is_flag=True,
    help='Skip creating backup branch (not recommended)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed recovery steps'
)
@click.pass_context
def recover(ctx, full, error_file, error_message, no_backup, verbose):
    """Recover from git push failures.
    
    This command automatically detects and attempts to recover from common
    git push failures including:
    
    - Authentication errors (invalid/expired tokens)
    - Large files exceeding GitHub limits
    - Divergent history conflicts
    - Corrupted git objects
    - Git LFS issues
    - Protected branch force push requirements
    
    Examples:
        
        # Recover from last failed push
        goal recover
        
        # Run full recovery workflow
        goal recover --full
        
        # Provide specific error message
        goal recover -m "Updates were rejected because the tip of your current branch is behind"
        
        # Read error from file
        goal recover -e push-error.log
    """
    ctx_obj = ctx.obj or {}
    
    # Get repository path
    repo_path = os.getcwd()
    
    # Get error output
    error_output = _get_error_output(error_file, error_message)
    
    if not error_output:
        click.echo(click.style("No error output found. Run 'git push' to see the error.", fg='yellow'))
        return
    
    if verbose:
        click.echo(f"\nRepository: {repo_path}")
        click.echo(f"Error output:\n{error_output}\n")
    
    # Create recovery manager
    config = ctx_obj.get('config')
    manager = RecoveryManager(repo_path, config)
    
    # Run recovery
    if full:
        # Full recovery workflow
        success = manager.full_recovery_workflow()
    else:
        # Standard recovery based on error
        success = manager.recover_from_push_failure(error_output)
    
    # Report result
    if success:
        click.echo(click.style("\n🎉 Recovery completed successfully!", fg='green', bold=True))
        sys.exit(0)
    else:
        click.echo(click.style("\n❌ Recovery failed. Manual intervention may be required.", fg='red', bold=True))
        sys.exit(1)


def _get_error_output(error_file: Optional[str], error_message: Optional[str]) -> Optional[str]:
    """Get error output from various sources."""
    if error_message:
        return error_message
    
    if error_file:
        try:
            with open(error_file, 'r') as f:
                return f.read()
        except Exception as e:
            click.echo(click.style(f"Failed to read error file: {e}", fg='red'))
            return None
    
    # Try to get from last git push command
    try:
        # Check if there's a recent push error in terminal history
        # This is a simplified approach - in a real implementation,
        # we might need to integrate with the shell history
        return None
    except:
        return None


# Register the command - imported in goal.cli.__init__
