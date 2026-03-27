#!/usr/bin/env python3
"""Test automatic large file handling."""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add goal to path
sys.path.insert(0, str(Path(__file__).parent))

def test_large_file_auto_handling():
    """Test that large files are automatically handled."""
    from goal.validators.file_validator import handle_large_files, get_file_size_mb
    
    print("Testing automatic large file handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a large test file
        large_file_path = os.path.join(tmpdir, "large_file.dat")
        with open(large_file_path, 'wb') as f:
            # Write 15MB of data
            f.write(b'0' * (15 * 1024 * 1024))
        
        # Check file size
        size_mb = get_file_size_mb(large_file_path)
        print(f"Created test file: {size_mb:.1f}MB")
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=tmpdir, check=True, capture_output=True)
        
        # Stage the large file
        subprocess.run(['git', 'add', 'large_file.dat'], cwd=tmpdir, check=True, capture_output=True)
        
        # Test auto-handling
        os.chdir(tmpdir)
        try:
            handle_large_files([large_file_path])
            
            # Check .gitignore was updated
            gitignore_path = os.path.join(tmpdir, '.gitignore')
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    content = f.read()
                if 'large_file.dat' in content:
                    print("✓ Large file added to .gitignore")
                else:
                    print("❌ Large file not in .gitignore")
                    return False
            
            # Check file is unstaged
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=tmpdir, capture_output=True, text=True)
            if 'large_file.dat' not in result.stdout:
                print("✓ Large file unstaged")
            else:
                print("❌ Large file still staged")
                return False
            
            print("✅ Automatic large file handling works!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


if __name__ == "__main__":
    success = test_large_file_auto_handling()
    sys.exit(0 if success else 1)
