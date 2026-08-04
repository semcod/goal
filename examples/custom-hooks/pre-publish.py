#!/usr/bin/env python3
"""
Pre-publish hook example for Goal.

Validates package before publishing to registry.
"""

import sys
import subprocess
import tempfile
from pathlib import Path


def test_build():
    """Test that package builds correctly."""
    print("1. Testing package build...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Build package
        result = subprocess.run(
            ["python", "-m", "build", "--outdir", tmpdir],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("  ✗ Build failed")
            print(result.stderr)
            return False

        print("  ✓ Package builds successfully")

        # Check wheel exists
        wheels = list(Path(tmpdir).glob("*.whl"))
        if not wheels:
            print("  ✗ No wheel produced")
            return False

        print(f"  ✓ Wheel created: {wheels[0].name}")
        return True


def test_install():
    """Test package installation in clean environment."""
    print("\n2. Testing package installation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create clean venv
        venv_path = Path(tmpdir) / "venv"
        result = subprocess.run(
            ["python", "-m", "venv", str(venv_path)], capture_output=True, text=True
        )

        if result.returncode != 0:
            print("  ✗ Failed to create test venv")
            return False

        # Build and install
        build_result = subprocess.run(
            ["python", "-m", "build", "--wheel", "--outdir", tmpdir],
            capture_output=True,
            text=True,
        )

        if build_result.returncode != 0:
            print("  ✗ Build failed")
            return False

        wheel = list(Path(tmpdir).glob("*.whl"))[0]
        pip = venv_path / "bin" / "pip"

        result = subprocess.run(
            [str(pip), "install", str(wheel)], capture_output=True, text=True
        )

        if result.returncode != 0:
            print("  ✗ Installation failed")
            print(result.stderr)
            return False

        print("  ✓ Package installs cleanly")
        return True


def check_version():
    """Verify version is not already published."""
    print("\n3. Checking version uniqueness...")

    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        package_name = config.get("project", {}).get("name")
        version = config.get("project", {}).get("version")

        if not package_name or not version:
            print("  ⚠ Could not determine package name/version")
            return True

        # Check PyPI
        import urllib.request

        url = f"https://pypi.org/pypi/{package_name}/{version}/json"

        try:
            urllib.request.urlopen(url, timeout=10)
            print(f"  ✗ Version {version} already exists on PyPI")
            return False
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  ✓ Version {version} is new")
                return True
            raise

    except Exception as e:
        print(f"  ⚠ Could not check version: {e}")
        return True


def run_security_check():
    """Run security checks on package."""
    print("\n4. Running security checks...")

    # Check for known vulnerabilities
    result = subprocess.run(["pip", "audit"], capture_output=True, text=True)

    if result.returncode != 0:
        print("  ⚠ Security issues found:")
        print(result.stdout)
        # Don't fail, just warn
    else:
        print("  ✓ No known vulnerabilities")

    return True


def main():
    """Run all pre-publish checks."""
    print("📦 Running pre-publish validation...\n")

    checks = [
        test_build,
        test_install,
        check_version,
        run_security_check,
    ]

    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"  ✗ Check failed with error: {e}")
            results.append(False)

    if all(results):
        print("\n✅ All pre-publish checks passed! Ready to publish.")
        return 0
    else:
        print("\n❌ Some checks failed. Fix issues before publishing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
