#!/usr/bin/env python3
"""Debug the recovery path extraction."""

import sys
import re
from pathlib import Path

# Add goal to path
sys.path.insert(0, str(Path(__file__).parent))

from goal.recovery.strategies import LargeFileStrategy

def test_recovery():
    """Test the recovery strategy with actual error."""
    
    # The actual error from the user
    error_output = """remote: warning: File examples/quick-start/quick-start.yaml is 98.90 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: File .planfile_analysis/analysis_summary.json is 73.26 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: File examples/strategies/.planfile_analysis/analysis_summary.json is 69.74 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: File planfile/.planfile_analysis/analysis_summary.json is 69.40 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: File examples/integrated-functionality/generated.yaml is 92.42 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: File examples/quick-start/quick-start.yaml is 63.31 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: error: File examples/integrated-functionality/external.yaml is 128.23 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/demo-without-keys/local-strategy.yaml is 296.46 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/strategies/.planfile_analysis/analysis_summary.json is 209.76 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File planfile-from-files.yaml is 189.00 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/quick-start/quick-start.yaml is 895.94 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/external-tools/full-analysis.yaml is 128.13 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File planfile-from-files.yaml is 129.16 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/external-tools/full-analysis.yaml is 194.32 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/integrated-functionality/generated.yaml is 297.84 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: File examples/integrated-functionality/external-tools-strategy.yaml is 194.31 MB; this exceeds GitHub's file size limit of 100.00 MB
remote: error: GH001: Large files detected. You may want to try Git Large File Storage - https://git-lfs.github.com.
To github.com:semcod/strategy.git
 ! [remote rejected] main -> main (pre-receive hook declined)
error: failed to push some refs to 'github.com:semcod/strategy.git'"""
    
    strategy = LargeFileStrategy("/tmp")
    
    print("Testing individual patterns:")
    patterns = [
        r'remote:\s+error:\s+File\s+(\S+)\s+is\s+[\d.]+\s*MB',
        r'File\s+(\S+)\s+is\s+[\d.]+\s*MB',
        r'File\s+(\S+)\s+exceeds',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, error_output, re.IGNORECASE)
        print(f"Pattern: {pattern}")
        print(f"Matches: {matches}")
        print()
    
    print("\nTesting path extraction:")
    paths = strategy._extract_file_paths(error_output)
    print(f"Extracted paths: {paths}")
    
    print("\nTesting if can handle:")
    can_handle = strategy.can_handle(error_output)
    print(f"Can handle: {can_handle}")

if __name__ == "__main__":
    test_recovery()
