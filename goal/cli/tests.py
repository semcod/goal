"""Test running functions - extracted from cli.py."""

import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Dict

try:
    from ..git_ops import run_git, run_command
    from .version import PROJECT_TYPES
except ImportError:
    from goal.git_ops import run_git, run_command
    from goal.cli.version import PROJECT_TYPES


def _has_usable_test_script(project_dir: Path, project_type: str) -> bool:
    """Check if project has a usable test script defined."""
    if project_type == 'nodejs':
        package_json = project_dir / 'package.json'
        if package_json.exists():
            import json
            try:
                data = json.loads(package_json.read_text())
                scripts = data.get('scripts', {})
                if 'test' in scripts:
                    test_cmd = scripts['test']
                    # Check if it's not the default placeholder
                    if test_cmd and test_cmd not in ['echo "Error: no test specified"', 'echo "Error: no test specified" && exit 1']:
                        return True
            except Exception:
                pass
    return False


def _run_tests_in_subdirs(project_type: str, base_cmd: List[str]) -> bool:
    """Run tests in subdirectories (monorepo support)."""
    test_dirs = []
    
    if project_type == 'python':
        # Find directories with test files
        for root, dirs, files in os.walk('.'):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', '.venv', 'build', 'dist', '__pycache__', 'node_modules']]
            
            if any(f.startswith('test_') and f.endswith('.py') for f in files):
                if root != '.':
                    test_dirs.append(root)
    
    elif project_type == 'nodejs':
        # Skip node tests if npm is not available
        if shutil.which('npm') is None:
            return True

        # Find directories with package.json that have test scripts
        for package_json in Path('.').rglob('package.json'):
            # Avoid picking up package.json in virtualenvs, build artifacts or dependencies
            parts = set(package_json.parts)
            if parts.intersection({'venv', '.venv', 'node_modules', 'build', 'dist', '__pycache__'}):
                continue

            if _has_usable_test_script(package_json.parent, 'nodejs'):
                if str(package_json.parent) != '.':
                    test_dirs.append(str(package_json.parent))
    
    if not test_dirs:
        return True  # No subdir tests to run
    
    all_passed = True
    for test_dir in test_dirs[:5]:  # Limit to 5 subdirs to avoid runaway
        try:
            result = subprocess.run(
                base_cmd,
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                all_passed = False
        except Exception:
            all_passed = False
    
    return all_passed


def run_tests(project_types: List[str]) -> bool:
    """Run tests for detected project types."""
    success = True
    
    for ptype in project_types:
        config = PROJECT_TYPES.get(ptype, {})
        test_cmd_str = config.get('test_command', '')
        
        if not test_cmd_str:
            continue
        
        test_cmd = test_cmd_str.split()
        
        # Special handling for Node.js to check if tests are configured
        if ptype == 'nodejs':
            if not _has_usable_test_script(Path('.'), 'nodejs'):
                continue
        
        try:
            result = run_command(test_cmd_str, capture=False)
            if result.returncode != 0:
                success = False
            
            # Also try running in subdirs for monorepos
            if not _run_tests_in_subdirs(ptype, test_cmd):
                success = False
                
        except Exception:
            success = False
    
    return success


__all__ = [
    '_has_usable_test_script',
    '_run_tests_in_subdirs',
    'run_tests',
]
