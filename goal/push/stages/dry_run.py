"""Push workflow stages - dry run handling."""

from typing import Dict, List, Any, Optional

import click

from goal.cli import apply_ticket_prefix, split_paths_by_type
from goal.commit_generator import CommitMessageGenerator
from goal.formatter import format_enhanced_summary, format_push_result


def _build_split_plan_body(
    ctx_obj: Dict[str, Any],
    files: List[str],
    ticket: Optional[str],
    new_version: str,
    no_version_sync: bool,
    no_changelog: bool,
) -> str:
    """Build commit body text describing the planned split commits."""
    config_dict = (
        (ctx_obj.get("config") or {}).to_dict() if ctx_obj.get("config") else None
    )
    generator = CommitMessageGenerator(config=config_dict)
    groups = split_paths_by_type(files)

    plan_lines = []
    for gname in ["code", "docs", "ci", "examples", "other"]:
        if gname not in groups:
            continue
        d = generator.generate_detailed_message(cached=True, paths=groups[gname])
        if not d:
            continue
        title = apply_ticket_prefix(d.get("title"), ticket)
        plan_lines.append(f"- {gname}: {title} ({len(groups[gname])} files)")

    if not no_version_sync or not no_changelog:
        plan_lines.append(f"- release: chore(release): bump to {new_version}")

    nl = "\n"
    return f"Planned split commits:\n{nl.join(plan_lines)}".strip()


def _format_markdown_dry_run(
    ctx_obj: Dict[str, Any],
    project_types: List[str],
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: Optional[str],
    detailed_result: Optional[Dict],
) -> str:
    """Return markdown-formatted dry-run output."""
    if detailed_result and detailed_result.get("enhanced"):
        return format_enhanced_summary(
            commit_title=commit_msg,
            commit_body=commit_body or "",
            capabilities=detailed_result.get("capabilities"),
            roles=detailed_result.get("roles"),
            relations=detailed_result.get("relations"),
            metrics=detailed_result.get("metrics"),
            files=files,
            stats=stats,
            current_version=current_version,
            new_version=new_version,
        )
    return format_push_result(
        project_types=project_types,
        files=files,
        stats=stats,
        current_version=current_version,
        new_version=new_version,
        commit_msg=commit_msg,
        commit_body=commit_body,
        test_result="Dry run - tests not executed",
        test_exit_code=0,
        actions=[
            "Detected project types",
            "Staged changes",
            "Generated commit message",
            "Planned version bump",
            "Planned changelog update",
            "Planned tag creation",
            "Planned push to remote",
        ],
    )


def _print_plain_dry_run(
    project_types: List[str],
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
) -> None:
    """Print plain-text dry-run summary."""
    click.echo(click.style("=== DRY RUN ===", fg="cyan", bold=True))
    if project_types:
        click.echo(f"Project types: {', '.join(project_types)}")
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    click.echo(f"Files to commit: {len(files)} (+{total_adds}/-{total_dels} lines)")
    click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
    click.echo(f"Version: {current_version} -> {new_version}")


def handle_dry_run(
    ctx_obj: Dict[str, Any],
    project_types: List[str],
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: Optional[str],
    detailed_result: Optional[Dict],
    split: bool,
    ticket: Optional[str],
    bump: str,
    no_version_sync: bool,
    no_changelog: bool,
    no_tag: bool,
    markdown: bool,
) -> None:
    """Handle dry run output."""
    if split and not ctx_obj.get("message"):
        commit_body = _build_split_plan_body(
            ctx_obj, files, ticket, new_version, no_version_sync, no_changelog
        )

    if markdown or ctx_obj.get("markdown"):
        click.echo(
            _format_markdown_dry_run(
                ctx_obj,
                project_types,
                files,
                stats,
                current_version,
                new_version,
                commit_msg,
                commit_body,
                detailed_result,
            )
        )
    else:
        _print_plain_dry_run(
            project_types, files, stats, current_version, new_version, commit_msg
        )
