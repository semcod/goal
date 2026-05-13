"""
Version validation example.

Shows how to validate versions across registries.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from goal.version_validation import (
    validate_project_versions,
    check_readme_badges,
    get_pypi_version,
)
from goal.cli.version import get_current_version, detect_project_types


def main():
    """Demonstrate version validation."""
    print("=" * 60)
    print("Goal API - Version Validation")
    print("=" * 60)

    # Get current version
    print("\n1. Current version:")
    current = get_current_version()
    print(f"   Local: {current}")

    # Check PyPI for goal itself
    print("\n2. Checking PyPI (goal package):")
    latest = get_pypi_version("goal")
    if latest:
        status = (
            "✓ up to date" if latest == current else f"⚠ update available (v{latest})"
        )
        print(f"   Registry: v{latest}")
        print(f"   Status: {status}")
    else:
        print("   ✗ Could not fetch from PyPI")

    # Detect project types and validate
    print("\n3. Project type validation:")
    project_types = detect_project_types()
    if project_types:
        results = validate_project_versions(project_types, current)
        for ptype, result in results.items():
            registry = result.get("registry_version", "N/A")
            is_latest = result.get("is_latest", False)
            error = result.get("error")

            if error:
                print(f"   {ptype}: ⚠ {error}")
            elif is_latest:
                print(f"   {ptype}: ✓ up to date ({current})")
            else:
                print(f"   {ptype}: ⚠ {current} → {registry}")
    else:
        print("   No project types detected")

    # Check README badges
    print("\n4. README badge check:")
    badge_info = check_readme_badges(current)
    if badge_info["exists"]:
        print(f"   Badges found: {len(badge_info['badges'])}")
        for badge in badge_info["badges"][:3]:
            status = "✓" if not badge["needs_update"] else "⚠"
            print(f"   {status} {badge['url'][:50]}...")
        if badge_info["needs_update"]:
            print(f"   ⚠ Some badges need update to {current}")
    else:
        print(f"   ✗ {badge_info['message']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
