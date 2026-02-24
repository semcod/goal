#!/usr/bin/env python3
"""Version validation utilities for registry publishing and README badges."""

import re
import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from pathlib import Path


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


def validate_project_versions(project_types: List[str], current_version: str) -> Dict[str, Dict]:
    """Validate versions across different registries.
    
    Returns:
        Dict with validation results for each project type.
    """
    results = {}
    
    for project_type in project_types:
        result = {
            "registry": None,
            "package_name": None,
            "registry_version": None,
            "local_version": current_version,
            "is_latest": True,
            "error": None
        }
        
        if project_type == "python":
            # Try to get package name from pyproject.toml
            package_name = None
            pyproject_path = Path("pyproject.toml")
            if pyproject_path.exists():
                try:
                    try:
                        import tomllib
                    except ModuleNotFoundError:
                        tomllib = None
                    
                    if tomllib is not None:
                        data = tomllib.loads(pyproject_path.read_text())
                        package_name = (
                            (data.get("project") or {}).get("name")
                            or ((data.get("tool") or {}).get("poetry") or {}).get("name")
                        )
                except Exception:
                    pass
            
            if package_name:
                result["registry"] = "pypi"
                result["package_name"] = package_name
                result["registry_version"] = get_pypi_version(package_name)
                
                if result["registry_version"]:
                    result["is_latest"] = result["registry_version"] == current_version
                else:
                    result["error"] = "Package not found in PyPI"
        
        elif project_type == "nodejs":
            # Try to get package name from package.json
            package_name = None
            package_json_path = Path("package.json")
            if package_json_path.exists():
                try:
                    data = json.loads(package_json_path.read_text())
                    package_name = data.get("name")
                except Exception:
                    pass
            
            if package_name:
                result["registry"] = "npm"
                result["package_name"] = package_name
                result["registry_version"] = get_npm_version(package_name)
                
                if result["registry_version"]:
                    result["is_latest"] = result["registry_version"] == current_version
                else:
                    result["error"] = "Package not found in npm"
        
        elif project_type == "rust":
            # Try to get package name from Cargo.toml
            package_name = None
            cargo_path = Path("Cargo.toml")
            if cargo_path.exists():
                try:
                    content = cargo_path.read_text()
                    match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
                    if match:
                        package_name = match.group(1)
                except Exception:
                    pass
            
            if package_name:
                result["registry"] = "cargo"
                result["package_name"] = package_name
                result["registry_version"] = get_cargo_version(package_name)
                
                if result["registry_version"]:
                    result["is_latest"] = result["registry_version"] == current_version
                else:
                    result["error"] = "Crate not found in crates.io"
        
        elif project_type == "ruby":
            # Try to get gem name from .gemspec
            package_name = None
            for gemspec_path in Path(".").glob("*.gemspec"):
                try:
                    content = gemspec_path.read_text()
                    match = re.search(r'\.name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        package_name = match.group(1)
                        break
                except Exception:
                    pass
            
            if package_name:
                result["registry"] = "rubygems"
                result["package_name"] = package_name
                result["registry_version"] = get_rubygems_version(package_name)
                
                if result["registry_version"]:
                    result["is_latest"] = result["registry_version"] == current_version
                else:
                    result["error"] = "Gem not found in RubyGems"
        
        results[project_type] = result
    
    return results


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
