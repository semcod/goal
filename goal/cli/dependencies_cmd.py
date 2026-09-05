"""Internal package freshness without bootstrap, self-update or publication."""

import json
from pathlib import Path
import subprocess

import click

from goal.cli import main
from goal.internal_dependencies import audit, read_catalog, update_lock


@main.command("dependencies")
@click.option(
    "--catalog",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Reviewed goal.internal-dependencies/v1 JSON package allowlist (PyPI/SemVer).",
)
@click.option(
    "--project",
    default=".",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--check",
    is_flag=True,
    help="Exit 1 when any catalogued locked package is not current.",
)
@click.option(
    "--update",
    is_flag=True,
    help="Resolve and verify a new uv.lock in a clean standalone checkout.",
)
@click.pass_context
def dependencies(ctx, catalog, project, check, update):
    """Audit catalogued uv packages; print JSON and exact stable upgrade targets.

    An explicit --update changes only uv.lock. Run the project's tests and sync
    its environment before delivery. Source overrides and governed updates need
    their repository workflow. Other ecosystems and version schemes are not
    supported by this first catalog contract. Global --dry-run never writes.
    """
    if check and update:
        raise click.UsageError("Choose --check or --update")
    try:
        report = audit(project, read_catalog(catalog))
        if update and not ctx.obj.get("dry_run"):
            report = update_lock(project, report)
        click.echo(json.dumps(report, indent=2))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        raise click.ClickException(str(error)) from error
    if check and not report["fresh"]:
        ctx.exit(1)
