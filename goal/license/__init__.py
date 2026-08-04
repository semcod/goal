"""License management module for Goal.

Provides functionality for:
- License template management
- Automatic LICENSE file creation/update
- SPDX license identifier validation
- License compatibility checking
"""

from .manager import LicenseManager, create_license_file, update_license_file
from .spdx import validate_spdx_id, get_license_info, check_compatibility

__all__ = [
    "LicenseManager",
    "create_license_file",
    "update_license_file",
    "validate_spdx_id",
    "get_license_info",
    "check_compatibility",
]
