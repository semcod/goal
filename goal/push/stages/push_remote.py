"""Push workflow stages - remote push."""

import sys
import os
import re
from typing import Optional

import click

from goal.git_ops import run_git, ensure_remote, get_remote_branch, run_git_with_status, _echo_cmd, HAS_CLICKMD
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
    
    # Check if this is a large file error
    large_file_patterns = [
        r'GH001: Large files detected',
        r'pre-receive hook declined',
        r'exceeds GitHub\'s file size limit',
        r'file larger than 100 MB',
    ]
    
    is_large_file_error = any(re.search(pattern, error_output, re.IGNORECASE) 
                             for pattern in large_file_patterns)
    
    if is_large_file_error:
        click.echo(click.style("\n📦 Large file error detected!", fg='yellow', bold=True))
        click.echo(click.style("\nThe following files are too large for GitHub:", fg='red'))
        
        # Try to extract file paths from error
        try:
            from goal.recovery.strategies import LargeFileStrategy
            strategy = LargeFileStrategy(os.getcwd())
            file_paths = strategy._extract_file_paths(error_output)
            
            if file_paths:
                for path in file_paths[:10]:  # Show max 10 files
                    click.echo(f"  • {path}")
                if len(file_paths) > 10:
                    click.echo(f"  ... and {len(file_paths) - 10} more files")
            
            # Check if files are in history
            if strategy._files_in_history(file_paths):
                click.echo(click.style("\n⚠️  These files are already committed in git history!", fg='red', bold=True))
                click.echo(click.style("\nTo fix this, we need to:", fg='yellow'))
                click.echo("1. Create a backup branch")
                click.echo("2. Remove large files from git history using filter-repo")
                click.echo("3. Force push to update remote")
                click.echo(click.style("\n⚠️  This will REWRITE GIT HISTORY:", fg='red'))
                click.echo("  • Commits will be rewritten")
                click.echo("  • Team members must re-clone or rebase")
                click.echo(click.style("\nYour local files will NOT be deleted.", fg='green'))
                
                if click.confirm(click.style("\nProceed with automatic recovery?", fg='yellow', bold=True)):
                    try:
                        from goal.recovery import RecoveryManager
                        repo_path = os.getcwd()
                        manager = RecoveryManager(repo_path)
                        
                        click.echo(click.style("\n🔧 Starting automatic recovery...", fg='blue', bold=True))
                        success = manager.recover_from_push_failure(error_output)
                        
                        if success:
                            click.echo(click.style("\n✅ Recovery completed! Large files removed from history.", fg='green'))
                            return True
                        else:
                            click.echo(click.style("\n❌ Recovery failed. You may need to run manually:", fg='red'))
                            click.echo("  goal recover")
                            return False
                    except Exception as e:
                        click.echo(click.style(f"\n❌ Recovery failed: {e}", fg='red'))
                        return False
                else:
                    click.echo(click.style("\nRecovery cancelled. Large files remain in history.", fg='yellow'))
                    return False
            else:
                click.echo(click.style("\n✓ Files are not committed yet - just need to be unstaged.", fg='green'))
                if click.confirm(click.style("\nProceed with automatic recovery?", fg='yellow')):
                    try:
                        from goal.recovery import RecoveryManager
                        repo_path = os.getcwd()
                        manager = RecoveryManager(repo_path)
                        
                        click.echo(click.style("\n🔧 Starting recovery...", fg='blue', bold=True))
                        success = manager.recover_from_push_failure(error_output)
                        
                        if success:
                            click.echo(click.style("\n✅ Recovery completed! Files unstaged and added to .gitignore.", fg='green'))
                            return True
                        else:
                            click.echo(click.style("\n❌ Recovery failed.", fg='red'))
                            return False
                    except Exception as e:
                        click.echo(click.style(f"\n❌ Recovery failed: {e}", fg='red'))
                        return False
                else:
                    return False
        except Exception as e:
            click.echo(click.style(f"\n⚠️ Could not analyze error: {e}", fg='yellow'))
    
    # For non-large-file errors, offer general recovery
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
