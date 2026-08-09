"""Utility commands (status, init, info, version) - extracted from cli.py."""

import click
from pathlib import Path

from goal.git_ops import (
    get_remote_branch,
    get_staged_files,
    get_unstaged_files,
    get_working_tree_files,
    run_git,
    ensure_git_repository,
    validate_repo_url,
    clone_repository,
)
from goal.formatter import format_status_output
from goal.config import init_config
from goal.user_config import get_user_config, initialize_user_config
from goal.project_bootstrap import detect_project_types_deep, bootstrap_project
from goal.package_managers import (
    detect_package_managers,
    detect_project_language,
    suggest_package_managers,
)
from goal.version_validation import (
    format_validation_results,
    update_badge_versions,
    validate_project_versions,
)
from goal.cli import main
from goal.cli.version import (
    get_current_version,
    bump_version,
    detect_project_types,
    format_version_decision,
    resolve_version_decision,
    sync_all_versions,
)


@main.command()
@click.option(
    "--markdown/--ascii", default=True, help="Output format (default: markdown)"
)
@click.pass_context
def status(ctx, markdown) -> None:
    """Show current git status and version info."""
    version = get_current_version()
    branch = get_remote_branch()
    staged = get_staged_files()
    unstaged = get_unstaged_files()

    if markdown or ctx.obj.get("markdown"):
        md_output = format_status_output(
            version=version,
            branch=branch,
            staged_files=staged if staged and staged != [""] else [],
            unstaged_files=unstaged,
        )
        click.echo(md_output)
    else:
        click.echo(f"Version: {click.style(version, fg='cyan')}")
        click.echo(f"Branch: {click.style(branch, fg='cyan')}")

        if staged and staged != [""]:
            click.echo(f"\nStaged files ({len(staged)}):")
            for f in staged:
                click.echo(f"  {click.style('+', fg='green')} {f}")

        if unstaged:
            click.echo(f"\nUnstaged files ({len(unstaged)}):")
            for f in unstaged:
                click.echo(f"  {click.style('!', fg='yellow')} {f}")


@main.command()
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.pass_context
def init(ctx, force) -> None:
    """Initialize goal in current repository (creates VERSION, CHANGELOG.md, and goal.yaml)."""
    # Ensure git repository
    if not ensure_git_repository(auto=True):
        return

    # Initialize configuration
    config = init_config(force=force)

    # Detect project types
    project_types = detect_project_types()
    if project_types:
        click.echo(f"Detected project types: {', '.join(project_types)}")

    # Initialize user config if not exists
    user_config = get_user_config()
    if not user_config.is_initialized():
        initialize_user_config()

    click.echo(click.style("✓ Goal initialized successfully!", fg="green", bold=True))


@main.command()
def info() -> None:
    """Show detailed project information and version status."""
    project_types = detect_project_types()
    version = get_current_version()
    branch = get_remote_branch()

    click.echo(click.style("=== Project Info ===", fg="cyan", bold=True))
    click.echo(f"Version: {click.style(version, fg='green')}")
    click.echo(f"Branch: {click.style(branch, fg='cyan')}")

    if project_types:
        click.echo(f"Project types: {', '.join(project_types)}")
    else:
        click.echo("No project types detected.")


@main.command()
@click.argument("bump_type", type=click.Choice(["major", "minor", "patch"]))
def version(bump_type):
    """Bump version and sync across all project files."""
    current = get_current_version()
    new_version = bump_version(current, bump_type)

    user_config = get_user_config()
    updated = sync_all_versions(new_version, user_config)

    click.echo(
        click.style(
            f"Version bumped: {current} -> {new_version}", fg="green", bold=True
        )
    )
    click.echo(f"Updated files: {', '.join(updated)}")

    # Stage the changes
    for f in updated:
        run_git("add", f)

    click.echo(
        click.style("✓ Version changes staged. Run 'goal push' to commit.", fg="cyan")
    )


