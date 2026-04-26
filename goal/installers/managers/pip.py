"""Pip package manager - universal fallback."""

from goal.installers.managers.base import AbstractPackageManager, InstallResult


class PipManager(AbstractPackageManager):
    """Pip package manager implementation - always available fallback."""
    
    name = "pip"
    priority = 100  # Lowest priority - slow but always available
    binary = "pip"
    
    def is_available(self) -> bool:
        """Pip is always considered available (python -m pip)."""
        return True
    
    def install_editable(self, extras: list[str]) -> InstallResult:
        """Install package in editable mode with optional extras."""
        if extras:
            extras_str = ",".join(extras)
            cmd = ["pip", "install", "-e", f".[{extras_str}]"]
        else:
            cmd = ["pip", "install", "-e", "."]
        return self._run(cmd)
    
    def install_requirements(self, req_file: str) -> InstallResult:
        """Install from requirements file."""
        return self._run(["pip", "install", "-r", req_file])
