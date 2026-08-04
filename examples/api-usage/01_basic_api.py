"""
Basic API usage example for Goal.

This example shows how to use Goal's Python API for common operations.
"""

import sys
from pathlib import Path

# Add goal to path (adjust as needed)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from goal.doctor.core import diagnose_and_report
from goal.cli.version import get_current_version, detect_project_types
from goal.config import ensure_config
from goal.user_config import get_user_config


def main():
    """Run basic API examples."""
    print("=" * 60)
    print("Goal API - Basic Usage Example")
    print("=" * 60)

    # 1. Detect project types
    print("\n1. Detecting project types...")
    project_types = detect_project_types()
    print(f"   Found: {', '.join(project_types) if project_types else 'None'}")

    # 2. Get current version
    print("\n2. Getting current version...")
    version = get_current_version()
    print(f"   Version: {version}")

    # 3. Load configuration
    print("\n3. Loading configuration...")
    try:
        config = ensure_config()
        print(
            f"   Project: {config.project.name if hasattr(config, 'project') else 'N/A'}"
        )
    except Exception as e:
        print(f"   Config error: {e}")

    # 4. Get user config
    print("\n4. Loading user configuration...")
    try:
        user = get_user_config()
        if user and user.is_initialized():
            print(f"   Author: {user.get('author_name', 'Not set')}")
            print(f"   Email: {user.get('author_email', 'Not set')}")
        else:
            print("   No user config found or not initialized")
    except Exception as e:
        print(f"   Could not load user config: {e}")

    # 5. Diagnose project (if in a project)
    print("\n5. Running diagnostics...")
    if project_types:
        for ptype in project_types[:1]:  # Just first type
            report = diagnose_and_report(Path("."), ptype, auto_fix=False)
            print(f"   {ptype}: {len(report.issues)} issues")
            for issue in report.issues[:3]:  # Show first 3
                print(f"     - {issue.title} ({issue.severity})")
    else:
        print("   No project to diagnose")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
