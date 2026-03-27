"""Recovery strategies for different git push failure scenarios."""

import os
import re
import subprocess
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import click

from .exceptions import (
    RecoveryError,
    AuthError,
    LargeFileError,
    DivergentHistoryError,
    CorruptedObjectError,
    LFSIssueError,
    NetworkError,
    QuotaExceededError,
)


class RecoveryStrategy(ABC):
    """Base class for all recovery strategies."""
    
    def __init__(self, repo_path: str, config: Dict[str, Any] = None):
        self.repo_path = repo_path
        self.config = config or {}
        self.git_env = os.environ.copy()
        
    @abstractmethod
    def can_handle(self, error_output: str) -> bool:
        """Check if this strategy can handle the given error."""
        pass
    
    @abstractmethod
    def recover(self, error_output: str) -> bool:
        """Attempt to recover from the error. Returns True if successful."""
        pass
    
    def run_git(self, *args, capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the repository."""
        cmd = ['git'] + list(args)
        try:
            return subprocess.run(
                cmd, 
                cwd=self.repo_path,
                env=self.git_env,
                capture_output=capture_output,
                text=True,
                check=check
            )
        except subprocess.CalledProcessError as e:
            click.echo(f"Git command failed: {' '.join(cmd)}")
            click.echo(f"Error: {e.stderr}")
            raise
    
    def run_git_with_output(self, *args) -> str:
        """Run git command and return stdout."""
        result = self.run_git(*args, capture_output=True, check=True)
        return result.stdout.strip()


class AuthErrorStrategy(RecoveryStrategy):
    """Handles authentication errors."""
    
    def can_handle(self, error_output: str) -> bool:
        """Check if error is authentication related."""
        auth_patterns = [
            r'authentication failed',
            r'invalid credentials',
            r'invalid username or password',
            r'permission denied',
            r'401',
            r'403',
            r'support for password authentication was removed',
            r'could not read Username',
            r'fatal: Authentication failed'
        ]
        return any(re.search(pattern, error_output, re.IGNORECASE) for pattern in auth_patterns)
    
    def recover(self, error_output: str) -> bool:
        """Attempt to recover from authentication error."""
        click.echo(click.style("\n🔐 Authentication error detected", fg='yellow', bold=True))
        click.echo("Attempting to recover...")
        
        # Try to check if we have a GitHub token
        if 'GITHUB_TOKEN' in os.environ:
            click.echo("✓ Found GITHUB_TOKEN environment variable")
            # Update remote URL to use token
            try:
                remote_url = self.run_git_with_output('remote', 'get-url', 'origin')
                if 'github.com' in remote_url:
                    # Convert to token-based URL
                    if remote_url.startswith('https://'):
                        token_url = remote_url.replace('https://', f'https://{os.environ["GITHUB_TOKEN"]}@')
                        self.run_git('remote', 'set-url', 'origin', token_url)
                        click.echo("✓ Updated remote URL with token")
                        return True
            except Exception as e:
                click.echo(click.style(f"✗ Failed to update remote URL: {e}", fg='red'))
        
        # Try to use gh CLI authentication
        try:
            self.run_git('credential', 'fill', check=False)
            result = self.run_git('ls-remote', '--heads', 'origin', check=False)
            if result.returncode == 0:
                click.echo("✓ Git credentials are valid")
                return True
        except:
            pass
        
        # Check if gh CLI is available and authenticated
        try:
            subprocess.run(['gh', 'auth', 'status'], check=True, capture_output=True)
            click.echo("✓ GitHub CLI (gh) is authenticated")
            # Try to clone using gh
            return True
        except:
            pass
        
        click.echo(click.style("\n❌ Could not resolve authentication issue", fg='red'))
        click.echo("\nPossible solutions:")
        click.echo("1. Set GITHUB_TOKEN environment variable")
        click.echo("2. Run 'gh auth login' to authenticate with GitHub CLI")
        click.echo("3. Update your git credentials with 'git config --global credential.helper store'")
        
        return False


class LargeFileStrategy(RecoveryStrategy):
    """Handles large file errors."""
    
    def __init__(self, repo_path: str, config=None):
        super().__init__(repo_path, config)
        self.last_error = None
    
    def can_handle(self, error_output: str) -> bool:
        """Check if error is related to large files."""
        self.last_error = error_output  # Store for later use
        large_file_patterns = [
            r'file larger than 100 MB',
            r'large files detected',
            r'cannot upload.*larger than',
            r'cannot push large files',
            r'GB exceeds GitHub\'s file size limit',
            r'MB; this exceeds GitHub\'s file size limit',
            r'pathspec.*did not match any files',
            r'large file notification',
            r'GH001: Large files detected',
            r'exceeds GitHub\'s file size limit'
        ]
        return any(re.search(pattern, error_output, re.IGNORECASE) for pattern in large_file_patterns)
    
    def recover(self, error_output: str) -> bool:
        """Attempt to recover from large file error."""
        click.echo(click.style("\n📦 Large file error detected", fg='yellow', bold=True))
        
        # Try to extract file paths from error
        file_paths = self._extract_file_paths(error_output)
        
        if not file_paths:
            # Try to find large files in the repository
            file_paths = self._find_large_files()
        
        if not file_paths:
            click.echo(click.style("❌ Could not identify large files", fg='red'))
            return False
        
        click.echo(f"Found {len(file_paths)} large file(s) in git history:")
        for path in file_paths:
            size_mb = self._get_file_size_mb(path)
            click.echo(f"  - {path} ({size_mb:.1f} MB)")
        
        # Check if files are in history (not just staged)
        # If GitHub rejected the push, assume files are in history
        github_rejected = 'GH001: Large files detected' in error_output or 'pre-receive hook declined' in error_output
        
        if github_rejected or self._files_in_history(file_paths):
            click.echo(click.style("\n⚠️  WARNING: Large files are already committed in git history!", fg='red', bold=True))
            click.echo(click.style("\nTo proceed, we must:", fg='yellow'))
            click.echo("1. Remove large files from git history using filter-repo")
            click.echo("2. Force push to update remote")
            click.echo(click.style("\n⚠️  This will REWRITE GIT HISTORY:", fg='red', bold=True))
            click.echo("  • All commits containing these files will be rewritten")
            click.echo("  • You will need to force push (--force-with-lease)")
            click.echo("  • Team members must re-clone or rebase their local repos")
            click.echo(click.style("\nYour local files will NOT be deleted:", fg='green'))
            click.echo("  • Files remain on your disk")
            click.echo("  • Only removed from git history")
            
            if not click.confirm(click.style("\nDo you want to proceed with history rewrite?", fg='yellow')):
                click.echo("Operation cancelled.")
                return False
            
            # Use filter-repo to remove from history
            return self._remove_from_history(file_paths)
        
        # Files are only staged, not committed
        click.echo("\nRecovery options:")
        click.echo("1. Add files to .gitignore and remove from history")
        click.echo("2. Move files to Git LFS")
        click.echo("3. Continue without these files")
        
        choice = click.prompt("Choose option [1/2/3]", type=int, default=1)
        
        if choice == 1:
            return self._remove_large_files(file_paths)
        elif choice == 2:
            return self._move_to_lfs(file_paths)
        elif choice == 3:
            return self._skip_large_files(file_paths)
        
        return False
    
    def _files_in_history(self, file_paths: List[str]) -> bool:
        """Check if files are in git history (not just staged)."""
        for path in file_paths:
            try:
                # Check if file exists in any commit
                result = self.run_git('log', '--all', '--full-history', '--', path, 
                                    capture_output=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except:
                continue
        return False
    
    def _remove_from_history(self, file_paths: List[str]) -> bool:
        """Remove files from git history using filter-repo."""
        click.echo(click.style("\n🔧 Removing large files from git history...", fg='blue'))
        
        # Check if git-filter-repo is available
        try:
            subprocess.run(['git-filter-repo', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo(click.style("❌ git-filter-repo is not installed", fg='red'))
            click.echo("Install with: pip install git-filter-repo")
            return False
        
        # Create backup before filter-repo
        backup_ref = f"goal-backup-before-filter-{int(time.time())}"
        self.run_git('branch', backup_ref)
        click.echo(f"✓ Created backup branch: {backup_ref}")
        
        # Store remote URL in case filter-repo removes it
        try:
            remote_url = self.run_git('remote', 'get-url', 'origin', capture_output=True, check=True).stdout.strip()
        except subprocess.CalledProcessError:
            remote_url = None
        
        try:
            # Run filter-repo to remove files
            cmd = ['git-filter-repo', '--force']
            # Add each file to be removed
            for path in file_paths:
                cmd.extend(['--path', path, '--invert-paths'])
            
            click.echo("Running git-filter-repo (this may take a while)...")
            subprocess.run(cmd, cwd=self.repo_path, check=True)
            
            click.echo(click.style("✓ Large files removed from history", fg='green'))
            
            # Restore remote if filter-repo removed it
            if remote_url:
                try:
                    self.run_git('remote', 'get-url', 'origin', capture_output=True, check=True)
                except subprocess.CalledProcessError:
                    click.echo("Restoring remote configuration...")
                    self.run_git('remote', 'add', 'origin', remote_url)
                    click.echo("✓ Remote restored")
            
            # Force push
            click.echo("\nForce pushing to remote...")
            # Get current branch name
            current_branch = self.run_git('branch', '--show-current', capture_output=True, check=True).stdout.strip()
            self.run_git('push', '--set-upstream', 'origin', current_branch, '--force-with-lease')
            click.echo(click.style("✓ Successfully pushed to remote", fg='green'))
            
            # Clean up backup
            self.run_git('branch', '-D', backup_ref)
            
            return True
            
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"❌ Failed to remove files from history: {e}", fg='red'))
            click.echo(f"You can restore from backup branch: {backup_ref}")
            return False
    
    def _extract_file_paths(self, error_output: str) -> List[str]:
        """Extract file paths from error message."""
        paths = []
        
        # GitHub's specific error format: "remote: error: File <path> is <size> MB"
        # This pattern is more specific to avoid partial matches
        github_patterns = [
            r'remote:\s+error:\s+File\s+(\S+)\s+is\s+[\d.]+\s*MB',
            r'File\s+(\S+)\s+is\s+[\d.]+\s*MB',
            r'File\s+(\S+)\s+exceeds',
        ]
        
        for pattern in github_patterns:
            matches = re.findall(pattern, error_output, re.IGNORECASE)
            paths.extend(matches)
        
        # Fallback patterns for other git errors (more restrictive)
        fallback_patterns = [
            r"'([^']+\.[^']+)':",  # Must have a file extension
            r'path\s+([^\s]+\.[^\s]+)',  # Must have a file extension
        ]
        
        for pattern in fallback_patterns:
            matches = re.findall(pattern, error_output, re.IGNORECASE)
            paths.extend(matches)
        
        # Filter out invalid paths more strictly
        valid_paths = []
        for path in paths:
            # Skip common non-file words and patterns
            skip_words = ['file', 'path', 'storage', 'size', 'mb', 'gb', 'git', 'lfs', 'large', 'filestorage']
            if path.lower() in skip_words:
                continue
            
            # Must contain either a slash (directory) or a dot (extension)
            if '/' not in path and '.' not in path:
                continue
            
            # Skip if it's too short
            if len(path) < 3:
                continue
            
            valid_paths.append(path)
        
        return list(set(valid_paths))  # Remove duplicates
    
    def _find_large_files(self, min_size_mb: int = 50) -> List[str]:
        """Find large files in the repository."""
        try:
            # Find files larger than min_size_mb
            result = self.run_git(
                'ls-tree', '-r', '-l', 'HEAD',
                capture_output=True, check=True
            )
            
            large_files = []
            for line in result.stdout.split('\n'):
                parts = line.split()
                if len(parts) >= 4:
                    size = int(parts[3])
                    size_mb = size / (1024 * 1024)
                    if size_mb > min_size_mb:
                        file_path = parts[4]
                        large_files.append(file_path)
            
            return large_files
        except:
            return []
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB."""
        try:
            full_path = os.path.join(self.repo_path, file_path)
            size_bytes = os.path.getsize(full_path)
            return size_bytes / (1024 * 1024)
        except:
            return 0.0
    
    def _remove_large_files(self, file_paths: List[str]) -> bool:
        """Remove large files from repository."""
        click.echo(click.style("\n🗑️  Removing large files...", fg='yellow'))
        
        # Check if files are in history
        github_rejected = 'GH001: Large files detected' in self.last_error or 'pre-receive hook declined' in self.last_error
        
        if github_rejected or self._files_in_history(file_paths):
            click.echo(click.style("\n⚠️  Large files are in git history - using filter-repo", fg='yellow'))
            return self._remove_from_history(file_paths)
        
        # Files are only staged, not committed
        try:
            # Add to .gitignore
            gitignore_path = os.path.join(self.repo_path, '.gitignore')
            with open(gitignore_path, 'a') as f:
                f.write('\n# Large files removed by Goal recovery\n')
                for path in file_paths:
                    f.write(f'{path}\n')
            
            # Remove from git
            self.run_git('rm', '--cached', *file_paths, check=False)
            self.run_git('add', '.gitignore')
            
            commit_msg = "chore: remove large files and update .gitignore"
            self.run_git('commit', '-m', commit_msg)
            
            click.echo(click.style("✓ Large files removed from repository", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Failed to remove large files: {e}", fg='red'))
            return False
    
    def _move_to_lfs(self, file_paths: List[str]) -> bool:
        """Move large files to Git LFS."""
        try:
            # Check if Git LFS is installed
            subprocess.run(['git', 'lfs', 'version'], check=True, capture_output=True)
            
            # Initialize LFS if not already
            self.run_git('lfs', 'install', check=False)
            
            # Track files with LFS
            for path in file_paths:
                self.run_git('lfs', 'track', path)
            
            self.run_git('add', '.gitattributes')
            self.run_git('add', *file_paths)
            
            commit_msg = "chore: move large files to Git LFS"
            self.run_git('commit', '-m', commit_msg)
            
            click.echo(click.style("✓ Large files moved to Git LFS", fg='green'))
            return True
        except subprocess.CalledProcessError:
            click.echo(click.style("❌ Git LFS is not installed", fg='red'))
            click.echo("Install Git LFS with: git lfs install")
            return False
        except Exception as e:
            click.echo(click.style(f"✗ Failed to move files to LFS: {e}", fg='red'))
            return False
    
    def _skip_large_files(self, file_paths: List[str]) -> bool:
        """Skip large files in current commit."""
        try:
            # Reset the files
            self.run_git('reset', 'HEAD', '--', *file_paths)
            click.echo(click.style("✓ Large files unstaged", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Failed to skip large files: {e}", fg='red'))
            return False


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


class ForcePushStrategy(RecoveryStrategy):
    """Handles force push recovery scenarios."""
    
    def can_handle(self, error_output: str) -> bool:
        """Check if error requires force push."""
        patterns = [
            r'protected branch',
            r'force push',
            r'push --force',
            r'update --force'
        ]
        return any(re.search(pattern, error_output, re.IGNORECASE) for pattern in patterns)
    
    def recover(self, error_output: str) -> bool:
        """Attempt to recover with force push."""
        click.echo(click.style("\n💪 Force push may be required", fg='yellow', bold=True))
        
        if click.confirm(click.style("Force push may overwrite remote changes. Continue?", fg='red')):
            try:
                # Use force-with-lease for safety
                self.run_git('push', '--force-with-lease')
                click.echo(click.style("✓ Force push successful", fg='green'))
                return True
            except Exception as e:
                click.echo(click.style(f"✗ Force push failed: {e}", fg='red'))
                
                # Try with regular force as last resort
                if click.confirm("Try with regular force push?"):
                    try:
                        self.run_git('push', '--force')
                        click.echo(click.style("✓ Force push successful", fg='green'))
                        return True
                    except Exception as e2:
                        click.echo(click.style(f"✗ Force push failed: {e2}", fg='red'))
                        return False
        
        return False
