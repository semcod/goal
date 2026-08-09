"""Push workflow stages - version handling."""

from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence

import click

if TYPE_CHECKING:
    from goal.cli.version_state import VersionDecision


def _get_version_module():
    """Lazy import version functions to avoid circular imports."""
    from goal.cli.version import get_current_version, bump_version, sync_all_versions

    return get_current_version, bump_version, sync_all_versions


def sync_all_versions_wrapper(
    new_version: str,
    user_config: Optional[Dict],
    version_decision: Optional["VersionDecision"] = None,
) -> List[str]:
    """Wrapper to sync versions to all project files."""
    _, _, sync_all_versions = _get_version_module()
    specs = version_decision.managed_specs if version_decision is not None else None
    return sync_all_versions(
        new_version,
        user_config,
        version_specs=specs,
        strict=version_decision is not None,
    )


def handle_version_sync(
    new_version: str,
    no_version_sync: bool,
    user_config: Optional[Dict],
    yes: bool,
    version_decision: Optional["VersionDecision"] = None,
) -> None:
    """Sync versions to all project files."""
    _, _, sync_all_versions = _get_version_module()

    if not no_version_sync:
        specs = version_decision.managed_specs if version_decision is not None else None
        updated_files = sync_all_versions(
            new_version,
            user_config,
            version_specs=specs,
            strict=version_decision is not None,
        )
        # Use stage_paths with chunking to avoid "Argument list too long"
        # Lazy import to avoid circular dependency
        from goal.cli import stage_paths

        stage_paths(updated_files)
        for f in updated_files:
            click.echo(click.style(f"✓ Updated {f} to {new_version}", fg="green"))
    else:
        if version_decision is None:
            Path("VERSION").write_text(new_version + "\n")
            # Lazy import to avoid circular dependency
            from goal.cli import stage_paths

            stage_paths(["VERSION"])
            click.echo(click.style(f"✓ Updated VERSION to {new_version}", fg="green"))
        else:
            from goal.cli.version_state import validate_version_sources

            validate_version_sources(version_decision.managed_specs, new_version)
            click.echo(
                click.style(
                    "✓ Existing version files match target (--no-version-sync)",
                    fg="green",
                )
            )


def get_version_info(
    current_version: Optional[str] = None,
    bump: str = "patch",
    target_version: Optional[str] = None,
    config=None,
    project_types: Sequence[str] = (),
    registry_versions=None,
    include_decision: bool = False,
    release_required: bool = True,
) -> tuple:
    """Get current and new version info."""
    get_current_version, bump_version, _ = _get_version_module()
    if current_version is not None and config is None and not project_types:
        new_version = target_version or bump_version(current_version, bump)
        return current_version, new_version

    from goal.cli.version_state import resolve_version_decision

    decision = resolve_version_decision(
        bump=bump,
        target_version=target_version,
        config=config,
        project_types=project_types,
        registry_versions=registry_versions,
        release_required=release_required,
    )
    if include_decision:
        return decision.current_version, decision.target_version, decision
    return decision.current_version, decision.target_version
