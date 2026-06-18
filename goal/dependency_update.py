"""Update project dependencies to the latest available versions."""

from __future__ import annotations

import os
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

_SKIP_DIRS = frozenset(
    {
        ".git",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".urisys",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "site-packages",
        "venv",
    }
)

_PROJECT_MARKERS = tuple({lockfile for lockfile, _ in _LOCKFILE_MANAGERS}) + (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "composer.json",
    "mix.exs",
    "pubspec.yaml",
    "Package.swift",
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
    seen_languages: set[str] = set()

    for lockfile, manager_name in _LOCKFILE_MANAGERS:
        if not (project_root / lockfile).exists():
            continue
        pm = available.get(manager_name) or get_package_manager(manager_name)
        if not pm or pm.name in seen_names:
            continue
        if pm.language in seen_languages:
            continue
        if get_update_all_command(pm, project_root) is None:
            continue
        selected.append(pm)
        seen_names.add(pm.name)
        seen_languages.add(pm.language)

    if selected:
        return selected

    # uv.lock without poetry.lock — do not fall back to poetry/pip.
    if (project_root / "uv.lock").exists():
        uv_pm = available.get("uv") or get_package_manager("uv")
        if uv_pm and get_update_all_command(uv_pm, project_root):
            return [uv_pm]

    by_language: dict[str, PackageManager] = {}
    for pm in sorted(available.values(), key=lambda item: item.priority, reverse=True):
        if pm.language in by_language:
            continue
        if get_update_all_command(pm, project_root) is None:
            continue
        lockfile = next(
            (lf for lf, name in _LOCKFILE_MANAGERS if name == pm.name),
            None,
        )
        if lockfile and not (project_root / lockfile).exists():
            continue
        by_language[pm.language] = pm

    return list(by_language.values())


def _path_has_skipped_dir(path: Path) -> bool:
    return bool(set(path.parts) & _SKIP_DIRS)


def _iter_project_marker_files(project_root: Path):
    """Yield manifest/lockfile paths while pruning ignored directories."""
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = sorted(
            dirname for dirname in dirnames if dirname not in _SKIP_DIRS
        )
        current = Path(dirpath)
        for filename in filenames:
            if filename in _PROJECT_MARKERS:
                yield current / filename


def discover_dependency_project_roots(
    project_path: str = ".",
    *,
    recursive: bool = False,
) -> List[Path]:
    """Return project roots that have updatable dependency managers."""
    project_root = Path(project_path).resolve()
    candidate_roots: dict[str, Path] = {}

    def add_candidate(directory: Path) -> None:
        candidate_roots.setdefault(str(directory.resolve()), directory.resolve())

    add_candidate(project_root)

    root_has_managers = bool(_select_managers_to_update(str(project_root)))
    if recursive or not root_has_managers:
        for found in _iter_project_marker_files(project_root):
            if _path_has_skipped_dir(found):
                continue
            add_candidate(found.parent)

    updatable: List[Path] = []
    for path in sorted(candidate_roots.values(), key=lambda item: str(item)):
        if _select_managers_to_update(str(path)):
            updatable.append(path)
    return updatable


def _format_project_label(project_root: Path) -> str:
    """Return a stable, human-friendly path label for prompts."""
    try:
        return str(project_root.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(project_root.resolve())


def _update_dependencies_in_root(
    project_root: Path,
    *,
    auto: bool,
    dry_run: bool,
) -> List[DependencyUpdateResult]:
    managers = _select_managers_to_update(str(project_root))
    if not managers:
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

    if not auto:
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


def update_project_dependencies(
    project_path: str = ".",
    *,
    yes: bool = False,
    dry_run: bool = False,
    recursive: bool = False,
    interactive: bool = False,
) -> List[DependencyUpdateResult]:
    """Update all detected project dependencies to their latest versions."""
    project_roots = discover_dependency_project_roots(
        project_path,
        recursive=recursive,
    )

    if not project_roots:
        click.echo(
            click.style(
                "No supported package manager found for dependency updates.",
                fg="yellow",
            )
        )
        return []

    if len(project_roots) > 1:
        names = ", ".join(path.name for path in project_roots[:5])
        suffix = "..." if len(project_roots) > 5 else ""
        click.echo(
            click.style(
                f"  📁 Found {len(project_roots)} subproject(s) with dependencies: {names}{suffix}",
                fg="cyan",
            )
        )

    auto = yes and not interactive
    if len(project_roots) > 1 and not auto and not interactive:
        if not click.confirm(
            f"Update dependencies in all {len(project_roots)} projects?",
            default=False,
        ):
            click.echo(click.style("Skipped dependency updates.", fg="yellow"))
            return []

    results: List[DependencyUpdateResult] = []
    for project_root in project_roots:
        project_auto = auto
        if interactive:
            label = _format_project_label(project_root)
            if not click.confirm(f"Process project {label}?", default=True):
                click.echo(
                    click.style(f"  ⏭️  Skipped {project_root.name}", fg="yellow")
                )
                continue
            project_auto = True

        results.extend(
            _update_dependencies_in_root(
                project_root,
                auto=project_auto,
                dry_run=dry_run,
            )
        )
    return results
