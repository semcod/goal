"""Update project dependencies to the latest available versions."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import click

from goal.package_managers import (
    PackageManager,
    get_available_package_managers,
    get_package_manager,
    get_update_all_command,
)

_LOCKFILE_MANAGERS = (
    ("uv.lock", "uv"),
    ("poetry.lock", "poetry"),
    ("pdm.lock", "pdm"),
    ("Pipfile.lock", "pipenv"),
    ("package-lock.json", "npm"),
    ("yarn.lock", "yarn"),
    ("pnpm-lock.yaml", "pnpm"),
    ("bun.lockb", "bun"),
    ("Cargo.lock", "cargo"),
    ("go.sum", "go"),
    ("Gemfile.lock", "bundler"),
    ("composer.lock", "composer"),
    ("mix.lock", "mix"),
    ("pubspec.lock", "pub"),
    ("Package.resolved", "swift"),
)


@dataclass
class DependencyUpdateResult:
    """Result of a dependency update operation."""

    manager: str
    command: str
    success: bool
    duration_s: float
    error: Optional[str] = None


def _run_update_command(command: str, cwd: str) -> DependencyUpdateResult:
    """Execute a dependency update command."""
    t0 = time.monotonic()
    try:
        subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return DependencyUpdateResult(
            manager="",
            command=command,
            success=True,
            duration_s=time.monotonic() - t0,
        )
    except subprocess.CalledProcessError as exc:
        error = (exc.stderr or exc.stdout or str(exc)).strip()
        return DependencyUpdateResult(
            manager="",
            command=command,
            success=False,
            duration_s=time.monotonic() - t0,
            error=error,
        )


def _select_managers_to_update(project_path: str) -> List[PackageManager]:
    """Return package managers that support project-wide dependency updates."""
    project_root = Path(project_path)
    available = {
        pm.name: pm for pm in get_available_package_managers(project_path)
    }
    selected: List[PackageManager] = []
    seen_names: set[str] = set()

    for lockfile, manager_name in _LOCKFILE_MANAGERS:
        if not (project_root / lockfile).exists():
            continue
        pm = available.get(manager_name) or get_package_manager(manager_name)
        if not pm or pm.name in seen_names:
            continue
        if get_update_all_command(pm, project_root) is None:
            continue
        selected.append(pm)
        seen_names.add(pm.name)

    if selected:
        return selected

    by_language: dict[str, PackageManager] = {}
    for pm in sorted(available.values(), key=lambda item: item.priority, reverse=True):
        if pm.language in by_language:
            continue
        if get_update_all_command(pm, project_root) is None:
            continue
        by_language[pm.language] = pm

    return list(by_language.values())


def update_project_dependencies(
    project_path: str = ".",
    *,
    yes: bool = False,
    dry_run: bool = False,
) -> List[DependencyUpdateResult]:
    """Update all detected project dependencies to their latest versions."""
    project_root = Path(project_path).resolve()
    managers = _select_managers_to_update(str(project_root))

    if not managers:
        click.echo(
            click.style(
                "No supported package manager found for dependency updates.",
                fg="yellow",
            )
        )
        return []

    click.echo(
        click.style(
            f"\n📦 Updating dependencies in {project_root}",
            fg="cyan",
            bold=True,
        )
    )

    planned = []
    for pm in managers:
        command = get_update_all_command(pm, project_root)
        if command:
            planned.append((pm, command))

    if dry_run:
        for pm, command in planned:
            click.echo(f"  Would run ({pm.name}): {command}")
        return []

    if not yes:
        click.echo("Detected package managers:")
        for pm, command in planned:
            click.echo(f"  - {pm.name}: {command}")
        if not click.confirm("Update dependencies to latest versions?", default=True):
            click.echo(click.style("Skipped dependency updates.", fg="yellow"))
            return []

    results: List[DependencyUpdateResult] = []
    for pm, command in planned:
        click.echo(click.style(f"  ↻ {pm.name}: {command}", fg="cyan"))
        result = _run_update_command(command, str(project_root))
        result.manager = pm.name
        results.append(result)

        if result.success:
            click.echo(
                click.style(
                    f"  ✓ {pm.name} updated ({result.duration_s:.1f}s)",
                    fg="green",
                )
            )
        else:
            click.echo(
                click.style(
                    f"  ✗ {pm.name} update failed ({result.duration_s:.1f}s)",
                    fg="red",
                )
            )
            if result.error:
                click.echo(click.style(f"    {result.error}", fg="red"))

    return results
