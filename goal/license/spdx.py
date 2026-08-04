"""SPDX license identifier validation and information."""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Cache of SPDX license data
_SPDX_DATA: Optional[Dict] = None

# Basic license compatibility matrix
# Format: license_id -> [compatible licenses]
_COMPATIBILITY_MATRIX = {
    "MIT": ["MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC", "0BSD"],
    "BSD-3-Clause": ["MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC"],
    "BSD-2-Clause": ["MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC"],
    "Apache-2.0": ["MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC", "0BSD"],
    "ISC": ["MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC", "0BSD"],
    "0BSD": ["MIT", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0", "ISC", "0BSD"],
    "LGPL-2.1": ["LGPL-2.1", "LGPL-3.0", "GPL-2.0", "GPL-3.0"],
    "LGPL-3.0": ["LGPL-2.1", "LGPL-3.0", "GPL-2.0", "GPL-3.0"],
    "GPL-2.0": ["GPL-2.0", "GPL-3.0"],
    "GPL-3.0": ["GPL-2.0", "GPL-3.0"],
    "AGPL-3.0": ["AGPL-3.0"],
}

# Copyleft licenses that require source disclosure
_COPYLEFT_LICENSES = ["GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0"]

# Permissive licenses
_PERMISSIVE_LICENSES = [
    "MIT",
    "BSD-3-Clause",
    "BSD-2-Clause",
    "Apache-2.0",
    "ISC",
    "0BSD",
    "Unlicense",
]


def _load_spdx_data() -> Dict:
    """Load SPDX license data from bundled file or fetch from SPDX."""
    global _SPDX_DATA

    if _SPDX_DATA is not None:
        return _SPDX_DATA

    # Try to load bundled data first
    bundled_file = Path(__file__).parent / "data" / "licenses.json"
    if bundled_file.exists():
        try:
            with open(bundled_file, "r") as f:
                _SPDX_DATA = json.load(f)
            return _SPDX_DATA
        except Exception:
            pass

    # Fallback to minimal data if no bundled file
    _SPDX_DATA = {
        "licenses": [
            {"licenseId": "MIT", "name": "MIT License", "isDeprecatedLicenseId": False},
            {
                "licenseId": "Apache-2.0",
                "name": "Apache License 2.0",
                "isDeprecatedLicenseId": False,
            },
            {
                "licenseId": "GPL-3.0",
                "name": "GNU General Public License v3.0",
                "isDeprecatedLicenseId": False,
            },
            {
                "licenseId": "BSD-3-Clause",
                "name": "BSD 3-Clause License",
                "isDeprecatedLicenseId": False,
            },
            {"licenseId": "ISC", "name": "ISC License", "isDeprecatedLicenseId": False},
            {
                "licenseId": "LGPL-3.0",
                "name": "GNU Lesser General Public License v3.0",
                "isDeprecatedLicenseId": False,
            },
            {
                "licenseId": "AGPL-3.0",
                "name": "GNU Affero General Public License v3.0",
                "isDeprecatedLicenseId": False,
            },
            {
                "licenseId": "BSD-2-Clause",
                "name": "BSD 2-Clause License",
                "isDeprecatedLicenseId": False,
            },
            {
                "licenseId": "0BSD",
                "name": "BSD Zero Clause License",
                "isDeprecatedLicenseId": False,
            },
            {
                "licenseId": "Unlicense",
                "name": "The Unlicense",
                "isDeprecatedLicenseId": False,
            },
        ]
    }

    return _SPDX_DATA


def validate_spdx_id(license_id: str) -> Tuple[bool, str]:
    """Validate an SPDX license identifier.

    Args:
        license_id: The SPDX license ID to validate

    Returns:
        Tuple of (is_valid, error_message_or_license_name)
    """
    if not license_id:
        return False, "License ID cannot be empty"

    # Handle special cases
    if license_id.upper() == "NONE":
        return True, "No license (proprietary)"
    elif license_id.upper() == "ALL-RESERVED":
        return True, "All rights reserved"

    # Check if it's a valid SPDX ID
    data = _load_spdx_data()
    for license_info in data.get("licenses", []):
        if license_info["licenseId"] == license_id:
            if license_info.get("isDeprecatedLicenseId", False):
                return False, f"License ID '{license_id}' is deprecated"
            return True, license_info.get("name", license_id)

    # Check for common typos
    suggestions = []
    for license_info in data.get("licenses", []):
        if (
            license_id.lower() in license_info["licenseId"].lower()
            or license_info["licenseId"].lower() in license_id.lower()
        ):
            suggestions.append(license_info["licenseId"])

    if suggestions:
        return (
            False,
            f"Invalid license ID '{license_id}'. Did you mean: {', '.join(suggestions[:3])}?",
        )

    return False, f"Invalid license ID '{license_id}'"


def get_license_info(license_id: str) -> Optional[Dict]:
    """Get detailed information about a license.

    Args:
        license_id: The SPDX license ID

    Returns:
        Dictionary with license information or None if not found
    """
    data = _load_spdx_data()
    for license_info in data.get("licenses", []):
        if license_info["licenseId"] == license_id:
            return {
                "id": license_info["licenseId"],
                "name": license_info.get("name", license_id),
                "is_deprecated": license_info.get("isDeprecatedLicenseId", False),
                "is_copyleft": license_id in _COPYLEFT_LICENSES,
                "is_permissive": license_id in _PERMISSIVE_LICENSES,
                "category": "copyleft"
                if license_id in _COPYLEFT_LICENSES
                else "permissive",
            }
    return None


def check_compatibility(license1: str, license2: str) -> Tuple[bool, str]:
    """Check basic license compatibility between two licenses.

    This is a simplified compatibility check. Real license compatibility
    is complex and depends on many factors.

    Args:
        license1: First SPDX license ID
        license2: Second SPDX license ID

    Returns:
        Tuple of (is_compatible, explanation)
    """
    # Handle special cases
    if license1.upper() in ["NONE", "ALL-RESERVED"] or license2.upper() in [
        "NONE",
        "ALL-RESERVED",
    ]:
        return (
            False,
            "Proprietary licenses are generally not compatible with open source licenses",
        )

    # Validate both licenses
    valid1, msg1 = validate_spdx_id(license1)
    valid2, msg2 = validate_spdx_id(license2)

    if not valid1:
        return False, f"Invalid license 1: {msg1}"
    if not valid2:
        return False, f"Invalid license 2: {msg2}"

    # Same licenses are always compatible
    if license1 == license2:
        return True, f"Same license ({license1}) is always compatible"

    # Check compatibility matrix
    compatible = _COMPATIBILITY_MATRIX.get(license1, [])
    if license2 in compatible:
        return True, f"{license1} is compatible with {license2}"

    # Check reverse compatibility
    compatible = _COMPATIBILITY_MATRIX.get(license2, [])
    if license1 in compatible:
        return True, f"{license2} is compatible with {license1}"

    # Special cases
    info1 = get_license_info(license1)
    info2 = get_license_info(license2)

    if info1 and info2:
        if info1["is_copyleft"] and info2["is_permissive"]:
            return (
                False,
                f"Copyleft license {license1} may not be compatible with permissive license {license2}",
            )
        elif info2["is_copyleft"] and info1["is_permissive"]:
            return (
                False,
                f"Copyleft license {license2} may not be compatible with permissive license {license1}",
            )

    return (
        False,
        f"Compatibility between {license1} and {license2} is uncertain. Consult legal advice.",
    )


def get_compatible_licenses(license_id: str) -> List[str]:
    """Get a list of licenses compatible with the given license.

    Args:
        license_id: The SPDX license ID

    Returns:
        List of compatible license IDs
    """
    if license_id.upper() in ["NONE", "ALL-RESERVED"]:
        return []

    compatible = _COMPATIBILITY_MATRIX.get(license_id, [])
    return sorted(compatible)


def is_copyleft(license_id: str) -> bool:
    """Check if a license is copyleft.

    Args:
        license_id: The SPDX license ID

    Returns:
        True if the license is copyleft
    """
    return license_id in _COPYLEFT_LICENSES


def is_permissive(license_id: str) -> bool:
    """Check if a license is permissive.

    Args:
        license_id: The SPDX license ID

    Returns:
        True if the license is permissive
    """
    return license_id in _PERMISSIVE_LICENSES
