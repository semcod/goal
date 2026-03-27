#!/usr/bin/env python3
"""Test script for file validation functionality."""

import os
import tempfile
import sys
from pathlib import Path

# Add goal to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from goal.validators.file_validator import validate_files, FileSizeError, TokenDetectedError
from goal.config import GoalConfig


def test_file_size_validation():
    """Test file size validation."""
    print("Testing file size validation...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        # Create a file larger than 10MB (using zeros)
        f.write('0' * (11 * 1024 * 1024))  # 11MB
        large_file = f.name
    
    try:
        # Should raise FileSizeError
        validate_files([large_file], max_size_mb=10.0)
        print("❌ File size validation failed - should have raised error")
        return False
    except FileSizeError as e:
        print(f"✅ File size validation works: {e}")
        return True
    finally:
        os.unlink(large_file)


def test_token_detection():
    """Test API token detection."""
    print("\nTesting API token detection...")
    
    test_cases = [
        ("github_token.txt", "ghp_test_token_abcdefghijklmnop", "GitHub Personal Access"),
        ("aws_key.txt", "AKIATEST1234567890ABCD", "AWS Access Key"),
        ("slack_bot.txt", "xoxb-test-123-456-abcdefghijklmnop", "Slack Bot"),
        ("generic_token.txt", "Bearer test_token_1234567890", "Bearer Token"),
    ]
    
    all_passed = True
    
    for filename, content, expected_type in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', prefix=filename) as f:
            f.write(content)
            test_file = f.name
        
        try:
            validate_files([test_file], detect_tokens=True)
            print(f"❌ Token detection failed for {expected_type}")
            all_passed = False
        except TokenDetectedError as e:
            if expected_type in str(e):
                print(f"✅ Token detection works for {expected_type}")
            else:
                print(f"❌ Wrong token type detected: {e}")
                all_passed = False
        finally:
            os.unlink(test_file)
    
    return all_passed


def test_safe_files():
    """Test that safe files pass validation."""
    print("\nTesting safe files...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        f.write("""
# Normal Python code
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
""")
        safe_file = f.name
    
    try:
        validate_files([safe_file], max_size_mb=10.0, detect_tokens=True)
        print("✅ Safe files pass validation")
        return True
    except Exception as e:
        print(f"❌ Safe file validation failed: {e}")
        return False
    finally:
        os.unlink(safe_file)


def test_config_integration():
    """Test integration with GoalConfig."""
    print("\nTesting config integration...")
    
    # Create a test config
    config = GoalConfig()
    config.set('advanced.file_validation.max_file_size_mb', 5.0)
    config.set('advanced.file_validation.block_large_files', True)
    config.set('advanced.file_validation.detect_api_tokens', True)
    
    # Test with small file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Small file content")
        small_file = f.name
    
    # Test with large file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write('0' * (6 * 1024 * 1024))  # 6MB
        large_file = f.name
    
    try:
        # Small file should pass
        validate_files([small_file], max_size_mb=5.0)
        print("✅ Config integration: small file passes")
        
        # Large file should fail
        validate_files([large_file], max_size_mb=5.0)
        print("❌ Config integration: large file should have failed")
        return False
    except FileSizeError:
        print("✅ Config integration: large file correctly blocked")
        return True
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
    results.append(test_config_integration())
    
    print("\n" + "="*50)
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
