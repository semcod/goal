"""PDM package manager."""

from typing import Optional
from goal.installers.managers.base import AbstractPackageManager, InstallResult


class PdmManager(AbstractPackageManager):
    """PDM package manager implementation."""
    
    name = "pdm"
    priority = 20  # Between uv (10) and poetry (30)
    binary = "pdm"
    
    def install_editable(self, extras: list[str]) -> InstallResult:
        """Install package using PDM."""
        if extras:
            extras_str = ",".join(extras)
            cmd = ["pdm", "install", "-G", extras_str]
        else:
            cmd = ["pdm", "install"]
        return self._run(cmd)
    
    def install_requirements(self, req_file: str) -> InstallResult:
        """PDM can import from requirements."""
        return self._run(["pdm", "import", req_file])
    
    def install_from_lockfile(self) -> Optional[InstallResult]:
        """Install from pdm.lock."""
        return self._run(["pdm", "sync"])
