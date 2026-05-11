#!/usr/bin/env python3
"""Version validation utilities for registry publishing and README badges."""

import re
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def get_pypi_version(package_name: str) -> Optional[str]:
    """Get latest version of a package from PyPI."""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("info", {}).get("version")
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


def get_npm_version(package_name: str) -> Optional[str]:
    """Get latest version of a package from npm registry."""
    try:
        url = f"https://registry.npmjs.org/{package_name}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("dist-tags", {}).get("latest")
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


def get_cargo_version(package_name: str) -> Optional[str]:
    """Get latest version of a crate from crates.io."""
    try:
        url = f"https://crates.io/api/v1/crates/{package_name}"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("crate", {}).get("max_version")
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


def get_rubygems_version(package_name: str) -> Optional[str]:
    """Get latest version of a gem from RubyGems."""
    try:
        url = f"https://rubygems.org/api/v1/gems/{package_name}.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("version")
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


REGISTRY_HANDLERS = {
    "pypi": get_pypi_version,
    "npm": get_npm_version,
    "cargo": get_cargo_version,
    "rubygems": get_rubygems_version,
}


def get_registry_version(registry: str, package_name: str) -> Optional[str]:
    """Get latest version from specified registry."""
    handler = REGISTRY_HANDLERS.get(registry.lower())
    if handler:
        return handler(package_name)
    return None


def extract_badge_versions(readme_path: Path) -> List[Tuple[str, str, str]]:
    """Extract version badges from README.md.
    
    Returns:
        List of tuples: (badge_url, current_version, badge_type)
    """
    if not readme_path.exists():
        return []
    
    content = readme_path.read_text()
    badges = []
    
    # Pattern for shields.io version badges
    version_badge_pattern = r'https://img\.shields\.io/badge/(?:version|v)-([0-9]+\.[0-9]+\.[0-9]+)'
    
    for match in re.finditer(version_badge_pattern, content):
        current_version = match.group(1)
        badge_url = match.group(0)
        badges.append((badge_url, current_version, "version"))
    
    # Pattern for PyPI badges
    pypi_badge_pattern = r'https://img\.shields\.io/badge/pypi-([0-9]+\.[0-9]+\.[0-9]+)'
    
    for match in re.finditer(pypi_badge_pattern, content):
        current_version = match.group(1)
        badge_url = match.group(0)
        badges.append((badge_url, current_version, "pypi"))
    
    return badges


def update_badge_versions(readme_path: Path, new_version: str) -> bool:
    """Update version badges in README.md to new version."""
    if not readme_path.exists():
        return False
    
    content = readme_path.read_text()
    original_content = content
    
    # Update version badges
    content = re.sub(
        r'(https://img\.shields\.io/badge/(?:version|v)-)[0-9]+\.[0-9]+\.[0-9]+',
        f'\\g<1>{new_version}',
        content
    )
    
    # Update PyPI badges
    content = re.sub(
        r'(https://img\.shields\.io/badge/pypi-)[0-9]+\.[0-9]+\.[0-9]+',
        f'\\g<1>{new_version}',
        content
    )
    
    if content != original_content:
        readme_path.write_text(content)
        return True
    
    return False


# -- Per-language package name extractors ----------------------------------

