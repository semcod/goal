"""Test running functions - extracted from cli.py."""

import os
import shlex
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

import click

from goal.git_ops import run_command
from goal.cli.version import PROJECT_TYPES
from goal.project_bootstrap import _find_python_bin


def _get_project_strategy(config: object, project_type: str) -> dict:
    """Get strategy config for a project type from GoalConfig/dict."""
    if config is None:
        return {}

    if hasattr(config, 'get_strategy'):
        try:
            return config.get_strategy(project_type) or {}
        except Exception:
            return {}

    if isinstance(config, dict):
        return config.get('strategies', {}).get(project_type, {}) or {}

    return {}


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


def _active_venv_python() -> Optional[str]:
    """Return active virtualenv Python path when VIRTUAL_ENV is set."""
    venv = os.environ.get('VIRTUAL_ENV')
    if not venv:
        return None
    candidate = Path(venv) / 'bin' / 'python'
    if candidate.exists():
        return str(candidate)
    return None


def _resolve_project_python(project_root: Optional[Path], fallback_python: str) -> str:
    """Resolve Python interpreter for a subproject, preferring its own virtualenv."""
    if not project_root:
        return fallback_python
    try:
        candidate = Path(_find_python_bin(project_root))
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        return str(candidate)
    except Exception:
        return fallback_python


def _coerce_python_strategy_to_project_pytest(test_cmd_str: str, python_bin: str) -> Optional[List[str]]:
    """Convert common pytest strategy commands to use the resolved project Python."""
    try:
        args = shlex.split(test_cmd_str)
    except Exception:
        return None

    if not args:
        return None

    first = Path(args[0]).name
    if first in {'pytest', 'py.test'}:
        return [python_bin, '-m', 'pytest', *args[1:]]

    if first in {'python', 'python3'} and len(args) >= 3 and args[1] == '-m' and args[2] == 'pytest':
        return [python_bin, '-m', 'pytest', *args[3:]]

    return None


def _find_python_test_dirs() -> List[str]:
    """Find Python subproject test targets (tests/ dir preferred, otherwise project root)."""
    cwd = Path('.').resolve()
    seen_roots: set[str] = set()
    project_roots: List[Path] = []

    for test_file in Path('.').rglob('test_*.py'):
        if set(test_file.parts) & _SKIP_DIRS:
            continue

        project_root = _find_project_root(test_file.parent, 'python')
        if project_root is None:
            continue

        try:
            resolved_root = project_root.resolve()
        except Exception:
            resolved_root = project_root

        if resolved_root == cwd:
            continue

        root_key = str(resolved_root)
        if root_key in seen_roots:
            continue
        seen_roots.add(root_key)
        project_roots.append(project_root)

    dirs: List[str] = []
    for root in project_roots:
        tests_dir = root / 'tests'
        if tests_dir.is_dir():
            dirs.append(str(tests_dir))
        else:
            dirs.append(str(root))

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


def _check_python_venv(project_root: Optional[Path]) -> tuple[bool, Optional[Path]]:
    """Check if Python project has a virtual environment. Returns (has_venv, project_root)."""
    if not project_root:
        return False, None
    venv_paths = [
        project_root / '.venv',
        project_root / 'venv',
        project_root / 'env',
    ]
    has_venv = any(v.exists() for v in venv_paths)
    return has_venv, project_root


