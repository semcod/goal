"""Base abstraction for package managers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import shutil
import subprocess
import time


@dataclass
class InstallResult:
    """Result of a package manager operation."""

    manager: str
    success: bool
    duration_s: float
    command: str
    error: Optional[str] = None


class AbstractPackageManager(ABC):
    """Abstract base class for package managers."""

    name: str
    priority: int  # Lower is better (uv=10, pip=100)
    binary: str  # Binary name for availability check

    def is_available(self) -> bool:
        """Check if this package manager is installed."""
        return shutil.which(self.binary) is not None

    @abstractmethod
    def install_editable(self, extras: list[str]) -> InstallResult:
        """Install package in editable mode with extras."""
        ...

    @abstractmethod
    def install_requirements(self, req_file: str) -> InstallResult:
        """Install from a requirements file."""
        ...

    def install_from_lockfile(self) -> Optional[InstallResult]:
        """
        Install from lockfile if supported (uv sync, poetry install, etc.).
        Return None if this manager doesn't use lockfiles.
        """
        return None  # Default: no lockfile support

    def _run(self, cmd: list[str]) -> InstallResult:
        """Execute a command and return structured result."""
        t0 = time.monotonic()
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return InstallResult(self.name, True, time.monotonic() - t0, " ".join(cmd))
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            return InstallResult(
                self.name, False, time.monotonic() - t0, " ".join(cmd), error_msg
            )
