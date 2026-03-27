#!/usr/bin/env python3
"""Test path extraction from GitHub error messages."""

import sys
import re
from pathlib import Path

# Add goal to path
sys.path.insert(0, str(Path(__file__).parent))

def test_extract_paths():
    """Test extracting file paths from error messages."""
    
    error_messages = [
        """remote: error: File examples/demo-without-keys/local-strategy.yaml is 296.46 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/quick-start/quick-start.yaml is 895.94 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: GH001: Large files detected. You may want to try Git Large File Storage - https://git-lfs.github.com.""",
        
        """remote: warning: File examples/quick-start/quick-start.yaml is 98.90 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: error: File examples/integrated-functionality/external.yaml is 128.23 MB; this exceeds GitHub's file size limit of 100.00 MB""",
        
        """error: File 'large-file.zip' is 150.00 MB; this exceeds GitHub's file size limit"""
    ]
    
    patterns = [
        r'remote:\s+error:\s+File\s+([^\s]+(?:\.[^\s]+)*)\s+is\s+[\d.]+\s*MB',
        r'File\s+([^\s]+(?:\.[^\s]+)*)\s+is\s+[\d.]+\s*MB',
        r'File\s+([^\s]+(?:\.[^\s]+)*)\s+exceeds',
        r"'([^']+\.[^']+)':",
    ]
    
    for i, error_msg in enumerate(error_messages, 1):
        print(f"\nTest case {i}:")
        print(f"Error: {error_msg[:100]}...")
        
        paths = []
        for pattern in patterns:
            matches = re.findall(pattern, error_msg, re.IGNORECASE)
            paths.extend(matches)
        
        # Filter invalid paths
        valid_paths = []
        for path in paths:
            skip_words = ['file', 'path', 'storage', 'size', 'mb', 'gb', 'git', 'lfs', 'large']
            if path.lower() in skip_words:
                continue
            if '/' not in path and '.' not in path:
                continue
            valid_paths.append(path)
        
        print(f"Extracted paths: {valid_paths}")
        print(f"Unique paths: {list(set(valid_paths))}")

if __name__ == "__main__":
    test_extract_paths()
