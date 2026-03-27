"""Recovery manager that orchestrates recovery strategies."""

import os
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import click

from .strategies import (
    RecoveryStrategy,
    AuthErrorStrategy,
    LargeFileStrategy,
    DivergentHistoryStrategy,
    CorruptedObjectStrategy,
    LFSIssueStrategy,
    ForcePushStrategy,
)
from .exceptions import (
    RecoveryError,
    RollbackError,
    NetworkError,
    QuotaExceededError,
)


class RecoveryManager:
    """Manages the recovery process for failed git pushes."""
    
    def __init__(self, repo_path: str, config: Dict[str, Any] = None):
        self.repo_path = repo_path
        self.config = config or {}
        self.recovery_dir = os.path.join(repo_path, '.goal', 'recovery')
        self.clean_clone_dir = os.path.join(self.recovery_dir, 'clean-clone')
        self.backup_dir = os.path.join(self.recovery_dir, 'backups')
        
        # Initialize strategies
        self.strategies: List[RecoveryStrategy] = [
            AuthErrorStrategy(repo_path, config),
            LargeFileStrategy(repo_path, config),
            DivergentHistoryStrategy(repo_path, config),
            CorruptedObjectStrategy(repo_path, config),
            LFSIssueStrategy(repo_path, config),
            ForcePushStrategy(repo_path, config),
        ]
        
        self._ensure_recovery_dir()
    
    def _ensure_recovery_dir(self):
        """Ensure recovery directory exists."""
        os.makedirs(self.recovery_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Add to .gitignore
        gitignore_path = os.path.join(self.repo_path, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                content = f.read()
            if '.goal/recovery/' not in content:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# Goal recovery directory\n.goal/recovery/\n')
    
    def run_git(self, *args, capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the repository."""
        cmd = ['git'] + list(args)
        try:
            return subprocess.run(
                cmd, 
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                check=check
            )
        except subprocess.CalledProcessError as e:
            click.echo(f"Git command failed: {' '.join(cmd)}")
            click.echo(f"Error: {e.stderr}")
            raise
    
    def recover_from_push_failure(self, error_output: str) -> bool:
        """Attempt to recover from a git push failure."""
        click.echo(click.style("\n🚀 Starting recovery process...", fg='blue', bold=True))
        
        # Create backup before attempting recovery
        backup_branch = self._create_backup()
        
        try:
            # Identify the appropriate strategy
            strategy = self._identify_strategy(error_output)
            
            if not strategy:
                click.echo(click.style("\n❌ No recovery strategy found for this error", fg='red'))
                click.echo("\nError output:")
                click.echo(error_output)
                return False
            
            click.echo(f"\nUsing {strategy.__class__.__name__} for recovery")
            
            # Execute recovery
            success = strategy.recover(error_output)
            
            if success:
                # Try to push again
                click.echo("\nAttempting to push after recovery...")
                push_result = self._attempt_push()
                
                if push_result:
                    click.echo(click.style("\n✅ Recovery successful! Push completed.", fg='green', bold=True))
                    self._cleanup_backup(backup_branch)
                    return True
                else:
                    click.echo(click.style("\n⚠️ Recovery completed but push still failed", fg='yellow'))
                    return False
            else:
                click.echo(click.style("\n❌ Recovery strategy failed", fg='red'))
                return False
                
        except Exception as e:
            click.echo(click.style(f"\n💥 Recovery failed with error: {e}", fg='red'))
            click.echo("Rolling back to backup...")
            self._rollback_to_backup(backup_branch)
            return False
    
    def _identify_strategy(self, error_output: str) -> Optional[RecoveryStrategy]:
        """Identify the appropriate recovery strategy for the error."""
        for strategy in self.strategies:
            if strategy.can_handle(error_output):
                return strategy
        return None
    
    def _create_backup(self) -> str:
        """Create a backup branch before attempting recovery."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_branch = f"goal-recovery-backup-{timestamp}"
        
        try:
            self.run_git('checkout', '-b', backup_branch)
            click.echo(f"✓ Created backup branch: {backup_branch}")
            return backup_branch
        except Exception as e:
            click.echo(click.style(f"⚠️ Could not create backup branch: {e}", fg='yellow'))
            return None
    
    def _cleanup_backup(self, backup_branch: str):
        """Clean up backup branch after successful recovery."""
        if backup_branch:
            try:
                self.run_git('checkout', 'main')
                self.run_git('branch', '-D', backup_branch)
                click.echo(f"✓ Cleaned up backup branch: {backup_branch}")
            except:
                pass
    
    def _rollback_to_backup(self, backup_branch: str):
        """Rollback to backup branch."""
        if not backup_branch:
            click.echo(click.style("❌ No backup branch to rollback to", fg='red'))
            return
        
        try:
            # Switch back to main branch
            self.run_git('checkout', 'main', check=False)
            
            # Reset to backup
            self.run_git('reset', '--hard', backup_branch)
            click.echo(click.style(f"✓ Rolled back to backup: {backup_branch}", fg='green'))
        except Exception as e:
            click.echo(click.style(f"❌ Rollback failed: {e}", fg='red'))
    
    def _attempt_push(self) -> bool:
        """Attempt to push to remote."""
        try:
            result = self.run_git('push', 'origin', 'HEAD', capture_output=True, check=False)
            return result.returncode == 0
        except:
            return False
    
    def setup_clean_clone(self) -> bool:
        """Set up a clean clone from remote for reference."""
        click.echo("\nSetting up clean reference clone...")
        
        # Get remote URL
        try:
            remote_url = self.run_git('remote', 'get-url', 'origin', capture_output=True, check=True)
            remote_url = remote_url.stdout.strip()
        except:
            click.echo(click.style("❌ Could not get remote URL", fg='red'))
            return False
        
        # Remove existing clean clone if it exists
        if os.path.exists(self.clean_clone_dir):
            shutil.rmtree(self.clean_clone_dir)
        
        try:
            # Clone the repository
            subprocess.run(
                ['git', 'clone', remote_url, self.clean_clone_dir],
                check=True,
                capture_output=True
            )
            click.echo(click.style("✓ Clean clone created", fg='green'))
            return True
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"❌ Failed to create clean clone: {e}", fg='red'))
            return False
    
    def identify_new_commits(self) -> List[str]:
        """Identify commits that are in local repo but not in clean clone."""
        if not os.path.exists(self.clean_clone_dir):
            if not self.setup_clean_clone():
                return []
        
        try:
            # Get commit hashes that are in local but not in remote
            result = self.run_git(
                'log', '--oneline', f'origin/main..HEAD',
                capture_output=True, check=True
            )
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    hash_part = line.split()[0]
                    commits.append(hash_part)
            
            return commits
        except:
            return []
    
    def cherry_pick_commits(self, commits: List[str]) -> bool:
        """Cherry-pick commits onto clean clone."""
        if not commits:
            click.echo("No new commits to cherry-pick")
            return True
        
        click.echo(f"Cherry-picking {len(commits)} commit(s)...")
        
        # Work in the clean clone
        original_dir = os.getcwd()
        try:
            os.chdir(self.clean_clone_dir)
            
            for commit in reversed(commits):  # Apply in correct order
                try:
                    subprocess.run(['git', 'cherry-pick', commit], check=True, capture_output=True)
                    click.echo(f"✓ Cherry-picked {commit}")
                except subprocess.CalledProcessError as e:
                    click.echo(click.style(f"✗ Failed to cherry-pick {commit}: {e}", fg='red'))
                    # Abort cherry-pick
                    subprocess.run(['git', 'cherry-pick', '--abort'], check=False)
                    return False
            
            return True
            
        finally:
            os.chdir(original_dir)
    
    def push_from_clean_clone(self) -> bool:
        """Push from the clean clone."""
        original_dir = os.getcwd()
        try:
            os.chdir(self.clean_clone_dir)
            
            click.echo("Pushing from clean clone...")
            subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
            click.echo(click.style("✓ Push successful from clean clone", fg='green'))
            
            # Update original repo
            os.chdir(self.repo_path)
            self.run_git('fetch', 'origin')
            self.run_git('reset', '--hard', 'origin/main')
            
            return True
            
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"❌ Push from clean clone failed: {e}", fg='red'))
            return False
        finally:
            os.chdir(original_dir)
    
    def full_recovery_workflow(self) -> bool:
        """Execute full recovery workflow using clean clone method."""
        click.echo(click.style("\n🔄 Starting full recovery workflow...", fg='blue', bold=True))
        
        # Create backup
        backup_branch = self._create_backup()
        
        try:
            # Identify new commits
            new_commits = self.identify_new_commits()
            
            if not new_commits:
                click.echo("No new commits found")
                return True
            
            click.echo(f"Found {len(new_commits)} new commit(s)")
            
            # Set up clean clone
            if not self.setup_clean_clone():
                return False
            
            # Cherry-pick commits
            if not self.cherry_pick_commits(new_commits):
                click.echo(click.style("❌ Cherry-pick failed", fg='red'))
                return False
            
            # Push from clean clone
            if not self.push_from_clean_clone():
                return False
            
            click.echo(click.style("\n✅ Full recovery successful!", fg='green', bold=True))
            self._cleanup_backup(backup_branch)
            return True
            
        except Exception as e:
            click.echo(click.style(f"\n💥 Full recovery failed: {e}", fg='red'))
            self._rollback_to_backup(backup_branch)
            return False
