"""Project type detection - extracted from project_bootstrap.py."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from goal.bootstrap.templates import PROJECT_TEMPLATES


def _match_marker(base: Path, pattern: str) -> bool:
    """Check if a marker file/pattern exists under *base*."""
    if '*' in pattern:
        return bool(list(base.glob(pattern)))
    return (base / pattern).exists()


def detect_project_types_deep(root: Optional[Path] = None, max_depth: int = 1) -> Dict[str, List[Path]]:
    """Detect project types in *root* and up to *max_depth* subfolder levels.

    Returns a dict mapping project type → list of directories where it was found.
    """
    if root is None:
        root = Path('.')
    root = root.resolve()

    results: Dict[str, List[Path]] = {}

    dirs_to_scan = [root]
    if max_depth >= 1:
        try:
            for child in sorted(root.iterdir()):
                if child.is_dir() and not child.name.startswith('.'):
                    dirs_to_scan.append(child)
        except PermissionError:
            pass

    for scan_dir in dirs_to_scan:
        for ptype, cfg in PROJECT_TEMPLATES.items():
            for marker in cfg.marker_files:
                if _match_marker(scan_dir, marker):
                    results.setdefault(ptype, []).append(scan_dir)
                    break

    return results


def _guess_python_name(project_dir: Path) -> Optional[str]:
    """Guess Python package name from pyproject.toml or setup.py."""
    for filename, pattern, flags in [
        ('pyproject.toml', r'^name\s*=\s*["\']([^"\']+)["\']', re.MULTILINE),
        ('setup.py',       r'name\s*=\s*["\']([^"\']+)["\']', 0),
    ]:
        path = project_dir / filename
        if not path.exists():
            continue
        try:
            m = re.search(pattern, path.read_text(errors='ignore'), flags)
            if m:
                return m.group(1).replace('-', '_')
        except Exception:
            pass
    return None


def _guess_nodejs_name(project_dir: Path) -> Optional[str]:
    """Guess Node.js package name from package.json."""
    pkg = project_dir / 'package.json'
    if not pkg.exists():
        return None
    try:
        data = json.loads(pkg.read_text(errors='ignore'))
        name = data.get('name', '')
        return name.split('/')[-1] if '/' in name else name
    except Exception:
        return None


def _guess_rust_name(project_dir: Path) -> Optional[str]:
    """Guess Rust crate name from Cargo.toml."""
    cargo = project_dir / 'Cargo.toml'
    if not cargo.exists():
        return None
    try:
        m = re.search(r'^name\s*=\s*"([^"]+)"', cargo.read_text(errors='ignore'), re.MULTILINE)
        return m.group(1) if m else None
    except Exception:
        return None


def _guess_go_name(project_dir: Path) -> Optional[str]:
    """Guess Go module name from go.mod."""
    gomod = project_dir / 'go.mod'
    if not gomod.exists():
        return None
    try:
        m = re.search(r'^module\s+(\S+)', gomod.read_text(errors='ignore'), re.MULTILINE)
        return m.group(1).split('/')[-1] if m else None
    except Exception:
        return None


def guess_package_name(project_dir: Path, project_type: str) -> Optional[str]:
    """Guess package name based on project type."""
    guessers = {
        'python': _guess_python_name,
        'nodejs': _guess_nodejs_name,
        'rust': _guess_rust_name,
        'go': _guess_go_name,
    }
    if project_type in guessers:
        return guessers[project_type](project_dir)
    return None
