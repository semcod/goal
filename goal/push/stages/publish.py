"""Push workflow stages - publishing."""

import click

from goal.cli.publish import publish_project
from goal.cli import confirm
from goal.publish.changes import PublishChangeReport, analyze_publishable_changes


def _format_skip_message(report: PublishChangeReport) -> str:
    """Build a transparent skip explanation for the user."""
    lines = [
        "  No package source changes detected — publish skipped.",
        f"  Registry types checked: {', '.join(report.project_types) or '(none)'}",
    ]
    if report.non_publishable_files:
        preview = report.non_publishable_files[:8]
        suffix = (
            f" (+{len(report.non_publishable_files) - len(preview)} more)"
            if len(report.non_publishable_files) > len(preview)
            else ""
        )
        lines.append(
            "  Staged files (metadata/docs/tests only): "
            + ", ".join(preview)
            + suffix
        )
    lines.append("  Tip: use --force-publish to publish anyway.")
    return "\n".join(lines)


def handle_publish(
    project_types: list,
    new_version: str,
    yes: bool,
    no_publish: bool = False,
    config=None,
    staged_files: list[str] | None = None,
    force_publish: bool = False,
) -> tuple[bool, PublishChangeReport | None]:
    """Publish to package registries.

    Returns (publish_success, change_report). When publish is skipped because there
    are no package source changes, publish_success is False and the report explains why.
    """
    if no_publish:
        click.echo(
            click.style("  🤖 AUTO: Skipping publish (--no-publish)", fg="yellow")
        )
        return False, None

    change_report: PublishChangeReport | None = None
    if staged_files is not None and not force_publish:
        change_report = analyze_publishable_changes(staged_files, project_types)
        if not change_report.has_changes:
            click.echo(
                click.style(
                    "\n📦 Skipping publish — no package source changes",
                    fg="yellow",
                    bold=True,
                )
            )
            click.echo(_format_skip_message(change_report))
            return False, change_report

    if not yes:
        if not confirm(f"Publish version {new_version}?"):
            click.echo(
                click.style("  🤖 AUTO: Skipping publish (user chose N)", fg="yellow")
            )
            return False, change_report
    else:
        if force_publish:
            click.echo(
                click.style(
                    f"\n🤖 AUTO: Publishing version {new_version} (--force-publish)",
                    fg="cyan",
                )
            )
        else:
            click.echo(
                click.style(
                    f"\n🤖 AUTO: Publishing version {new_version} (--all mode)",
                    fg="cyan",
                )
            )
        if change_report and change_report.publishable_files:
            preview = change_report.publishable_files[:8]
            suffix = (
                f" (+{len(change_report.publishable_files) - len(preview)} more)"
                if len(change_report.publishable_files) > len(preview)
                else ""
            )
            click.echo(
                click.style(
                    "  Package source changes: " + ", ".join(preview) + suffix,
                    fg="green",
                )
            )

    try:
        publish_success = publish_project(
            project_types, new_version, yes, config=config
        )
        if publish_success:
            click.echo(
                click.style(
                    f"\n✓ Published version {new_version}", fg="green", bold=True
                )
            )
        else:
            click.echo(
                click.style(
                    "⚠ Publish failed. Release tag and remote push will be skipped in auto mode.",
                    fg="yellow",
                )
            )
        return publish_success, change_report
    except Exception as e:
        click.echo(
            click.style(f"⚠ Publish error: {str(e)}. Continuing...", fg="yellow")
        )
        return False, change_report
