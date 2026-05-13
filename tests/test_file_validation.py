#!/usr/bin/env python3
"""Test script for file validation functionality."""

import os
import tempfile
import sys
from pathlib import Path

# Add goal to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from goal.validators.file_validator import (
    validate_files,
    FileSizeError,
    TokenDetectedError,
)
from goal.config import GoalConfig


def test_file_size_validation():
    """Test file size validation."""
    print("Testing file size validation...")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        # Create a file larger than 10MB (using zeros)
        f.write("0" * (11 * 1024 * 1024))  # 11MB
        large_file = f.name

    try:
        # Should raise FileSizeError
        validate_files([large_file], max_size_mb=10.0, auto_handle_large=False)
        print("❌ File size validation failed - should have raised error")
        assert False, "Expected FileSizeError"
    except FileSizeError as e:
        print(f"✅ File size validation works: {e}")
        assert True
    finally:
        os.unlink(large_file)


def test_token_detection():
    """Test API token detection."""
    print("\nTesting API token detection...")

    test_cases = [
        # Tokens must match the regex pattern lengths AND have high entropy
        # Use mixed case + digits for high entropy (real secret-like)
        (
            "github_token.txt",
            "ghp_" + "aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890Ab",
            "GitHub Personal Access",
        ),
        ("aws_key.txt", "AKIA" + "IOSFODNN7EXAMPLEX", "AWS Access Key"),
        (
            "slack_bot.txt",
            "xoxb-1234567890123-1234567890123-" + "aBcDeFgHiJkLmNoPqRsTuVwXy",
            "Slack Bot",
        ),
        (
            "generic_token.txt",
            "Bearer Abcdef1234567890Abcdef1234567890Abcdef",
            "Bearer Token",
        ),
    ]

    for filename, content, expected_type in test_cases:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", prefix=filename
        ) as f:
            f.write(content)
            test_file = f.name

        try:
            validate_files([test_file], detect_tokens=True, auto_handle_large=False)
            print(f"❌ Token detection failed for {expected_type}")
            assert False, f"Expected TokenDetectedError for {expected_type}"
        except TokenDetectedError as e:
            if expected_type in str(e):
                print(f"✅ Token detection works for {expected_type}")
                assert True
            else:
                print(f"❌ Wrong token type detected: {e}")
                assert False, f"Wrong token type: {e}"
        finally:
            os.unlink(test_file)


def test_safe_files():
    """Test that safe files pass validation."""
    print("\nTesting safe files...")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        f.write("""
# Normal Python code
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
""")
        safe_file = f.name

    try:
        validate_files(
            [safe_file], max_size_mb=10.0, detect_tokens=True, auto_handle_large=False
        )
        print("✅ Safe files pass validation")
        assert True
    except Exception as e:
        print(f"❌ Safe file validation failed: {e}")
        assert False, f"Safe file failed: {e}"
    finally:
        os.unlink(safe_file)


def test_false_positive_prevention():
    """Test that legitimate code doesn't trigger false positives."""
    print("\nTesting false positive prevention...")

    test_cases = [
        # Long lowercase parameter names should NOT trigger
        ("param_test.txt", "enable_image_optimization=enable_image_optimization"),
        ("param_test2.txt", "some_long_parameter_name=another_long_value"),
        # Regular assignment to lowercase var should NOT trigger
        ("var_test.txt", "my_variable=some_value_here"),
        # Documentation examples with "Token" should NOT trigger (has spaces)
        ("readme_example.txt", "Token can be obtained from your account settings"),
        # Placeholder examples should NOT trigger
        (
            "placeholder.txt",
            "OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        ),
        # Bearer with short value should NOT trigger
        ("short_bearer.txt", "Bearer token123"),
        # Generic Python constants (no secret keyword) should NOT trigger
        (
            "python_const.txt",
            "MIGRATION_QUERY=Abcdef12345678901234567890abcdef123456789",
        ),
        (
            "python_const2.txt",
            "CANDIDATE_LIST=XyZ123Abc456Def789GhI012JkL345MnO678PqR9",
        ),
    ]

    for filename, content in test_cases:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", prefix=filename
        ) as f:
            f.write(content)
            test_file = f.name

        try:
            # Should NOT raise TokenDetectedError
            validate_files([test_file], detect_tokens=True, auto_handle_large=False)
            print(f"✅ No false positive for: {content[:40]}...")
        except TokenDetectedError as e:
            print(f"❌ False positive detected for '{content}': {e}")
            assert False, f"False positive: {e}"
        finally:
            os.unlink(test_file)

    # But uppercase env vars SHOULD still trigger (with proper entropy: upper + lower + digit)
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".txt", prefix="env_var.txt"
    ) as f:
        f.write("API_KEY=Abcdef12345678901234567890abcdef123456789")
        env_file = f.name

    try:
        validate_files([env_file], detect_tokens=True, auto_handle_large=False)
        print("❌ Should have detected uppercase env var")
        assert False, "Expected TokenDetectedError for uppercase env var"
    except TokenDetectedError:
        print("✅ Correctly detected uppercase env var")
    finally:
        os.unlink(env_file)


def test_config_integration():
    """Test integration with GoalConfig."""
    print("\nTesting config integration...")

    # Create a test config
    config = GoalConfig()
    config.set("advanced.file_validation.max_file_size_mb", 5.0)
    config.set("advanced.file_validation.block_large_files", True)
    config.set("advanced.file_validation.detect_api_tokens", True)

    # Test with small file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Small file content")
        small_file = f.name

    # Test with large file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("0" * (6 * 1024 * 1024))  # 6MB
        large_file = f.name

    try:
        # Small file should pass
        validate_files([small_file], max_size_mb=5.0, auto_handle_large=False)
        print("✅ Config integration: small file passes")

        # Large file should fail
        validate_files([large_file], max_size_mb=5.0, auto_handle_large=False)
        print("❌ Config integration: large file should have failed")
        assert False, "Expected FileSizeError"
    except FileSizeError:
        print("✅ Config integration: large file correctly blocked")
        assert True
    finally:
        os.unlink(small_file)
        os.unlink(large_file)


def main():
    """Run all tests."""
    print("Running validation tests...\n")

    results = []
    results.append(test_file_size_validation())
    results.append(test_token_detection())
    results.append(test_safe_files())
    results.append(test_false_positive_prevention())
    results.append(test_config_integration())

    print("\n" + "=" * 50)
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
