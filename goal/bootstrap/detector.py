"""Project type detection - extracted from project_bootstrap.py."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from goal.bootstrap.templates import PROJECT_TEMPLATES


def _match_marker(base: Path, pattern: str) -> bool:
    """Check if a marker file/pattern exists under *base*."""
    if "*" in pattern:
        return bool(list(base.glob(pattern)))
    return (base / pattern).exists()


def detect_project_types_deep(
    root: Optional[Path] = None, max_depth: int = 1
) -> Dict[str, List[Path]]:
    """Detect project types in *root* and up to *max_depth* subfolder levels.

    Returns a dict mapping project type → list of directories where it was found.
    """
    if root is None:
        root = Path(".")
    root = root.resolve()

    results: Dict[str, List[Path]] = {}

    dirs_to_scan = [root]
    if max_depth >= 1:
        try:
            for child in sorted(root.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
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


def _python_package_dir_exists(project_dir: Path, package_name: str) -> bool:
    """Return True when *package_name* looks like an on-disk Python package."""
    for base in (project_dir, project_dir / "src"):
        pkg_dir = base / package_name
        if not pkg_dir.is_dir():
            continue
        if (pkg_dir / "__init__.py").exists():
            return True
        if any(pkg_dir.glob("*.py")):
            return True
    return False


def _guess_python_name(project_dir: Path) -> Optional[str]:
    """Guess Python package name from pyproject.toml or setup.py."""
    for filename, pattern, flags in [
        ("pyproject.toml", r'^name\s*=\s*["\']([^"\']+)["\']', re.MULTILINE),
        ("setup.py", r'name\s*=\s*["\']([^"\']+)["\']', 0),
    ]:
        path = project_dir / filename
        if not path.exists():
            continue
        try:
            m = re.search(pattern, path.read_text(errors="ignore"), flags)
            if m:
                return m.group(1).replace("-", "_")
        except Exception:
            pass
    return None


def _python_scaffold_import_name(project_dir: Path, name: str) -> str:
    """Pick an import name for scaffold tests when pyproject name is not a package."""
    if _python_package_dir_exists(project_dir, name):
        return name
    dirname = project_dir.name.replace("-", "_")
    if dirname in ("tests", "test"):
        return dirname
    if name.endswith("_tests") or name.endswith("_test"):
        return dirname
    return name


def _guess_nodejs_name(project_dir: Path) -> Optional[str]:
    """Guess Node.js package name from package.json."""
    pkg = project_dir / "package.json"
    if not pkg.exists():
        return None
    try:
        data = json.loads(pkg.read_text(errors="ignore"))
        name = data.get("name", "")
        return name.split("/")[-1] if "/" in name else name
    except Exception:
        return None


def _guess_rust_name(project_dir: Path) -> Optional[str]:
    """Guess Rust crate name from Cargo.toml."""
    cargo = project_dir / "Cargo.toml"
    if not cargo.exists():
        return None
    try:
        m = re.search(
            r'^name\s*=\s*"([^"]+)"', cargo.read_text(errors="ignore"), re.MULTILINE
        )
        return m.group(1) if m else None
    except Exception:
        return None


def _guess_go_name(project_dir: Path) -> Optional[str]:
    """Guess Go module name from go.mod."""
    gomod = project_dir / "go.mod"
    if not gomod.exists():
        return None
    try:
        m = re.search(
            r"^module\s+(\S+)", gomod.read_text(errors="ignore"), re.MULTILINE
        )
        return m.group(1).split("/")[-1] if m else None
    except Exception:
        return None


def guess_package_name(project_dir: Path, project_type: str) -> str:
    """Best-effort guess of the package/module name for scaffold templates."""
    project_dir = project_dir.resolve()
    guessers = {
        "python": _guess_python_name,
        "nodejs": _guess_nodejs_name,
        "rust": _guess_rust_name,
        "go": _guess_go_name,
    }
    if project_type in guessers:
        name = guessers[project_type](project_dir)
        if name:
            if project_type == "python":
                return _python_scaffold_import_name(project_dir, name)
            return name
    return project_dir.name.replace("-", "_")
