"""UV package manager - fastest Python package manager."""

from pathlib import Path
from typing import Optional

from goal.installers.managers.base import AbstractPackageManager, InstallResult
from goal.package_managers import get_uv_dependency_flags


class UvManager(AbstractPackageManager):
    """UV package manager implementation."""

    name = "uv"
    priority = 10  # Highest priority - fastest
    binary = "uv"

    def install_editable(self, extras: list[str]) -> InstallResult:
        """Install package in editable mode with optional extras."""
        if extras:
            extras_str = ",".join(extras)
            cmd = ["uv", "pip", "install", "-e", f".[{extras_str}]"]
        else:
            cmd = ["uv", "pip", "install", "-e", "."]
        return self._run(cmd)

    def install_requirements(self, req_file: str) -> InstallResult:
        """Install from requirements file."""
        return self._run(["uv", "pip", "install", "-r", req_file])

    def sync_lockfile(self, extras: Optional[list[str]] = None) -> InstallResult:
        """Sync dependencies from uv.lock (fastest method)."""
        command = ["uv", "sync"]
        command.extend(get_uv_dependency_flags(Path(self.project_dir), extras or []))
        return self._run(command)

    def install_self(self) -> InstallResult:
        """Install uv itself using pip."""
        return self._run(["pip", "install", "uv", "--quiet"])

    def install_from_lockfile(
        self, extras: Optional[list[str]] = None
    ) -> Optional[InstallResult]:
        """Sync from uv.lock - fastest reproducible install."""
        return self.sync_lockfile(extras)
