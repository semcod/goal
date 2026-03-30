"""Push workflow stages - remote push."""

import sys
import os
import re
import subprocess
from typing import Optional

import click

from goal.git_ops import run_git, ensure_remote, run_git_with_status, _echo_cmd, HAS_CLICKMD
from goal.cli import confirm
from goal.recovery import RecoveryManager

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
    
    # Check for large file error first
    if _is_large_file_error(error_output):
        return _handle_large_file_error(error_output)
    
    # For other errors, show diff and offer options
    _show_diff_info()
    return _show_recovery_menu(error_output)


def _is_large_file_error(error_output: str) -> bool:
    """Check if error is related to large files."""
    large_file_patterns = [
        r'GH001: Large files detected',
        r'pre-receive hook declined',
        r'exceeds GitHub\'s file size limit',
        r'file larger than 100 MB',
    ]
    
    return any(re.search(pattern, error_output, re.IGNORECASE) 
               for pattern in large_file_patterns)


def _handle_large_file_error(error_output: str) -> bool:
    """Handle large file recovery scenarios."""
    click.echo(click.style("\n📦 Large file error detected!", fg='yellow', bold=True))
    click.echo(click.style("\nThe following files are too large for GitHub:", fg='red'))
    
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
            return _handle_large_files_in_history(error_output)
        else:
            return _handle_large_files_staged(error_output)
            
    except Exception as e:
        click.echo(click.style(f"\n⚠️ Could not analyze error: {e}", fg='yellow'))
        return False


def _handle_large_files_in_history(error_output: str) -> bool:
    """Handle large files that are already in git history."""
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
        return _execute_recovery(error_output)
    else:
        click.echo(click.style("\nRecovery cancelled. Large files remain in history.", fg='yellow'))
        return False


def _handle_large_files_staged(error_output: str) -> bool:
    """Handle large files that are staged but not committed."""
    click.echo(click.style("\n✓ Files are not committed yet - just need to be unstaged.", fg='green'))
    if click.confirm(click.style("\nProceed with automatic recovery?", fg='yellow')):
        return _execute_recovery(error_output)
    else:
        return False


def _execute_recovery(error_output: str) -> bool:
    """Execute the recovery process."""
    try:
        repo_path = os.getcwd()
        manager = RecoveryManager(repo_path)
        
        click.echo(click.style("\n🔧 Starting automatic recovery...", fg='blue', bold=True))
        success = manager.recover_from_push_failure(error_output)
        
        if success:
            click.echo(click.style("\n✅ Recovery completed!", fg='green'))
            return True
        else:
            click.echo(click.style("\n❌ Recovery failed.", fg='red'))
            return False
    except Exception as e:
        click.echo(click.style(f"\n❌ Recovery failed: {e}", fg='red'))
        return False


