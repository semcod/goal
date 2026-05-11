"""Discovery helpers for locating test targets (extracted from tests.py for maintainability)."""

import shutil
from pathlib import Path
from typing import List, Optional

from goal.cli.version import PROJECT_TYPES

_SKIP_DIRS = {'venv', '.venv', 'build', 'dist', '__pycache__', 'node_modules'}


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
                    if test_cmd and test_cmd not in [
                        'echo "Error: no test specified"',
                        'echo "Error: no test specified" && exit 1',
                    ]:
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


def find_python_test_dirs() -> List[str]:
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


def find_nodejs_test_dirs() -> List[str]:
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
