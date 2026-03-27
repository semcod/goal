"""Push workflow stages - remote push."""

import sys
import os
from typing import Optional

import click

from goal.git_ops import run_git, ensure_remote, get_remote_branch, run_git_with_status, HAS_CLICKMD
from goal.cli import confirm

# Import clickmd if available
if HAS_CLICKMD:
    from clickmd import echo_md


def push_to_remote(
    branch: str,
    tag_name: Optional[str],
    no_tag: bool,
    yes: bool
) -> bool:
    """Push commits and tags to remote."""
    has_remote = ensure_remote(auto=yes)
    
    if not has_remote:
        click.echo(click.style("  ℹ  No remote configured — commit saved locally.", fg='yellow'))
        return False
    
    if not yes:
        if not confirm("Push to remote?"):
            click.echo(click.style("  Skipping push (user chose N).", fg='yellow'))
            return False
    
    try:
        # Show push operation header
        if not yes:
            if HAS_CLICKMD:
                echo_md("\n### 📤 Pushing to Remote Repository")
                echo_md(f"**Branch:** `{branch}`")
                echo_md(f"**Remote:** `origin`")
            else:
                click.echo(click.style("\n📤 Pushing to Remote Repository", fg='blue', bold=True))
                click.echo(f"Branch: {branch}")
                click.echo(f"Remote: origin")
        else:
            click.echo(click.style("🤖 AUTO: Pushing to remote (--all mode)", fg='cyan'))
        
        # Push with enhanced display
        result = run_git_with_status('push', 'origin', branch, capture=True, show_output=False)
        
        if result.returncode != 0:
            click.echo(click.style(f"✗ Push failed (exit {result.returncode}).", fg='red'))
            
            # Try recovery if not in auto mode
            if not yes and result.stderr:
                if _offer_recovery(result.stderr):
                    # Retry push after recovery
                    click.echo(click.style("\nRetrying push after recovery...", fg='cyan'))
                    result = run_git('push', 'origin', branch, capture=False)
                    if result.returncode == 0:
                        click.echo(click.style("✓ Push successful after recovery!", fg='green'))
                    else:
                        click.echo(click.style(f"✗ Push still failed after recovery.", fg='red'))
                        sys.exit(1)
                else:
                    click.echo(click.style("Push failed. Run 'goal recover' to attempt automatic recovery.", fg='yellow'))
                    sys.exit(1)
            else:
                click.echo(click.style("Push failed. Run 'goal recover' to attempt automatic recovery.", fg='yellow'))
                return False
        
        if tag_name and not no_tag:
            _echo_cmd(['git', 'push', 'origin', tag_name])
            result = run_git('push', 'origin', tag_name, capture=False)
            if result.returncode != 0:
                click.echo(click.style(f"⚠  Could not push tag {tag_name}.", fg='yellow'))
        
        click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
        return True
    except Exception as e:
        click.echo(click.style(f"✗ Push error: {e}", fg='red'))
        if not yes:
            sys.exit(1)
        return False


def _offer_recovery(error_output: str) -> bool:
    """Offer to run recovery if push fails."""
    click.echo(click.style("\n🚨 Push failed with error:", fg='red'))
    click.echo(error_output)
    
    if click.confirm(click.style("\nWould you like to attempt automatic recovery?", fg='yellow')):
        try:
            from goal.recovery import RecoveryManager
            repo_path = os.getcwd()
            manager = RecoveryManager(repo_path)
            
            click.echo(click.style("\n🔧 Attempting recovery...", fg='blue', bold=True))
            success = manager.recover_from_push_failure(error_output)
            
            if success:
                click.echo(click.style("\n✅ Recovery completed! You can now push again.", fg='green'))
                return True
            else:
                click.echo(click.style("\n❌ Automatic recovery failed.", fg='red'))
                return False
        except ImportError:
            click.echo(click.style("\n⚠️ Recovery module not available. Please run 'goal recover' manually.", fg='yellow'))
            return False
        except Exception as e:
            click.echo(click.style(f"\n❌ Recovery failed with error: {e}", fg='red'))
            return False
    
    return False
