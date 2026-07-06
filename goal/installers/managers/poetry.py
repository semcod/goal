"""Poetry package manager."""

from typing import Optional
from goal.installers.managers.base import AbstractPackageManager, InstallResult


class PoetryManager(AbstractPackageManager):
    """Poetry package manager implementation."""

    name = "poetry"
    priority = 30
    binary = "poetry"

    def install_editable(self, extras: list[str]) -> InstallResult:
        """Install package and its dependency groups using poetry.

        ``goal`` passes dependency *groups* (e.g. ``["dev"]``) — in Poetry those
        are installed via ``--with``, NOT ``--extras`` (which are PEP621-style
        optional extras and fail when handed a group name like ``dev``). A plain
        ``poetry install`` already pulls the non-optional groups (dev included),
        so it's the safe default; requested groups are added with ``--with``.
        """
        cmd = ["poetry", "install"]
        # "dev" is installed by a plain `poetry install`; only pass --with for
        # any additional groups to avoid "Group(s) not found" on missing groups.
        extra_groups = [g for g in (extras or []) if g != "dev"]
        if extra_groups:
            cmd += ["--with", ",".join(extra_groups)]
        return self._run(cmd)

    def install_requirements(self, req_file: str) -> InstallResult:
        """Poetry doesn't use requirements.txt directly - convert needed."""
        # Poetry uses pyproject.toml, not requirements.txt
        # Fallback to regular install
        return self._run(["poetry", "install"])

    def install_from_lockfile(self) -> Optional[InstallResult]:
        """Install from poetry.lock."""
        return self._run(["poetry", "install"])