@main.command()
@click.option("--language", default=None, help="Filter by language")
@click.option("--available", is_flag=True, help="Show only available package managers")
def package_managers(language, available):
    """Show detected and available package managers for the current project."""
    if language:
        detected = detect_package_managers(".")
        by_lang = [pm for pm in detected if pm.language == language]
        click.echo(f"Package managers for {language}:")
        for pm in by_lang:
            click.echo(f"  - {pm.name}")
    else:
        detected = detect_package_managers(".")
        project_lang = detect_project_language(".")
        suggested = suggest_package_managers(".")

        click.echo(click.style("=== Package Managers ===", fg="cyan", bold=True))
        click.echo(f"Detected: {', '.join(pm.name for pm in detected)}")
        if project_lang:
            click.echo(f"Project language: {project_lang}")
        if suggested:
            click.echo(f"Suggested: {', '.join(suggested)}")


@main.command()
@click.option("--update-badges", is_flag=True, help="Update README badge versions")
@click.pass_context
def check_versions(ctx, update_badges):
    """Check version consistency across registries and README badges."""
    current_version = get_current_version()
    project_types = detect_project_types()
    results = {}

    click.echo(f"Current version: {click.style(current_version, fg='cyan')}")

    if project_types:
        click.echo(f"Project types: {', '.join(project_types)}")

        results = validate_project_versions(project_types, current_version)
        for line in format_validation_results(results):
            click.echo(line)
    else:
        click.echo("No project types detected.")

    registry_versions = {
        (
            f"{result.get('registry') or project_type}:"
            f"{result.get('package_name') or 'unknown-package'}"
        ): result["registry_version"]
        for project_type, result in results.items()
        if result.get("registry_version")
    }
    from goal.publish.changes import (
        analyze_publishable_changes,
        committed_unreleased_source_files,
    )

    pending_files = list(
        dict.fromkeys([*get_staged_files(), *get_working_tree_files()])
    )
    change_report = analyze_publishable_changes(pending_files, project_types)
    release_required = change_report.has_changes or bool(
        committed_unreleased_source_files(project_types)
    )
    try:
        decision = resolve_version_decision(
            bump=ctx.obj.get("bump", "patch"),
            target_version=ctx.obj.get("version"),
            config=ctx.obj.get("config"),
            project_types=project_types,
            registry_versions=registry_versions,
            release_required=release_required,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    for line in format_version_decision(decision):
        click.echo(line)

    badge_version = (
        decision.target_version
        if decision.reason in {"already-bumped", "partial-bump", "explicit-target"}
        else decision.current_version
    )
    if update_badges and update_badge_versions(Path("README.md"), badge_version):
        click.echo(f"Updated README badges to {badge_version}")

    if decision.local_drift:
        raise click.ClickException(
            "Local version files are inconsistent; run the governed release "
            "sync or set an explicit target."
        )


@main.command()
@click.argument("url")
@click.argument("directory", required=False)
@click.pass_context
def clone(ctx, url, directory):
    """Clone a git repository."""
    if not validate_repo_url(url):
        click.echo(click.style(f"Invalid URL: {url}", fg="red"))
        ctx.exit(1)

    target = directory or url.split("/")[-1].replace(".git", "")

    click.echo(f"Cloning {url} into {target}...")
    result = clone_repository(url, target)

    if result:
        click.echo(click.style(f"✓ Cloned to {target}", fg="green"))
    else:
        click.echo(click.style("✗ Clone failed", fg="red"))


@main.command()
@click.option("--yes", "-y", is_flag=True, help="Auto-confirm")
@click.option("--path", default=".", help="Path to bootstrap")
def bootstrap(yes, path):
    """Bootstrap project environments (install deps, scaffold tests)."""
    root = Path(path).resolve()
    detected = detect_project_types_deep(root)

    if not detected:
        click.echo("No project types detected.")
        return

    for ptype, dirs in detected.items():
        for project_dir in dirs:
            bootstrap_project(project_dir, ptype, yes=yes)

    click.echo(click.style("✓ Bootstrap complete", fg="green"))


__all__ = [
    "status",
    "init",
    "info",
    "version",
    "package_managers",
    "check_versions",
    "clone",
    "bootstrap",
]