def _detect_python_package() -> Optional[str]:
    """Extract package name from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return None
    try:
        try:
            import tomllib
        except ModuleNotFoundError:
            tomllib = None
        if tomllib is not None:
            data = tomllib.loads(pyproject_path.read_text())
            return (
                (data.get("project") or {}).get("name")
                or ((data.get("tool") or {}).get("poetry") or {}).get("name")
            )
    except (OSError, UnicodeDecodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        logger.debug("Unable to detect python package name from pyproject.toml: %s", exc)
    return None


def _detect_nodejs_package() -> Optional[str]:
    """Extract package name from package.json."""
    package_json_path = Path("package.json")
    if not package_json_path.exists():
        return None
    try:
        data = json.loads(package_json_path.read_text())
        return data.get("name")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.debug("Unable to detect node package name from package.json: %s", exc)
        return None


def _detect_rust_package() -> Optional[str]:
    """Extract package name from Cargo.toml."""
    cargo_path = Path("Cargo.toml")
    if not cargo_path.exists():
        return None
    try:
        content = cargo_path.read_text()
        match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
        return match.group(1) if match else None
    except (OSError, UnicodeDecodeError, re.error) as exc:
        logger.debug("Unable to detect rust package name from Cargo.toml: %s", exc)
        return None


def _detect_ruby_package() -> Optional[str]:
    """Extract gem name from .gemspec."""
    for gemspec_path in Path(".").glob("*.gemspec"):
        try:
            content = gemspec_path.read_text()
            match = re.search(r'\.name\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        except (OSError, UnicodeDecodeError, re.error) as exc:
            logger.debug("Unable to detect ruby package name from %s: %s", gemspec_path, exc)
    return None


# Registry for each project type: (registry_name, detect_func_name, fetch_func_name, not_found_msg)
# Uses function names (not references) so that unittest.mock.patch works correctly.
_VERSION_VALIDATORS = {
    "python": ("pypi",     "_detect_python_package", "get_pypi_version",     "Package not found in PyPI"),
    "nodejs": ("npm",      "_detect_nodejs_package", "get_npm_version",      "Package not found in npm"),
    "rust":   ("cargo",    "_detect_rust_package",   "get_cargo_version",    "Crate not found in crates.io"),
    "ruby":   ("rubygems", "_detect_ruby_package",   "get_rubygems_version", "Gem not found in RubyGems"),
}

import sys as _sys


def _validate_single_type(project_type: str, current_version: str) -> Dict:
    """Validate a single project type against its registry.

    Returns a result dict with registry info, or defaults when the type
    is unknown / the package cannot be detected.
    """
    result: Dict = {
        "registry": None,
        "package_name": None,
        "registry_version": None,
        "local_version": current_version,
        "is_latest": True,
        "error": None,
    }

    entry = _VERSION_VALIDATORS.get(project_type)
    if not entry:
        return result

    registry_name, detect_name, fetch_name, not_found_msg = entry
    _mod = _sys.modules[__name__]
    package_name = getattr(_mod, detect_name)()
    if not package_name:
        return result

    result["registry"] = registry_name
    result["package_name"] = package_name
    result["registry_version"] = getattr(_mod, fetch_name)(package_name)
    if result["registry_version"]:
        result["is_latest"] = result["registry_version"] == current_version
    else:
        result["error"] = not_found_msg

    return result


def validate_project_versions(project_types: List[str], current_version: str) -> Dict[str, Dict]:
    """Validate versions across different registries.

    Returns:
        Dict with validation results for each project type.
    """
    return {pt: _validate_single_type(pt, current_version) for pt in project_types}


def check_readme_badges(current_version: str) -> Dict[str, any]:
    """Check if README badges are up to date with current version."""
    readme_path = Path("README.md")
    
    if not readme_path.exists():
        return {
            "exists": False,
            "badges": [],
            "needs_update": False,
            "message": "README.md not found"
        }
    
    badges = extract_badge_versions(readme_path)
    needs_update = any(
        badge_version != current_version 
        for _, badge_version, _ in badges
    )
    
    return {
        "exists": True,
        "badges": [
            {
                "url": url,
                "current_version": version,
                "needs_update": version != current_version
            }
            for url, version, _ in badges
        ],
        "needs_update": needs_update,
        "message": "Badges are up to date" if not needs_update else f"Badges need update to {current_version}"
    }


def format_validation_results(results: Dict[str, Dict]) -> List[str]:
    """Format validation results for display."""
    messages = []
    
    for project_type, result in results.items():
        if result["error"]:
            messages.append(f"❌ {project_type}: {result['error']}")
        elif not result["registry_version"]:
            messages.append(f"⚠️  {project_type}: Could not fetch registry version")
        elif result["is_latest"]:
            messages.append(f"✅ {project_type}: Version {result['local_version']} is up to date")
        else:
            messages.append(
                f"⚠️  {project_type}: Local {result['local_version']} != Registry {result['registry_version']}"
            )
    
    return messages
