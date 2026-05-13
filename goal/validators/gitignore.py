"""Gitignore management utilities."""

import os
from typing import Set, Tuple


def load_gitignore(gitignore_path: str = ".gitignore") -> Tuple[Set[str], Set[str]]:
    """Load .gitignore patterns, returning (ignored_patterns, whitelisted_patterns)."""
    ignored = set()
    whitelisted = set()

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("!"):
                    whitelisted.add(line[1:])
                else:
                    ignored.add(line)

    return ignored, whitelisted


def save_gitignore(ignored: Set[str], gitignore_path: str = ".gitignore") -> None:
    """Save patterns to .gitignore."""
    # Read existing content to preserve comments and order
    existing_lines = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            existing_lines = f.readlines()

    # Find where to insert new patterns (before any existing patterns)
    insert_idx = 0
    for i, line in enumerate(existing_lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_idx = i
            break

    # Insert new patterns
    new_patterns = [
        p + "\n" for p in sorted(ignored) if p not in "".join(existing_lines)
    ]
    if new_patterns:
        existing_lines[insert_idx:insert_idx] = new_patterns

        with open(gitignore_path, "w") as f:
            f.writelines(existing_lines)
