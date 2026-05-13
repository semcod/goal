"""Large file error recovery strategy."""

import os
import re
import subprocess
import time
from typing import List
import click

from .base import RecoveryStrategy


def _run_git_chunked(
    run_git_fn, cmd_base: List[str], paths: List[str], chunk_size: int = 100, **kwargs
) -> None:
    """Run git command in chunks to avoid 'Argument list too long' errors."""
    chunk: List[str] = []
    for path in paths:
        chunk.append(path)
        if len(chunk) >= chunk_size:
            run_git_fn(*cmd_base, *chunk, **kwargs)
            chunk = []
    if chunk:
        run_git_fn(*cmd_base, *chunk, **kwargs)


class LargeFileStrategy(RecoveryStrategy):
    """Handles large file errors."""

    def __init__(self, repo_path: str, config=None):
        super().__init__(repo_path, config)
        self.last_error = None

    def can_handle(self, error_output: str) -> bool:
        """Check if error is related to large files."""
        self.last_error = error_output  # Store for later use
        large_file_patterns = [
            r"file larger than 100 MB",
            r"large files detected",
            r"cannot upload.*larger than",
            r"cannot push large files",
            r"GB exceeds GitHub\'s file size limit",
            r"MB; this exceeds GitHub\'s file size limit",
            r"pathspec.*did not match any files",
            r"large file notification",
            r"GH001: Large files detected",
            r"exceeds GitHub\'s file size limit",
        ]
        return any(
            re.search(pattern, error_output, re.IGNORECASE)
            for pattern in large_file_patterns
        )

    def recover(self, error_output: str) -> bool:
        """Attempt to recover from large file error."""
        click.echo(
            click.style("\n📦 Large file error detected", fg="yellow", bold=True)
        )

        # Try to extract file paths from error
        file_paths = self._extract_file_paths(error_output)

        if not file_paths:
            # Try to find large files in the repository
            file_paths = self._find_large_files()

        if not file_paths:
            click.echo(click.style("❌ Could not identify large files", fg="red"))
            return False

        click.echo(f"Found {len(file_paths)} large file(s) in git history:")
        for path in file_paths:
            size_mb = self._get_file_size_mb(path)
            click.echo(f"  - {path} ({size_mb:.1f} MB)")

        # Check if files are in history (not just staged)
        # If GitHub rejected the push, assume files are in history
        github_rejected = (
            "GH001: Large files detected" in error_output
            or "pre-receive hook declined" in error_output
        )

        if github_rejected or self._files_in_history(file_paths):
            click.echo(
                click.style(
                    "\n⚠️  WARNING: Large files are already committed in git history!",
                    fg="red",
                    bold=True,
                )
            )
            click.echo(click.style("\nTo proceed, we must:", fg="yellow"))
            click.echo("1. Remove large files from git history using filter-repo")
            click.echo("2. Force push to update remote")
            click.echo(
                click.style("\n⚠️  This will REWRITE GIT HISTORY:", fg="red", bold=True)
            )
            click.echo("  • All commits containing these files will be rewritten")
            click.echo("  • You will need to force push (--force-with-lease)")
            click.echo("  • Team members must re-clone or rebase their local repos")
            click.echo(
                click.style("\nYour local files will NOT be deleted:", fg="green")
            )
            click.echo("  • Files remain on your disk")
            click.echo("  • Only removed from git history")

            if not click.confirm(
                click.style(
                    "\nDo you want to proceed with history rewrite?", fg="yellow"
                )
            ):
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
                result = self.run_git(
                    "log",
                    "--all",
                    "--full-history",
                    "--",
                    path,
                    capture_output=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except:
                continue
        return False

    def _remove_from_history(self, file_paths: List[str]) -> bool:
        """Remove files from git history using filter-repo."""
        click.echo(
            click.style("\n🔧 Removing large files from git history...", fg="blue")
        )

        # Check if git-filter-repo is available
        try:
            subprocess.run(
                ["git-filter-repo", "--version"], check=True, capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo(click.style("❌ git-filter-repo is not installed", fg="red"))
            click.echo("Install with: pip install git-filter-repo")
            return False

        # Create backup before filter-repo
        backup_ref = f"goal-backup-before-filter-{int(time.time())}"
        self.run_git("branch", backup_ref)
        click.echo(f"✓ Created backup branch: {backup_ref}")

        # Store remote URL in case filter-repo removes it
        try:
            remote_url = self.run_git(
                "remote", "get-url", "origin", capture_output=True, check=True
            ).stdout.strip()
        except subprocess.CalledProcessError:
            remote_url = None

        try:
            # Run filter-repo to remove files
            cmd = ["git-filter-repo", "--force"]
            # Add each file to be removed
            for path in file_paths:
                cmd.extend(["--path", path, "--invert-paths"])

            click.echo("Running git-filter-repo (this may take a while)...")
            subprocess.run(cmd, cwd=self.repo_path, check=True)

            click.echo(click.style("✓ Large files removed from history", fg="green"))

            # Restore remote if filter-repo removed it
            if remote_url:
                try:
                    self.run_git(
                        "remote", "get-url", "origin", capture_output=True, check=True
                    )
                except subprocess.CalledProcessError:
                    click.echo("Restoring remote configuration...")
                    self.run_git("remote", "add", "origin", remote_url)
                    click.echo("✓ Remote restored")

            # Force push
            click.echo("\nForce pushing to remote...")
            # Get current branch name
            current_branch = self.run_git(
                "branch", "--show-current", capture_output=True, check=True
            ).stdout.strip()
            self.run_git(
                "push", "--set-upstream", "origin", current_branch, "--force-with-lease"
            )
            click.echo(click.style("✓ Successfully pushed to remote", fg="green"))

            # Clean up backup
            self.run_git("branch", "-D", backup_ref)

            return True

        except subprocess.CalledProcessError as e:
            click.echo(
                click.style(f"❌ Failed to remove files from history: {e}", fg="red")
            )
            click.echo(f"You can restore from backup branch: {backup_ref}")
            return False

    def _extract_file_paths(self, error_output: str) -> List[str]:
        """Extract file paths from error message."""
        paths = []

        # GitHub's specific error format: "remote: error: File <path> is <size> MB"
        # This pattern is more specific to avoid partial matches
        github_patterns = [
            r"remote:\s+error:\s+File\s+(\S+)\s+is\s+[\d.]+\s*MB",
            r"File\s+(\S+)\s+is\s+[\d.]+\s*MB",
            r"File\s+(\S+)\s+exceeds",
        ]

        for pattern in github_patterns:
            matches = re.findall(pattern, error_output, re.IGNORECASE)
            paths.extend(matches)

        # Fallback patterns for other git errors (more restrictive)
        fallback_patterns = [
            r"'([^']+\.[^']+)':",  # Must have a file extension
            r"path\s+([^\s]+\.[^\s]+)",  # Must have a file extension
        ]

        for pattern in fallback_patterns:
            matches = re.findall(pattern, error_output, re.IGNORECASE)
            paths.extend(matches)

        # Filter out invalid paths more strictly
        valid_paths = []
        for path in paths:
            # Skip common non-file words and patterns
            skip_words = [
                "file",
                "path",
                "storage",
                "size",
                "mb",
                "gb",
                "git",
                "lfs",
                "large",
                "filestorage",
            ]
            if path.lower() in skip_words:
                continue

            # Must contain either a slash (directory) or a dot (extension)
            if "/" not in path and "." not in path:
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
                "ls-tree", "-r", "-l", "HEAD", capture_output=True, check=True
            )

            large_files = []
            for line in result.stdout.split("\n"):
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
        click.echo(click.style("\n🗑️  Removing large files...", fg="yellow"))

        # Check if files are in history
        github_rejected = (
            "GH001: Large files detected" in self.last_error
            or "pre-receive hook declined" in self.last_error
        )

        if github_rejected or self._files_in_history(file_paths):
            click.echo(
                click.style(
                    "\n⚠️  Large files are in git history - using filter-repo",
                    fg="yellow",
                )
            )
            return self._remove_from_history(file_paths)

        # Files are only staged, not committed
        try:
            # Add to .gitignore
            gitignore_path = os.path.join(self.repo_path, ".gitignore")
            with open(gitignore_path, "a") as f:
                f.write("\n# Large files removed by Goal recovery\n")
                for path in file_paths:
                    f.write(f"{path}\n")

            # Remove from git (in chunks to avoid argument list too long)
            _run_git_chunked(self.run_git, ["rm", "--cached"], file_paths, check=False)
            self.run_git("add", ".gitignore")

            commit_msg = "chore: remove large files and update .gitignore"
            self.run_git("commit", "-m", commit_msg)

            click.echo(click.style("✓ Large files removed from repository", fg="green"))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Failed to remove large files: {e}", fg="red"))
            return False

    def _move_to_lfs(self, file_paths: List[str]) -> bool:
        """Move large files to Git LFS."""
        try:
            # Check if Git LFS is installed
            subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)

            # Initialize LFS if not already
            self.run_git("lfs", "install", check=False)

            # Track files with LFS
            for path in file_paths:
                self.run_git("lfs", "track", path)

            self.run_git("add", ".gitattributes")
            # Add files in chunks to avoid argument list too long
            _run_git_chunked(self.run_git, ["add"], file_paths)

            commit_msg = "chore: move large files to Git LFS"
            self.run_git("commit", "-m", commit_msg)

            click.echo(click.style("✓ Large files moved to Git LFS", fg="green"))
            return True
        except subprocess.CalledProcessError:
            click.echo(click.style("❌ Git LFS is not installed", fg="red"))
            click.echo("Install Git LFS with: git lfs install")
            return False
        except Exception as e:
            click.echo(click.style(f"✗ Failed to move files to LFS: {e}", fg="red"))
            return False

    def _skip_large_files(self, file_paths: List[str]) -> bool:
        """Skip large files in current commit."""
        try:
            # Reset the files (in chunks to avoid argument list too long)
            _run_git_chunked(self.run_git, ["reset", "HEAD", "--"], file_paths)
            click.echo(click.style("✓ Large files unstaged", fg="green"))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Failed to skip large files: {e}", fg="red"))
            return False
