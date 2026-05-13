"""Version management - version synchronization functions."""

import re
from pathlib import Path
from typing import List

try:
    import tomlkit
except ImportError:
    tomlkit = None

from .version_utils import (
    update_json_version,
    update_project_metadata,
    update_readme_metadata,
)
from goal.version_validation import update_badge_versions


def _update_version_file(new_version: str, updated: List[str]) -> None:
    """Update VERSION file."""
    Path("VERSION").write_text(f"{new_version}\n")
    updated.append("VERSION")


def _update_json_version_file(
    filename: str, new_version: str, user_config, updated: List[str]
) -> None:
    """Update JSON version file (package.json, composer.json)."""
    path = Path(filename)
    if path.exists():
        if update_json_version(path, new_version):
            updated.append(filename)
        if user_config and update_project_metadata(path, user_config):
            if filename not in updated:
                updated.append(filename)


def _update_toml_version(
    filename: str, new_version: str, user_config, updated: List[str]
) -> None:
    """Update TOML version file (pyproject.toml)."""
    path = Path(filename)
    if not path.exists():
        return

    try:
        content = path.read_text()
        # Use tomlkit to preserve formatting and structure
        if tomlkit is not None:
            doc = tomlkit.parse(content)
            if "project" in doc and "version" in doc["project"]:
                if doc["project"]["version"] != new_version:
                    doc["project"]["version"] = new_version
                    path.write_text(tomlkit.dumps(doc))
                    updated.append(filename)
        else:
            # Fallback to regex if tomlkit not available
            new_content = re.sub(
                r'^(version\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
                rf"\g<1>{new_version}\g<2>",
                content,
                count=1,
                flags=re.MULTILINE,
            )
            if new_content != content:
                path.write_text(new_content)
                updated.append(filename)
    except Exception:
        # Fallback to regex on any error
        try:
            content = path.read_text()
            new_content = re.sub(
                r'^(version\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
                rf"\g<1>{new_version}\g<2>",
                content,
                count=1,
                flags=re.MULTILINE,
            )
            if new_content != content:
                path.write_text(new_content)
                updated.append(filename)
        except Exception:
            pass

    if user_config and update_project_metadata(path, user_config):
        if filename not in updated:
            updated.append(filename)


def _update_cargo_version(
    filename: str, new_version: str, user_config, updated: List[str]
) -> None:
    """Update Cargo.toml version."""
    path = Path(filename)
    if path.exists():
        content = path.read_text()
        new_content = re.sub(
            r'^(version\s*=\s*")\d+\.\d+\.\d+(")',
            rf"\g<1>{new_version}\g<2>",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if new_content != content:
            path.write_text(new_content)
            updated.append(filename)
        if user_config and update_project_metadata(path, user_config):
            if filename not in updated:
                updated.append(filename)


def _update_csproj_versions(new_version: str, updated: List[str]) -> None:
    """Update all .csproj files."""
    for csproj in Path(".").glob("*.csproj"):
        content = csproj.read_text()
        new_content = re.sub(
            r"<Version>\d+\.\d+\.\d+</Version>",
            f"<Version>{new_version}</Version>",
            content,
            count=1,
        )
        if new_content != content:
            csproj.write_text(new_content)
            updated.append(str(csproj))


def _update_pom_xml(new_version: str, updated: List[str]) -> None:
    """Update pom.xml version."""
    pom_path = Path("pom.xml")
    if pom_path.exists():
        content = pom_path.read_text()
        new_content = re.sub(
            r"(<version>)\d+\.\d+\.\d+(</version>)",
            rf"\g<1>{new_version}\g<2>",
            content,
            count=1,
        )
        if new_content != content:
            pom_path.write_text(new_content)
            updated.append("pom.xml")


def _update_readme_metadata(user_config, new_version: str, updated: List[str]) -> None:
    """Update README.md metadata and badges."""
    readme_updated = False
    if user_config and update_readme_metadata(user_config):
        if Path("README.md").exists():
            readme_updated = True

    if update_badge_versions(Path("README.md"), new_version):
        readme_updated = True

    if readme_updated and "README.md" not in updated:
        updated.append("README.md")


def _update_init_py_versions(new_version: str, updated: List[str]) -> None:
    """Update __version__ in __init__.py files."""
    skip_dirs = (
        "venv",
        ".venv",
        ".venv_test",
        "site-packages",
        "build",
        "dist",
        "node_modules",
    )

    for init_file in Path(".").rglob("__init__.py"):
        parts = init_file.parts
        if any(p in parts for p in skip_dirs) or ".egg-info" in str(init_file):
            continue
        try:
            content = init_file.read_text()
            new_content = re.sub(
                r'^(__version__\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
                rf"\g<1>{new_version}\g<2>",
                content,
                count=1,
                flags=re.MULTILINE,
            )
            if new_content != content:
                init_file.write_text(new_content)
                updated.append(str(init_file))
        except Exception:
            pass


def sync_all_versions(new_version: str, user_config=None) -> List[str]:
    """Update version, author, and license in all detected project files."""
    updated: List[str] = []

    _update_version_file(new_version, updated)
    _update_json_version_file("package.json", new_version, user_config, updated)
    _update_json_version_file("composer.json", new_version, user_config, updated)
    _update_toml_version("pyproject.toml", new_version, user_config, updated)
    _update_cargo_version("Cargo.toml", new_version, user_config, updated)
    _update_csproj_versions(new_version, updated)
    _update_pom_xml(new_version, updated)
    _update_readme_metadata(user_config, new_version, updated)
    _update_init_py_versions(new_version, updated)

    return updated
