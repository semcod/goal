"""Filesystem boundaries shared by automatic version scans."""

import os
from pathlib import Path
from typing import Iterable, Iterator


def project_version_files(skip_dirs: Iterable[str]) -> Iterator[Path]:
    """Walk this project without entering other checkouts or following links.

    A nested .git directory or gitfile marks a separate repository, including
    submodules and linked worktrees. Even an unavailable gitfile target is a
    boundary; automatic discovery does not need to resolve Git metadata.
    Explicitly configured version sources are handled by their existing API.
    """
    excluded = set(skip_dirs) | {".git", ".worktrees"}
    for dirpath, dirnames, filenames in os.walk(".", followlinks=False):
        directory = Path(dirpath)
        dirnames[:] = [
            name for name in dirnames
            if name not in excluded
            and not name.endswith(".egg-info")
            and not (directory / name).is_symlink()
            and not os.path.lexists(directory / name / ".git")
        ]
        for name in filenames:
            path = directory / name
            if not path.is_symlink():
                yield path
