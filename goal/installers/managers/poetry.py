"""Poetry package manager."""

from typing import Optional
from goal.installers.managers.base import AbstractPackageManager, InstallResult


class PoetryManager(AbstractPackageManager):
    """Poetry package manager implementation."""
    
    name = "poetry"
    priority = 30
    binary = "poetry"
    
    def install_editable(self, extras: list[str]) -> InstallResult:
        """Install package using poetry."""
        # Poetry handles extras via install command
        if extras:
            extras_str = ",".join(extras)
            cmd = ["poetry", "install", "--extras", extras_str]
        else:
            cmd = ["poetry", "install"]
        return self._run(cmd)
    
    def install_requirements(self, req_file: str) -> InstallResult:
        """Poetry doesn't use requirements.txt directly - convert needed."""
        # Poetry uses pyproject.toml, not requirements.txt
        # Fallback to regular install
        return self._run(["poetry", "install"])
    
    def install_from_lockfile(self) -> Optional[InstallResult]:
        """Install from poetry.lock."""
        return self._run(["poetry", "install"])
