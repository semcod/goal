"""Push workflow stages - publishing."""

import click

from goal.cli.publish import publish_project
from goal.cli import confirm
from goal.publish.changes import PublishChangeReport, analyze_publishable_changes
from goal.io.stdio import (
    echo_auto,
    echo_heading,
    echo_info,
    echo_status_error,
    echo_status_ok,
    echo_status_warn,
    use_markdown_stdio,
)


def _format_skip_message(report: PublishChangeReport) -> str:
    """Build a transparent skip explanation for the user."""
    if use_markdown_stdio():
        lines = [
            "No package source changes detected — publish skipped.",
            f"**Registry types checked:** {', '.join(report.project_types) or '(none)'}",
        ]
        if report.non_publishable_files:
            preview = report.non_publishable_files[:8]
            suffix = (
                f" (+{len(report.non_publishable_files) - len(preview)} more)"
                if len(report.non_publishable_files) > len(preview)
                else ""
            )
            lines.append(
                "**Staged files (metadata/docs/tests only):** "
                + ", ".join(f"`{path}`" for path in preview)
                + suffix
            )
        lines.append("**Tip:** use `--force-publish` to publish anyway.")
        return "\n\n".join(lines)

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
        echo_status_warn("Skipping publish (--no-publish)")
        return False, None

    change_report: PublishChangeReport | None = None
    if staged_files is not None and not force_publish:
        change_report = analyze_publishable_changes(staged_files, project_types)
        if not change_report.has_changes:
            # Staged files miss already-committed source (agent commits, then
            # goal -a runs on a clean tree) — same check as push/core.
            from goal.publish.changes import committed_unreleased_source_files

            pending = committed_unreleased_source_files(project_types)
            if not pending:
                echo_heading("Skipping publish — no package source changes", level=2)
                echo_info(_format_skip_message(change_report))
                return False, change_report
            echo_info(
                f"Publishing committed-but-unreleased source ({len(pending)} file(s) "
                f"since the last release tag)"
            )
            # Rebuild the report as a real release: downstream stages key off
            # skip_reason (the tag stage skipped v0.1.39/v0.1.106/... while the
            # registry got published, leaving release tags behind HEAD).
            change_report = PublishChangeReport(
                has_changes=True,
                project_types=change_report.project_types,
                publishable_files=list(pending),
                non_publishable_files=list(change_report.non_publishable_files),
            )

    if not yes:
        if not confirm(f"Publish version {new_version}?"):
            echo_status_warn("Skipping publish (user chose N)")
            return False, change_report
    else:
        if force_publish:
            echo_auto(f"Publishing version `{new_version}` (--force-publish)")
        else:
            echo_auto(f"Publishing version `{new_version}` (--all mode)")
        if change_report and change_report.publishable_files:
            preview = change_report.publishable_files[:8]
            suffix = (
                f" (+{len(change_report.publishable_files) - len(preview)} more)"
                if len(change_report.publishable_files) > len(preview)
                else ""
            )
            files_text = ", ".join(f"`{path}`" for path in preview) + suffix
            if use_markdown_stdio():
                echo_info(f"**Package source changes:** {files_text}")
            else:
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
            echo_status_ok(f"Published version {new_version}")
        else:
            echo_status_warn(
                "Publish failed. Release tag and remote push will be skipped in auto mode."
            )
        return publish_success, change_report
    except Exception as e:
        echo_status_warn(f"Publish error: {str(e)}. Continuing...")
        return False, change_report
