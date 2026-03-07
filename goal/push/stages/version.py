"""Push workflow stages - version handling."""

from pathlib import Path
from typing import List, Optional, Any, Dict

import click


def _get_version_module():
    """Lazy import version functions to avoid circular imports."""
    try:
        from ....cli.version import get_current_version, bump_version, sync_all_versions
    except ImportError:
        from goal.cli.version import get_current_version, bump_version, sync_all_versions
    return get_current_version, bump_version, sync_all_versions


def sync_all_versions_wrapper(new_version: str, user_config: Optional[Dict]) -> List[str]:
    """Wrapper to sync versions to all project files."""
    _, _, sync_all_versions = _get_version_module()
    return sync_all_versions(new_version, user_config)


def handle_version_sync(
    new_version: str,
    no_version_sync: bool,
    user_config: Optional[Dict],
    yes: bool
) -> None:
    """Sync versions to all project files."""
    _, _, sync_all_versions = _get_version_module()
    
    if not no_version_sync:
        updated_files = sync_all_versions(new_version, user_config)
        # Lazy import to avoid circular dependency
        try:
            from ..core import run_git_local
        except ImportError:
            from goal.push.core import run_git_local
        for f in updated_files:
            run_git_local('add', f)
            click.echo(click.style(f"✓ Updated {f} to {new_version}", fg='green'))
    else:
        Path('VERSION').write_text(new_version + '\n')
        # Lazy import to avoid circular dependency
        try:
            from ..core import run_git_local
        except ImportError:
            from goal.push.core import run_git_local
        run_git_local('add', 'VERSION')
        click.echo(click.style(f"✓ Updated VERSION to {new_version}", fg='green'))


def get_version_info(current_version: Optional[str] = None, bump: str = 'patch') -> tuple:
    """Get current and new version info."""
    get_current_version, bump_version, _ = _get_version_module()
    if current_version is None:
        current_version = get_current_version()
    new_version = bump_version(current_version, bump)
    return current_version, new_version
