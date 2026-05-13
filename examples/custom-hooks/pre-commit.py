#!/usr/bin/env python3
"""
Pre-commit hook example for Goal.

This hook runs security checks before allowing commits.
"""

import sys
import subprocess
import re
from pathlib import Path


def check_secrets():
    """Check for potential secrets in staged files."""
    # Get staged files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )

    staged_files = result.stdout.strip().split("\n") if result.stdout else []

    # Patterns to check
    secret_patterns = [
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        (r"[0-9a-f]{40}", "Generic secret (40 hex chars)"),
    ]

    issues = []

    for file_path in staged_files:
        path = Path(file_path)
        if not path.exists() or path.is_dir():
            continue

        try:
            content = path.read_text(errors="ignore")
            for pattern, name in secret_patterns:
                if re.search(pattern, content):
                    issues.append(f"  ⚠ Potential {name} in {file_path}")
        except Exception:
            pass

    return issues


def check_file_sizes(max_size_mb=10):
    """Check that no file exceeds size limit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )

    staged_files = result.stdout.strip().split("\n") if result.stdout else []
    max_bytes = max_size_mb * 1024 * 1024

    issues = []

    for file_path in staged_files:
        path = Path(file_path)
        if path.exists() and path.stat().st_size > max_bytes:
            size_mb = path.stat().st_size / 1024 / 1024
            issues.append(f"  ⚠ {file_path}: {size_mb:.1f}MB > {max_size_mb}MB limit")

    return issues


def run_tests():
    """Run quick tests before commit."""
    result = subprocess.run(
        ["python3", "-m", "pytest", "-x", "-q"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        return ["  ⚠ Tests failed - run 'pytest' to see details"]

    return []


def main():
    """Run all pre-commit checks."""
    print("🔍 Running pre-commit checks...")

    all_issues = []

    # Check 1: Secrets
    print("\n1. Checking for secrets...")
    issues = check_secrets()
    if issues:
        all_issues.extend(issues)
        print("\n".join(issues))
    else:
        print("  ✓ No secrets detected")

    # Check 2: File sizes
    print("\n2. Checking file sizes...")
    issues = check_file_sizes(max_size_mb=10)
    if issues:
        all_issues.extend(issues)
        print("\n".join(issues))
    else:
        print("  ✓ All files under size limit")

    # Check 3: Quick tests (optional)
    print("\n3. Running quick tests...")
    issues = run_tests()
    if issues:
        all_issues.extend(issues)
        print("\n".join(issues))
    else:
        print("  ✓ Tests passed")

    # Summary
    if all_issues:
        print(f"\n❌ Pre-commit checks failed ({len(all_issues)} issues)")
        print("\nFix the issues above or use --force to bypass")
        return 1

    print("\n✅ All pre-commit checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
