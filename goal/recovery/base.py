"""Base recovery strategy class."""

import os
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any
import click


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

    def run_git(
        self, *args, capture_output: bool = True, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a git command in the repository."""
        cmd = ["git"] + list(args)
        try:
            return subprocess.run(
                cmd,
                cwd=self.repo_path,
                env=self.git_env,
                capture_output=capture_output,
                text=True,
                check=check,
            )
        except subprocess.CalledProcessError as e:
            click.echo(f"Git command failed: {' '.join(cmd)}")
            click.echo(f"Error: {e.stderr}")
            raise

    def run_git_with_output(self, *args) -> str:
        """Run git command and return stdout."""
        result = self.run_git(*args, capture_output=True, check=True)
        return result.stdout.strip()
