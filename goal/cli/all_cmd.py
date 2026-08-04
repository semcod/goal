"""``goal all`` — run the full ``goal -a`` workflow across every git repository
with uncommitted changes under the given paths (monorepo sweep).

Also backs the ``goal -a ./*`` form: when ``-a``/``--all`` is passed together
with one or more path/glob arguments, :class:`GoalGroup` routes the invocation
to this command (see ``goal/cli/__init__.py``).
"""

import os
import subprocess
import sys
from glob import glob as _glob
from typing import List, Tuple

import click

from goal.cli import main
from goal.cli_helpers import confirm


_GLOB_CHARS = "*?["


def _expand_targets(paths: List[str]) -> List[str]:
    """Resolve CLI path/glob arguments into a sorted, de-duplicated dir list.

    An empty ``paths`` defaults to ``*`` (every entry in the current directory),
    so ``goal all`` with no arguments sweeps the current folder's sub-projects.
    """
    if not paths:
        paths = ["*"]

    resolved: List[str] = []
    seen = set()
    for p in paths:
        if any(c in p for c in _GLOB_CHARS):
            matches = _glob(p)
        elif os.path.isdir(p):
            matches = [p]
        else:
            matches = []
        for m in matches:
            m = os.path.normpath(m)
            if os.path.isdir(m) and m not in seen:
                seen.add(m)
                resolved.append(m)
    return sorted(resolved)


def _is_git_repo(path: str) -> bool:
    """Return True when ``path`` is the working tree of a git repository."""
    return os.path.isdir(os.path.join(path, ".git"))


def _has_uncommitted_changes(path: str) -> bool:
    """Return True when ``path`` has staged, unstaged, or untracked changes."""
    result = subprocess.run(
        ["git", "-C", path, "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _classify_targets(
    paths: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """Split resolved targets into (dirty repos, clean repos, non-repos)."""
    dirty: List[str] = []
    clean: List[str] = []
    non_repo: List[str] = []
    for d in _expand_targets(paths):
        if not _is_git_repo(d):
            non_repo.append(d)
        elif _has_uncommitted_changes(d):
            dirty.append(d)
        else:
            clean.append(d)
    return dirty, clean, non_repo


def _explicit_yes() -> bool:
    """True only when the user typed ``-y``/``--yes`` (NOT merely ``-a``).

    The batch confirmation must still appear for ``goal -a ./*`` even though
    ``-a`` sets the global auto-confirm for the *inner* per-project runs.
    """
    from goal.cli import _has_cli_flag

    return _has_cli_flag(sys.argv, "y", "--yes")


def _run_goal_a(path: str, dry_run: bool) -> int:
    """Run ``goal -a`` (the full workflow) inside ``path`` as a subprocess."""
    cmd = [sys.executable, "-m", "goal", "-a"]
    if dry_run:
        cmd.append("--dry-run")
    click.echo(click.style(f"\n=== goal -a → {path} ===", fg="cyan", bold=True))
    return subprocess.run(cmd, cwd=path).returncode


@main.command(name="all")
@click.argument("paths", nargs=-1)
@click.pass_context
def all_(ctx, paths) -> None:
    """Run ``goal -a`` in every sub-repo with uncommitted changes.

    PATHS are directories or globs (default: ``*`` — all entries in the current
    directory). Only git repositories that have uncommitted changes are
    processed; clean repos and non-git directories are skipped. Equivalent to
    the ``goal -a ./*`` shorthand.
    """
    dry_run = ctx.obj.get("dry_run", False)
    dirty, clean, non_repo = _classify_targets(list(paths))

    if not dirty:
        click.echo(
            click.style(
                "No sub-repositories with uncommitted changes found.", fg="yellow"
            )
        )
        return

    click.echo(
        click.style(
            f"\nProjects with uncommitted changes ({len(dirty)}):",
            fg="cyan",
            bold=True,
        )
    )
    for d in dirty:
        click.echo(f"  • {d}")
    if clean:
        click.echo(
            click.style(f"Skipping {len(clean)} clean repo(s).", fg="bright_black")
        )

    # Batch gate: list + one confirmation, skipped only with an explicit -y/--yes
    # (or when nothing will actually happen because of --dry-run).
    if not dry_run and not _explicit_yes():
        if not confirm(f"Run `goal -a` on these {len(dirty)} project(s)?"):
            click.echo(click.style("Aborted.", fg="red"))
            ctx.exit(1)

    results: List[Tuple[str, int]] = []
    for d in dirty:
        code = _run_goal_a(d, dry_run)
        results.append((d, code))

    succeeded = [d for d, c in results if c == 0]
    failed = [d for d, c in results if c != 0]

    click.echo(click.style("\n=== goal all summary ===", fg="cyan", bold=True))
    click.echo(click.style(f"  ✅ {len(succeeded)} succeeded", fg="green"))
    if failed:
        click.echo(click.style(f"  ❌ {len(failed)} failed:", fg="red", bold=True))
        for d in failed:
            click.echo(click.style(f"     • {d}", fg="red"))
        ctx.exit(1)


__all__ = ["all_"]
