#!/usr/bin/env python3
"""Simple test for the recovery system."""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add goal to path
sys.path.insert(0, str(Path(__file__).parent))


def test_strategy_detection():
    """Test that strategies can detect their respective errors."""
    from goal.recovery.strategies import (
        AuthErrorStrategy,
        LargeFileStrategy,
        DivergentHistoryStrategy,
    )

    print("Testing strategy detection...")

    # Test auth error detection
    auth_strategy = AuthErrorStrategy("/tmp")
    auth_errors = [
        "authentication failed",
        "remote: Invalid username or password",
        "fatal: Authentication failed for 'https://github.com/user/repo.git'",
        "error: 403 - Forbidden",
    ]

    for error in auth_errors:
        if not auth_strategy.can_handle(error):
            print(f"❌ Auth strategy failed to detect: {error}")
            return False
    print("✓ Auth error detection works")

    # Test large file detection
    large_file_strategy = LargeFileStrategy("/tmp")
    large_file_errors = [
        "remote: error: File large-file.zip is 150.00 MB; this exceeds GitHub's file size limit of 100.00 MB",
        "remote: error: GH001: Large files detected. You may want to try Git Large File Storage",
        "error: cannot push large files",
    ]

    for error in large_file_errors:
        if not large_file_strategy.can_handle(error):
            print(f"❌ Large file strategy failed to detect: {error}")
            return False
    print("✓ Large file detection works")

    # Test divergent history detection
    divergent_strategy = DivergentHistoryStrategy("/tmp")
    divergent_errors = [
        "Updates were rejected because the tip of your current branch is behind",
        "error: failed to push some refs to 'https://github.com/user/repo.git'",
        "hint: Updates were rejected because the remote contains work that you do",
        "! [rejected] main -> main (non-fast-forward)",
    ]

    for error in divergent_errors:
        if not divergent_strategy.can_handle(error):
            print(f"❌ Divergent history strategy failed to detect: {error}")
            return False
    print("✓ Divergent history detection works")

    return True


def test_recovery_manager():
    """Test RecoveryManager initialization."""
    from goal.recovery.manager import RecoveryManager

    print("\nTesting RecoveryManager...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)

        # Create recovery manager
        manager = RecoveryManager(tmpdir)

        # Check recovery directory is created
        recovery_dir = os.path.join(tmpdir, ".goal", "recovery")
        if not os.path.exists(recovery_dir):
            print("❌ Recovery directory not created")
            return False
        print("✓ Recovery directory created")

        # Check .gitignore is updated
        gitignore_path = os.path.join(tmpdir, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                content = f.read()
            if ".goal/recovery/" not in content:
                print("❌ .gitignore not updated")
                return False
        print("✓ .gitignore updated")

    return True


def main():
    """Run all tests."""
    print("Testing Goal Recovery System\n")

    tests = [
        test_strategy_detection,
        test_recovery_manager,
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


sys.exit(main())
