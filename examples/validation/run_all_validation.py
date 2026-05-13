#!/usr/bin/env python3
"""
Runs all example validation tests.

This is the main entry point for validating examples directory.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
import time


class ValidationRunner:
    """Runs all validation tests and aggregates results."""

    def __init__(self, validation_dir: Path):
        self.validation_dir = validation_dir
        self.results: List[Tuple[str, bool, str, float]] = []

    def run_test(self, script_name: str, description: str) -> bool:
        """Run a single validation test."""
        script_path = self.validation_dir / script_name

        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            self.results.append((description, False, "Script not found", 0))
            return False

        print(f"\n{'=' * 70}")
        print(f"Running: {description}")
        print("=" * 70)

        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=False,  # Let output go to terminal
                text=True,
                timeout=120,
            )
            elapsed = time.time() - start

            success = result.returncode == 0
            status = "✅ PASSED" if success else "❌ FAILED"

            self.results.append((description, success, status, elapsed))
            return success

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            self.results.append((description, False, "⏱️  TIMEOUT", elapsed))
            return False
        except Exception as e:
            elapsed = time.time() - start
            self.results.append((description, False, f"💥 ERROR: {e}", elapsed))
            return False

    def run_all(self) -> bool:
        """Run all validation tests."""
        tests = [
            ("test_syntax_check.py", "Syntax Check"),
            ("test_imports.py", "Import Validation"),
            ("test_api_signatures.py", "API Signature Check"),
            ("test_readme_consistency.py", "README Consistency"),
        ]

        print("=" * 70)
        print("EXAMPLE VALIDATION SUITE")
        print("=" * 70)
        print(f"Validation directory: {self.validation_dir}")
        print(f"Tests to run: {len(tests)}")

        all_passed = True
        for script, description in tests:
            if not self.run_test(script, description):
                all_passed = False

        return all_passed

    def print_summary(self):
        """Print final summary report."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)

        passed = sum(1 for _, success, _, _ in self.results if success)
        failed = len(self.results) - passed

        print(f"\nTotal tests: {len(self.results)}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")

        print("\nDetails:")
        for desc, success, status, elapsed in self.results:
            icon = "✅" if success else "❌"
            print(f"  {icon} {desc}: {status} ({elapsed:.1f}s)")

        if failed > 0:
            print("\n⚠️  Some tests failed. Fix the issues before releasing.")
        else:
            print("\n✅ All tests passed! Examples are in good shape.")

        print("\n" + "=" * 70)


def main():
    """Run all validations."""
    script_dir = Path(__file__).parent

    runner = ValidationRunner(script_dir)
    all_passed = runner.run_all()
    runner.print_summary()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
