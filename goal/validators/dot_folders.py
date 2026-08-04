"""Dot folder validation and management."""

import os
from pathlib import Path
from typing import List

from goal.validators.gitignore import load_gitignore, save_gitignore
from goal.validators.exceptions import DotFolderError


# Common safe dot files that shouldn't trigger warnings
_SAFE_DOT_FILES = {
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".git",
    ".github",
    ".gitlab-ci.yml",
    ".pre-commit-config.yaml",
}

# Default problematic dot folders/files
_DEFAULT_PROBLEMATIC = {
    ".idea",
    ".vscode",
    ".DS_Store",
    "Thumbs.db",
    ".pytest_cache",
    ".coverage",
    ".mypy_cache",
    ".tox",
    ".nox",
    ".venv",
    ".env",
    ".python-version",
    ".ruff_cache",
    ".cursorignore",
    ".cursorindexingignore",
}


def _is_dot_path(path: Path) -> bool:
    """True if the file or any parent (except root) is a dot-name."""
    return path.name.startswith(".") or any(p.startswith(".") for p in path.parts[:-1])


def _is_safe_path(path: Path) -> bool:
    """True if the path or a parent is in the safe-list."""
    return path.name in _SAFE_DOT_FILES or any(
        p in _SAFE_DOT_FILES for p in path.parts[:-1]
    )


def _is_whitelisted_path(path: Path, whitelist: set) -> bool:
    """True if the path matches any whitelist pattern."""
    return any(
        path.match(pattern)
        or any(p.match(pattern) for p in [path] + list(path.parents))
        for pattern in whitelist
    )


def _matches_problematic(path: Path, problematic_folders: set) -> bool:
    """True if the path name or prefix matches a problematic folder."""
    name = path.name
    path_str = str(path)
    return name in problematic_folders or any(
        name.startswith(f) or path_str.startswith(f + "/") for f in problematic_folders
    )


def check_dot_folders(files: List[str], config) -> List[str]:
    """Check for dot folders/files that should be in .gitignore.

    Returns:
        List of dot folders/files that need to be added to .gitignore
    """
    ignored, whitelisted = load_gitignore()

    known_dot_folders = (
        config.get("advanced.file_validation.known_dot_folders", []) if config else []
    )
    problematic_folders = _DEFAULT_PROBLEMATIC | set(known_dot_folders)

    problematic_found = []
    for file_path in files:
        path = Path(file_path)
        if not _is_dot_path(path):
            continue
        if _is_safe_path(path):
            continue
        if _is_whitelisted_path(path, whitelisted):
            continue
        if any(path.match(pattern) for pattern in ignored):
            continue
        if _matches_problematic(path, problematic_folders):
            problematic_found.append(str(path))

    return problematic_found


def manage_dot_folders(files: List[str], config, dry_run: bool = False) -> None:
    """Proactively manage dot folders in .gitignore.

    Args:
        files: List of staged files to check
        config: GoalConfig object
        dry_run: If True, only report what would be done

    Raises:
        DotFolderError: If problematic dot folders are found
    """
    import click
    from goal.git_ops import run_git

    problematic = check_dot_folders(files, config)

    if not problematic:
        return

    # Get configuration
    auto_add = (
        config.get("advanced.file_validation.auto_add_dot_folders", True)
        if config
        else True
    )

    if auto_add and not dry_run:
        # Load current ignored patterns
        ignored, _ = load_gitignore()

        # Add problematic patterns
        for item in problematic:
            # Add directory pattern if it's a directory
            if os.path.isdir(item):
                ignored.add(f"{item}/")
            else:
                ignored.add(item)

        # Save updated .gitignore
        save_gitignore(ignored)

        click.echo(
            click.style(
                f"✅ Added {len(problematic)} dot folder(s)/file(s) to .gitignore: {', '.join(problematic)}",
                fg="green",
            )
        )

        # Re-stage files to unstage the newly ignored ones
        run_git("add", ".gitignore")
        run_git("update-index", "--refresh")

        # Show which files were unstaged
        for item in problematic:
            if os.path.exists(item):
                run_git("reset", "--", item)
                click.echo(click.style(f"  → Unstaged: {item}", fg="yellow"))
    else:
        # Just report the issue
        raise DotFolderError(problematic)
