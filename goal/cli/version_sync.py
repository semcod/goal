"""Version management - version synchronization functions."""

import re
import subprocess
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


_DEPENDENCY_LOCK_REFRESHERS = (
    ("uv.lock", ("pyproject.toml",), ("uv", "lock"), ("uv.lock",)),
    ("poetry.lock", ("pyproject.toml",), ("poetry", "lock"), ("poetry.lock",)),
    ("pdm.lock", ("pyproject.toml",), ("pdm", "lock"), ("pdm.lock",)),
    (
        "package-lock.json",
        ("package.json",),
        ("npm", "install", "--package-lock-only"),
        ("package-lock.json",),
    ),
    (
        "pnpm-lock.yaml",
        ("package.json",),
        ("pnpm", "install", "--lockfile-only"),
        ("pnpm-lock.yaml",),
    ),
    ("Cargo.lock", ("Cargo.toml",), ("cargo", "generate-lockfile"), ("Cargo.lock",)),
)


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


def _warn_lock_refresh(message: str) -> None:
    import click

    click.echo(click.style(f"  Warning: {message}", fg="yellow"))


def _snapshot_paths(paths: tuple[str, ...]) -> dict[str, bytes | None]:
    return {path: Path(path).read_bytes() if Path(path).exists() else None for path in paths}


def _append_changed_paths(
    updated: List[str],
    before: dict[str, bytes | None],
    paths: tuple[str, ...],
) -> None:
    for path in paths:
        current = Path(path).read_bytes() if Path(path).exists() else None
        if current != before.get(path) and path not in updated:
            updated.append(path)


def _sync_dependency_lockfiles(updated: List[str]) -> None:
    """Refresh detected dependency lockfiles after manifest metadata changes."""
    for lockfile, manifests, command, tracked_paths in _DEPENDENCY_LOCK_REFRESHERS:
        if not Path(lockfile).exists() or not any(Path(manifest).exists() for manifest in manifests):
            continue

        before = _snapshot_paths(tracked_paths)
        cmd = list(command)
        label = " ".join(cmd)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            _warn_lock_refresh(
                f"{lockfile} exists but '{cmd[0]}' is not available; skipping lockfile refresh."
            )
            continue

        if result.returncode != 0:
            output = (result.stderr or result.stdout or f"{label} failed").strip()
            _warn_lock_refresh(
                f"{label} failed with: {output}; skipping {lockfile} refresh."
            )
            continue

        _append_changed_paths(updated, before, tracked_paths)


def _sync_uv_lock(updated: List[str]) -> None:
    """Backward-compatible wrapper for dependency lock refresh."""
    _sync_dependency_lockfiles(updated)


def _sync_dependency_locks_after_manifest_updates(updated: List[str]) -> None:
    """Refresh lockfiles after pyproject/package metadata changes."""
    _sync_dependency_lockfiles(updated)


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
    _sync_dependency_locks_after_manifest_updates(updated)
    _update_csproj_versions(new_version, updated)
    _update_pom_xml(new_version, updated)
    _update_readme_metadata(user_config, new_version, updated)
    _update_init_py_versions(new_version, updated)

    return updated