def _show_diff_info() -> None:
    """Show differences between local and remote."""
    click.echo(click.style("\n📋 Conflict Resolution Options:", fg='blue', bold=True))
    
    try:
        click.echo(click.style("\n🔍 Checking differences between local and remote...", fg='cyan'))
        
        # Get local commit count ahead/behind
        result = subprocess.run(
            ['git', 'rev-list', '--left-right', '--count', 'HEAD...origin/main'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        if result.returncode == 0:
            ahead_behind = result.stdout.strip().split()
            if len(ahead_behind) == 2:
                ahead, behind = int(ahead_behind[0]), int(ahead_behind[1])
                click.echo(f"\n  Local branch is:")
                if ahead > 0:
                    click.echo(f"    • {ahead} commit(s) ahead of remote (local changes to push)")
                if behind > 0:
                    click.echo(f"    • {behind} commit(s) behind remote (remote changes not in local)")
                if ahead == 0 and behind == 0:
                    click.echo(f"    • Same commit count, but histories diverged")
        
        # Show recent local commits
        click.echo(click.style("\n📤 Your local commits (not on remote):", fg='yellow'))
        result = subprocess.run(
            ['git', 'log', '--oneline', '--decorate', 'origin/main..HEAD', '-5'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n')[:5]:
                click.echo(f"  • {line}")
        else:
            click.echo("  (none visible)")
            
    except Exception as e:
        click.echo(click.style(f"  Could not get diff info: {e}", fg='yellow'))


def _show_recovery_menu(error_output: str) -> bool:
    """Show interactive recovery menu and handle choice."""
    click.echo(click.style("\n💡 What would you like to do?", fg='blue', bold=True))
    click.echo("\n  [1] 🚀 Force push (overwrite remote with local changes)")
    click.echo("       ⚠️  Warning: This will replace remote history!")
    click.echo("       Use when: You've rewritten history (e.g., removed large files)")
    
    click.echo("\n  [2] 📥 Pull and merge (integrate remote changes)")
    click.echo("       This will fetch remote and merge changes into your branch")
    click.echo("       Use when: Remote has changes you want to keep")
    
    click.echo("\n  [3] 👀 View detailed diff (see exactly what's different)")
    click.echo("       Show full commit log comparison")
    
    click.echo("\n  [4] 🔄 Automatic recovery (let Goal try to fix it)")
    click.echo("       Attempt smart conflict resolution")
    
    click.echo("\n  [5] ❌ Cancel (exit and handle manually)")
    click.echo("       You can fix the issue manually and retry later")
    
    choice = click.prompt(
        click.style("\nEnter your choice", fg='yellow', bold=True),
        type=click.Choice(['1', '2', '3', '4', '5']),
        default='5'
    )
    
    return _handle_recovery_choice(choice, error_output)


def _handle_recovery_choice(choice: str, error_output: str) -> bool:
    """Handle the user's recovery choice."""
    if choice == '1':
        return _handle_force_push()
    elif choice == '2':
        return _handle_pull_merge()
    elif choice == '3':
        return _handle_view_diff()
    elif choice == '4':
        return _handle_automatic_recovery(error_output)
    else:  # choice == '5' or default
        click.echo(click.style("\n❌ Cancelled. No changes made.", fg='yellow'))
        click.echo(click.style("You can run 'goal push' again when ready.", fg='cyan'))
        return False


def _handle_force_push() -> bool:
    """Handle force push option."""
    click.echo(click.style("\n🚀 Attempting force push...", fg='blue', bold=True))
    click.echo(click.style("⚠️  This will overwrite remote history!", fg='red'))
    if click.confirm(click.style("Are you sure?", fg='red', bold=True)):
        try:
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, cwd=os.getcwd(), check=True
            )
            current_branch = branch_result.stdout.strip()
            
            result = subprocess.run(
                ['git', 'push', '--force', 'origin', current_branch],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode == 0:
                click.echo(click.style("✅ Force push successful!", fg='green', bold=True))
                return True
            else:
                click.echo(click.style(f"❌ Force push failed: {result.stderr}", fg='red'))
                return False
        except Exception as e:
            click.echo(click.style(f"❌ Force push error: {e}", fg='red'))
            return False
    else:
        click.echo(click.style("Force push cancelled.", fg='yellow'))
        return False


def _handle_pull_merge() -> bool:
    """Handle pull and merge option."""
    click.echo(click.style("\n📥 Pulling remote changes...", fg='blue', bold=True))
    try:
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        if result.returncode == 0:
            click.echo(click.style("✅ Pull successful! Remote changes merged.", fg='green'))
            click.echo(click.style("\nYou can now retry 'goal push' to push your changes.", fg='cyan'))
            return False  # Don't auto-retry, let user decide
        else:
            click.echo(click.style(f"❌ Pull failed: {result.stderr}", fg='red'))
            return False
    except Exception as e:
        click.echo(click.style(f"❌ Pull error: {e}", fg='red'))
        return False


def _handle_view_diff() -> bool:
    """Handle view detailed diff option."""
    click.echo(click.style("\n👀 Detailed diff:", fg='blue', bold=True))
    try:
        # Show full log comparison
        result = subprocess.run(
            ['git', 'log', '--oneline', '--left-right', 'HEAD...origin/main'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            click.echo(click.style("\nCommits comparison (local | remote):", fg='cyan'))
            click.echo(result.stdout)
        
        # Show what files differ
        result = subprocess.run(
            ['git', 'diff', '--stat', 'HEAD', 'origin/main'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        if result.returncode == 0 and result.stdout.strip():
            click.echo(click.style("\nFiles that differ:", fg='cyan'))
            click.echo(result.stdout)
        
        click.echo(click.style("\n💡 Run 'goal push' again to choose an action.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"Could not show diff: {e}", fg='yellow'))
    return False


def _handle_automatic_recovery(error_output: str) -> bool:
    """Handle automatic recovery option."""
    click.echo(click.style("\n🔧 Attempting automatic recovery...", fg='blue', bold=True))
    try:
        repo_path = os.getcwd()
        manager = RecoveryManager(repo_path)
        
        success = manager.recover_from_push_failure(error_output)
        
        if success:
            click.echo(click.style("\n✅ Recovery completed! You can now push again.", fg='green'))
            return True
        else:
            click.echo(click.style("\n❌ Automatic recovery failed.", fg='red'))
            return False
    except ImportError:
        click.echo(click.style("\n⚠️ Recovery module not available.", fg='yellow'))
        return False
    except Exception as e:
        click.echo(click.style(f"\n❌ Recovery failed: {e}", fg='red'))
        return False