def _ensure_pytest_for_project(project_root: Path, python_bin: str) -> bool:
    """Ensure pytest is available in the subproject environment."""
    check_result = subprocess.run(
        [python_bin, '-c', 'import pytest'],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if check_result.returncode == 0:
        return True

    click.echo(click.style(f"\n  📦 Installing test dependencies in {project_root}/", fg='cyan'))

    install_attempts = [
        [python_bin, '-m', 'pip', 'install', '-e', '.[dev]'],
        [python_bin, '-m', 'pip', 'install', '-e', '.'],
        [python_bin, '-m', 'pip', 'install', 'pytest', 'pytest-cov'],
    ]

    for cmd in install_attempts:
        install_result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if install_result.returncode != 0:
            continue

        verify = subprocess.run(
            [python_bin, '-c', 'import pytest'],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if verify.returncode == 0:
            return True

    click.echo(click.style(f"\n  ❌ Failed to install test dependencies in {project_root}/", fg='red'))
    click.echo(click.style(f"  💡 Fix: cd {project_root} && {python_bin} -m pip install -e .[dev]", fg='cyan'))
    return False


def _display_test_error(result: subprocess.CompletedProcess, test_dir: str, project_type: str) -> None:
    """Display test failure output."""
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


def _run_python_test(test_dir: str, base_cmd: List[str]) -> tuple[bool, bool]:
    """Run Python tests in a subdirectory. Returns (success, skipped)."""
    project_root = _find_project_root(Path(test_dir), 'python')
    if not project_root:
        return True, True

    has_venv, _ = _check_python_venv(project_root)
    if not has_venv:
        click.echo(click.style(
            f"  ⏭️  Skipping {project_root.name}/ - no virtual environment (run 'goal doctor' to set up)",
            fg='yellow'
        ))
        return True, True

    python_bin = _resolve_project_python(project_root, base_cmd[0])
    if not _ensure_pytest_for_project(project_root, python_bin):
        click.echo(click.style(
            f"\n  ⏭️  Skipping {project_root.name}/ tests",
            fg='yellow'
        ))
        return True, True

    subdir_cmd = [python_bin, '-m', 'pytest']
    result = subprocess.run(subdir_cmd + [test_dir], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        _display_test_error(result, test_dir, 'python')
        return False, False
    return True, False


def _run_nodejs_test(test_dir: str, base_cmd: List[str]) -> bool:
    """Run Node.js tests in a subdirectory. Returns True on success."""
    result = subprocess.run(base_cmd, cwd=test_dir, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        _display_test_error(result, test_dir, 'nodejs')
        return False
    return True


def _run_subdir_test(project_type: str, base_cmd: List[str], test_dir: str) -> bool:
    """Run a single sub-directory test. Returns True on success."""
    try:
        if project_type == 'python':
            success, _ = _run_python_test(test_dir, base_cmd)
            return success
        else:
            return _run_nodejs_test(test_dir, base_cmd)
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


def run_tests(project_types: List[str], config: object = None) -> bool:
    """Run tests for detected project types."""
    success = True
    
    for ptype in project_types:
        project_config = PROJECT_TYPES.get(ptype, {})
        strategy = _get_project_strategy(config, ptype)
        strategy_test_cmd = strategy.get('test', '') if isinstance(strategy, dict) else ''
        if not isinstance(strategy_test_cmd, str):
            strategy_test_cmd = ''
        test_cmd_str = strategy_test_cmd or project_config.get('test_command', '')
        run_subdir_scan = not bool(strategy_test_cmd)
        
        if not test_cmd_str:
            continue

        use_subprocess = False

        if ptype == 'python':
            active_python = _active_venv_python()
            if active_python:
                python_bin = active_python
            else:
                detected_python = Path(_find_python_bin(Path.cwd()))
                if not detected_python.is_absolute():
                    detected_python = (Path.cwd() / detected_python).resolve()
                python_bin = str(detected_python)

            if strategy_test_cmd:
                coerced_cmd = _coerce_python_strategy_to_project_pytest(test_cmd_str, python_bin)
                if coerced_cmd is not None:
                    test_cmd = coerced_cmd
                    use_subprocess = True
                    if not _ensure_pytest_for_project(Path.cwd(), python_bin):
                        click.echo(click.style("\n  ❌ Root python environment is missing pytest.", fg='red'))
                        success = False
                        # Continue with subprojects to provide fuller diagnostics in monorepos.
                        if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
                            success = False
                        continue
                else:
                    test_cmd = test_cmd_str.split()
            else:
                test_cmd = [python_bin, '-m', 'pytest']
                use_subprocess = True

                if not _ensure_pytest_for_project(Path.cwd(), python_bin):
                    click.echo(click.style("\n  ❌ Root python environment is missing pytest.", fg='red'))
                    success = False
                    # Continue with subprojects to provide fuller diagnostics in monorepos.
                    if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
                        success = False
                    continue
        else:
            test_cmd = test_cmd_str.split()
        
        # Special handling for Node.js to check if tests are configured
        if ptype == 'nodejs':
            if not _has_usable_test_script(Path('.'), 'nodejs'):
                continue
        
        try:
            if use_subprocess:
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
            if run_subdir_scan and not _run_tests_in_subdirs(ptype, test_cmd):
                success = False
                
        except Exception:
            success = False
    
    return success


__all__ = [
    '_has_usable_test_script',
    '_run_tests_in_subdirs',
    'run_tests',
]
