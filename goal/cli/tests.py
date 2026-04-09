"""Test running functions - extracted from cli.py."""

import subprocess
import os
import shutil
from pathlib import Path
from typing import List, Optional

import click

from goal.git_ops import run_command
from goal.cli.version import PROJECT_TYPES
from goal.project_bootstrap import _find_python_bin


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


def _has_project_marker(project_dir: Path, marker: str) -> bool:
    """Check whether a marker file or glob exists in a directory."""
    if '*' in marker:
        return any(project_dir.glob(marker))
    return (project_dir / marker).exists()


def _find_project_root(path: Path, project_type: str) -> Optional[Path]:
    """Find the nearest ancestor that looks like a project root."""
    markers = PROJECT_TYPES.get(project_type, {}).get('files', [])
    current = path

    while True:
        if any(_has_project_marker(current, marker) for marker in markers):
            return current

        if current.parent == current:
            return None

        current = current.parent


_SKIP_DIRS = {'venv', '.venv', 'build', 'dist', '__pycache__', 'node_modules'}


def _find_python_test_dirs() -> List[str]:
    """Find subdirectories containing Python test files that belong to a real sub-project."""
    dirs: List[str] = []
    for root, child_dirs, files in os.walk('.'):
        child_dirs[:] = [d for d in child_dirs if not d.startswith('.') and d not in _SKIP_DIRS]
        if root == '.':
            continue
        if not any(f.startswith('test_') and f.endswith('.py') for f in files):
            continue
        project_root = _find_project_root(Path(root), 'python')
        if project_root is None or project_root == Path('.'):
            continue
        dirs.append(root)
    return dirs


def _find_nodejs_test_dirs() -> List[str]:
    """Find subdirectories with a usable Node.js test script."""
    if shutil.which('npm') is None:
        return []
    dirs: List[str] = []
    for package_json in Path('.').rglob('package.json'):
        if set(package_json.parts) & _SKIP_DIRS:
            continue
        if str(package_json.parent) != '.' and _has_usable_test_script(package_json.parent, 'nodejs'):
            dirs.append(str(package_json.parent))
    return dirs


def _run_subdir_test(project_type: str, base_cmd: List[str], test_dir: str) -> bool:
    """Run a single sub-directory test. Returns True on success."""
    try:
        if project_type == 'python':
            if Path(test_dir).parent == Path('.'):
                return True
            result = subprocess.run(base_cmd + [test_dir], capture_output=True, text=True, timeout=120)
        else:
            result = subprocess.run(base_cmd, cwd=test_dir, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            click.echo(click.style(f"\n  ❌ Tests failed in {test_dir}/", fg='red'))
            if result.stdout:
                click.echo(click.style("  stdout:", fg='yellow'))
                for line in result.stdout.strip().split('\n')[:10]:
                    click.echo(f"    {line}")
            if result.stderr:
                click.echo(click.style("  stderr:", fg='yellow'))
                for line in result.stderr.strip().split('\n')[:10]:
                    click.echo(f"    {line}")
            if project_type == 'nodejs':
                if not (Path(test_dir) / 'node_modules').exists():
                    click.echo(click.style(f"\n  💡 Fix: cd {test_dir} && npm install", fg='cyan'))
                elif 'Cannot find module' in (result.stderr or ''):
                    click.echo(click.style(f"\n  💡 Fix: cd {test_dir} && npm run compile", fg='cyan'))
            return False
        return True
    except Exception as e:
        click.echo(click.style(f"\n  ❌ Error running tests in {test_dir}/: {e}", fg='red'))
        return False


def _run_tests_in_subdirs(project_type: str, base_cmd: List[str]) -> bool:
    """Run tests in subdirectories (monorepo support)."""
    finders = {'python': _find_python_test_dirs, 'nodejs': _find_nodejs_test_dirs}
    finder = finders.get(project_type)
    if not finder:
        return True

    test_dirs = finder()
    if not test_dirs:
        return True

    if test_dirs:
        click.echo(click.style(f"  📁 Running tests in {len(test_dirs)} subproject(s): {', '.join(test_dirs[:5])}", fg='cyan'))

    return all(_run_subdir_test(project_type, base_cmd, d) for d in test_dirs[:5])


def run_tests(project_types: List[str]) -> bool:
    """Run tests for detected project types."""
    success = True
    
    for ptype in project_types:
        config = PROJECT_TYPES.get(ptype, {})
        test_cmd_str = config.get('test_command', '')
        
        if not test_cmd_str:
            continue

        if ptype == 'python':
            test_cmd = [_find_python_bin(Path.cwd()), '-m', 'pytest']
        else:
            test_cmd = test_cmd_str.split()
        
        # Special handling for Node.js to check if tests are configured
        if ptype == 'nodejs':
            if not _has_usable_test_script(Path('.'), 'nodejs'):
                continue
        
        try:
            if ptype == 'python':
                result = subprocess.run(
                    test_cmd,
                    capture_output=False,
                    text=True,
                )
            else:
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
