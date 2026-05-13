"""Version management functions - extracted from cli.py.

This module provides a shim for backward compatibility after splitting
into version_types.py, version_utils.py, and version_sync.py.
"""

# Re-export everything from the split modules
from .version_types import PROJECT_TYPES
from .version_utils import (
    detect_project_types,
    find_version_files,
    get_version_from_file,
    get_current_version,
    bump_version,
    update_version_in_file,
    update_json_version,
    update_project_metadata,
    update_readme_metadata,
)
from .version_sync import sync_all_versions

# Make all re-exported names available in __all__
__all__ = [
    "PROJECT_TYPES",
    "detect_project_types",
    "find_version_files",
    "get_version_from_file",
    "get_current_version",
    "bump_version",
    "update_version_in_file",
    "update_json_version",
    "update_project_metadata",
    "update_readme_metadata",
    "sync_all_versions",
]
