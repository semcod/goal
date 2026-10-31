"""Run the protected workflow for changes and configured pending releases.

Also backs the ``goal -a ./*`` form: when ``-a``/``--all`` is passed together
with one or more path/glob arguments, :class:`GoalGroup` routes the invocation
to this command (see ``goal/cli/__init__.py``).
"""

import json
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
            identity = os.path.realpath(m)
            if os.path.isdir(m) and identity not in seen:
                seen.add(identity)
                resolved.append(m)
    return sorted(resolved)


def _is_git_repo(path: str) -> bool:
    """Return True when ``path`` is the working tree of a git repository."""
    try:
        result = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"],
                                capture_output=True, text=True, timeout=10)
        return result.returncode == 0 and os.path.realpath(result.stdout.strip()) == os.path.realpath(path)
    except (OSError, subprocess.TimeoutExpired):
        return False


def _has_uncommitted_changes(path: str) -> bool:
    """Return True when ``path`` has staged, unstaged, or untracked changes."""
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", path, "-c", "core.fsmonitor=false", "status", "--porcelain"],
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


def _pending_release(path: str, config_path=None) -> bool:
    """Query the shared planner in an isolated child; never bootstrap the target."""
    command = [sys.executable, "-I", "-m", "goal.publish.state", "--project", os.path.abspath(path)]
    if config_path:
        command += ["--project-config", config_path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        plan = json.loads(result.stdout)
        return (result.returncode == 0 and plan.get("schema") == "goal.release-plan/v1"
                and plan.get("ready_for_goal") is True and plan.get("authorization_granted") is False)
    except (OSError, subprocess.TimeoutExpired, ValueError, AttributeError):
        return False


def _run_goal_a(path: str, dry_run: bool, options=None) -> int:
    """Run ``goal -a`` (the full workflow) inside ``path`` as a subprocess."""
    options = options or {}
    cmd = [sys.executable, "-I", "-m", "goal", "-a"]
    for key, flag in (("koru", "-k"), ("no_publish", "--no-publish"),
                      ("force_publish_explicit", "--force-publish")):
        if options.get(key):
            cmd.append(flag)
    for key, flag in (("delivery_mode", "--delivery-mode"), ("version", "--target-version"),
                      ("config_path", "--config")):
        if options.get(key) is not None:
            cmd += [flag, str(options[key])]
    if dry_run:
        cmd.append("--dry-run")
    click.echo(click.style(f"\n=== goal -a → {path} ===", fg="cyan", bold=True))
    return subprocess.run(cmd, cwd=path).returncode


@main.command(name="all")
@click.argument("paths", nargs=-1)
@click.pass_context
def all_(ctx, paths) -> None:
    """Run ``goal -a`` for changes and configured clean pending Python releases.

    PATHS are directories or globs (default: ``*`` — all entries in the current
    directory). A read-only plan also includes clean, synchronized public-PyPI
    releases waiting for publication. Other clean repos are skipped. Equivalent to
    the ``goal -a ./*`` shorthand.
    """
    options = dict(ctx.obj or {})
    config_path = ctx.parent.params.get("config_path") if ctx.parent else None
    if config_path:
        options["config_path"] = os.path.abspath(config_path)
    dry_run = options.get("dry_run", False)
    dirty, clean, non_repo = _classify_targets(list(paths))
    pending = [] if options.get("no_publish") else [path for path in clean if _pending_release(path, options.get("config_path"))]
    selected = dirty + pending

    if not selected:
        click.echo(
            click.style(
                "No sub-repositories with changes or ready pending releases found.", fg="yellow"
            )
        )
        return

    click.echo(
        click.style(
            f"\nProjects with changes or pending releases ({len(selected)}):",
            fg="cyan",
            bold=True,
        )
    )
    for d in selected:
        click.echo(f"  • {d}")
    if len(clean) > len(pending):
        click.echo(
            click.style(f"Skipping {len(clean) - len(pending)} other clean repo(s).", fg="bright_black")
        )

    # Batch gate: list + one confirmation, skipped only with an explicit -y/--yes
    # (or when nothing will actually happen because of --dry-run).
    if not dry_run and not _explicit_yes():
        if not confirm(f"Run `goal -a` on these {len(selected)} project(s)?"):
            click.echo(click.style("Aborted.", fg="red"))
            ctx.exit(1)

    results: List[Tuple[str, int]] = []
    for d in selected:
        code = _run_goal_a(d, dry_run, options)
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
