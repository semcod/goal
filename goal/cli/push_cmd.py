"""Push command - backward-compatibility shim.

The actual implementation is in goal.push package.
This file maintains backward compatibility for imports.
"""

import click

from goal.cli import main
from goal.push.core import execute_push_workflow


@main.command()
@click.option("--bump", default="patch", help="Version bump type (major, minor, patch)")
@click.option("--no-tag", is_flag=True, help="Skip creating git tag")
@click.option("--no-changelog", is_flag=True, help="Skip updating CHANGELOG.md")
@click.option(
    "--no-version-sync", is_flag=True, help="Skip syncing version to all files"
)
@click.option("--no-publish", is_flag=True, help="Skip publishing to registry")
@click.option("--message", "-m", default=None, help="Custom commit message")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be done without executing"
)
@click.option("--markdown/--ascii", default=False, help="Output format")
@click.option("--split", is_flag=True, help="Split commits by file type")
@click.option("--ticket", default=None, help="Ticket ID for commit prefix")
@click.option(
    "--abstraction", default=None, help="Abstraction level for commit message"
)
@click.option("--todo", "-t", is_flag=True, help="Create TODO.md with detected issues")
@click.option(
    "--model",
    default=None,
    help="AI model for cost tracking (e.g., openrouter/qwen/qwen3-coder-next)",
)
@click.option("--api-key", default=None, help="API key for cost tracking service")
@click.pass_context
def push(
    ctx,
    bump,
    no_tag,
    no_changelog,
    no_version_sync,
    no_publish,
    message,
    dry_run,
    markdown,
    split,
    ticket,
    abstraction,
    todo,
    model,
    api_key,
) -> None:
    """Add, commit, tag, and push changes to remote."""
    # Use yes from ctx.obj (set by -a/--all or -y/--yes global flags)
    yes = ctx.obj.get("yes", False)
    no_publish = no_publish or ctx.obj.get("no_publish", False)
    # Store model and api_key in ctx.obj for downstream use
    ctx.obj["cost_model"] = model
    ctx.obj["cost_api_key"] = api_key
    execute_push_workflow(
        ctx_obj=ctx.obj,
        bump=bump,
        no_tag=no_tag,
        no_changelog=no_changelog,
        no_version_sync=no_version_sync,
        no_publish=no_publish,
        message=message,
        dry_run=dry_run,
        yes=yes,
        markdown=markdown,
        split=split,
        ticket=ticket,
        abstraction=abstraction,
        todo=todo,
        model=model,
        api_key=api_key,
    )


# Re-export workflow functions for backward compatibility
from goal.push import (
    execute_push_workflow as _execute_push_workflow,
    PushContext as _PushContext,
    get_commit_message as _get_commit_message,
    enforce_quality_gates as _enforce_quality_gates,
    handle_single_commit as _handle_single_commit,
    handle_split_commits as _handle_split_commits,
    handle_version_sync as _handle_version_sync,
    get_version_info as _get_version_info,
    handle_changelog as _handle_changelog,
    run_test_stage as _run_test_stage,
    create_tag as _create_tag,
    push_to_remote as _push_to_remote,
    handle_publish as _handle_publish,
    handle_dry_run as _handle_dry_run,
    show_workflow_preview as _show_workflow_preview,
    output_final_summary as _output_final_summary,
)

# Expose for backward compatibility
execute_push_workflow = _execute_push_workflow
PushContext = _PushContext
get_commit_message = _get_commit_message
enforce_quality_gates = _enforce_quality_gates
handle_single_commit = _handle_single_commit
handle_split_commits = _handle_split_commits
handle_version_sync = _handle_version_sync
get_version_info = _get_version_info
handle_changelog = _handle_changelog
run_test_stage = _run_test_stage
create_tag = _create_tag
push_to_remote = _push_to_remote
handle_publish = _handle_publish
handle_dry_run = _handle_dry_run
show_workflow_preview = _show_workflow_preview
output_final_summary = _output_final_summary

__all__ = [
    "push",
    "execute_push_workflow",
    "PushContext",
    "get_commit_message",
    "enforce_quality_gates",
    "handle_single_commit",
    "handle_split_commits",
    "handle_version_sync",
    "get_version_info",
    "handle_changelog",
    "run_test_stage",
    "create_tag",
    "push_to_remote",
    "handle_publish",
    "handle_dry_run",
    "show_workflow_preview",
    "output_final_summary",
]
