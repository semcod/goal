"""Package manager broker - intelligently selects and executes installations."""

from pathlib import Path
from typing import Optional
from goal.installers.managers.base import AbstractPackageManager, InstallResult
from goal.installers.managers.uv import UvManager
from goal.installers.managers.pdm import PdmManager
from goal.installers.managers.poetry import PoetryManager
from goal.installers.managers.pip import PipManager
import click

# Registry of managers sorted by priority (lower = better)
_MANAGERS: list[AbstractPackageManager] = [
    UvManager(),       # priority=10  (~5-30s)
    PdmManager(),      # priority=20  (~30-60s)
    PoetryManager(),   # priority=30  (~60-120s)
    PipManager(),      # priority=100 (~120-600s) - always available
]

# Lockfile to manager mapping
_LOCKFILE_MANAGERS = {
    'uv.lock': 'uv',
    'poetry.lock': 'poetry', 
    'pdm.lock': 'pdm',
    'requirements.txt': 'pip',
    'requirements-dev.txt': 'pip',
}


class PackageManagerBroker:
    """
    Intelligent package manager broker.
    Detects available managers, selects the fastest, executes installation.
    """
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
        self._available: Optional[list[AbstractPackageManager]] = None
    
    def detect_available(self) -> list[AbstractPackageManager]:
        """Return available managers sorted by priority."""
        if self._available is None:
            self._available = sorted(
                [m for m in _MANAGERS if m.is_available()],
                key=lambda m: m.priority
            )
        return self._available
    
    def install(
        self,
        extras: Optional[list[str]] = None,
        prefer: Optional[str] = None,
        auto_install_uv: bool = True,
        use_lockfile: bool = True,
    ) -> InstallResult:
        """
        Main installation method.
        
        Args:
            extras: Optional dependency groups (e.g., ["dev", "mcp"])
            prefer: Force specific manager ("uv", "pip", ...)
            auto_install_uv: If True and uv unavailable, install it
            use_lockfile: If True and lockfile exists, use lockfile-based install
        """
        available = self.detect_available()
        
        # Auto-install uv if missing and pip is available
        if auto_install_uv and not any(m.name == "uv" for m in available):
            click.echo("⚡ Installing uv for faster package management...")
            UvManager().install_self()
            self._available = None  # Reset cache
            available = self.detect_available()
        
        # Select manager
        manager = self._select_manager(available, prefer)
        if not manager:
            raise RuntimeError("No package manager available!")
        
        # Check for lockfile-based install
        if use_lockfile:
            lockfile_result = manager.install_from_lockfile()
            if lockfile_result:
                click.echo(f"📦 Installing via {manager.name} (lockfile)...")
                self._report(lockfile_result, available)
                return lockfile_result
        
        click.echo(f"📦 Installing via {manager.name} (priority={manager.priority})...")
        result = manager.install_editable(extras or [])
        self._report(result, available)
        return result
    
    def _select_manager(
        self, 
        available: list[AbstractPackageManager], 
        prefer: Optional[str]
    ) -> Optional[AbstractPackageManager]:
        """Select appropriate manager based on preference or priority."""
        if prefer:
            return next((m for m in available if m.name == prefer), None)
        return available[0] if available else None
    
    def _report(
        self, 
        result: InstallResult, 
        available: list[AbstractPackageManager]
    ) -> None:
        """Report installation result."""
        status = "✅" if result.success else "❌"
        others = [m.name for m in available if m.name != result.manager]
        fallback_info = f" | fallback: {', '.join(others)}" if others else ""
        click.echo(
            f"{status} {result.manager} ({result.duration_s:.1f}s){fallback_info}"
        )
        if not result.success and result.error:
            click.echo(f"   Error: {result.error}", err=True)

    def detect_lockfile(self) -> Optional[str]:
        """Detect which lockfile exists in project directory."""
        project = Path(self.project_dir)
        for lockfile, manager in _LOCKFILE_MANAGERS.items():
            if (project / lockfile).exists():
                return lockfile
        return None

    def install_smart(
        self,
        extras: Optional[list[str]] = None,
        auto_install_uv: bool = True,
    ) -> InstallResult:
        """
        Smart installation that picks best method based on lockfile detection.
        
        Priority:
        1. Use manager matching existing lockfile (uv.lock → uv sync, etc.)
        2. Use fastest available manager for editable install
        """
        lockfile = self.detect_lockfile()
        if lockfile:
            prefer = _LOCKFILE_MANAGERS[lockfile]
            click.echo(f"🔒 Detected {lockfile} → using {prefer}")
            return self.install(extras=extras, prefer=prefer, auto_install_uv=auto_install_uv)
        
        # No lockfile - use fastest available
        return self.install(extras=extras, prefer=None, auto_install_uv=auto_install_uv)

    def show_available(self) -> None:
        """Display available package managers with indicators."""
        available = self.detect_available()
        lockfile = self.detect_lockfile()
        
        click.echo("📦 Available package managers:")
        for m in available:
            speed = "⚡ fast" if m.priority < 50 else "🐢 slow"
            indicator = "✓" if m == available[0] else " "
            lock_match = "🔒" if lockfile and _LOCKFILE_MANAGERS.get(lockfile) == m.name else ""
            click.echo(f"   {indicator} {m.name:8} {speed:8} {lock_match}")
