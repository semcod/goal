"""Push workflow core - orchestrator and utilities."""

import sys
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

import click

try:
    from ..git_ops import run_git, get_staged_files, get_diff_content, get_diff_stats
    from ..project_bootstrap import detect_project_types_deep, bootstrap_project
    from ..cli.version import detect_project_types
    from .stages import (
        get_commit_message, enforce_quality_gates, handle_single_commit,
        handle_split_commits, handle_version_sync, get_version_info,
        handle_changelog, run_test_stage, create_tag, push_to_remote,
        handle_publish, handle_dry_run
    )
except ImportError:
    from goal.git_ops import run_git, get_staged_files, get_diff_content, get_diff_stats
    from goal.project_bootstrap import detect_project_types_deep, bootstrap_project
    from goal.cli.version import detect_project_types
    from goal.push.stages import (
        get_commit_message, enforce_quality_gates, handle_single_commit,
        handle_split_commits, handle_version_sync, get_version_info,
        handle_changelog, run_test_stage, create_tag, push_to_remote,
        handle_publish, handle_dry_run
    )


def run_git_local(*args, **kwargs):
    """Local wrapper for run_git to avoid import issues."""
    return run_git(*args, **kwargs)


def show_workflow_preview(files, stats, current_version, new_version, commit_msg, commit_body, markdown, ctx_obj):
    """Show workflow preview for interactive mode."""
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    denom = (total_adds + total_dels) or 1
    deletion_pct = int((total_dels / denom) * 100)
    net = total_adds - total_dels
    
    if markdown or ctx_obj.get('markdown'):
        click.echo(f"\n## GOAL Workflow Preview\n")
        click.echo(f"- **Files:** {len(files)} (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)")
        click.echo(f"- **Version:** {current_version} → {new_version}")
        click.echo(f"- **Commit:** `{commit_msg}`")
        if commit_body:
            click.echo(f"\n### Commit Body\n```\n{commit_body}\n```")
    else:
        click.echo(click.style("\n=== GOAL Workflow ===", fg='cyan', bold=True))
        click.echo(f"Will commit {len(files)} files (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)")
        click.echo(f"Version bump: {current_version} -> {new_version}")
        click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
        if commit_body:
            click.echo(click.style("\nCommit body (preview):", fg='cyan'))
            click.echo(commit_body)


def output_final_summary(
    ctx_obj: Dict[str, Any],
    markdown: bool,
    project_types: List[str],
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: Optional[str],
    test_exit_code: int,
    publish_success: bool,
    no_tag: bool
) -> None:
    """Output final summary in markdown format if requested."""
    if not (markdown or ctx_obj.get('markdown')):
        return
    
    try:
        from ..formatter import format_push_result
    except ImportError:
        from goal.formatter import format_push_result
    
    success_emoji = "🎉" if test_exit_code == 0 and publish_success else "✅"
    click.echo(click.style(f"\n{success_emoji} Process completed successfully!", fg='green', bold=True))
    
    actions = [
        "Detected project types",
        "Staged changes",
        "Ran tests" if test_exit_code == 0 else "Tests failed but continued",
        "Committed changes",
        f"Updated version to {new_version}",
        "Updated changelog",
        f"Created tag v{new_version}" if not no_tag else "Skipped tag creation",
        "Pushed to remote" if not no_tag else "Pushed to remote without tags",
    ]
    if publish_success:
        actions.append(f"Published version {new_version}")
    else:
        actions.append("Publish failed or skipped")
    
    md_output = format_push_result(
        project_types=project_types,
        files=files,
        stats=stats,
        current_version=current_version,
        new_version=new_version,
        commit_msg=commit_msg,
        commit_body=commit_body,
        test_result="Tests passed" if test_exit_code == 0 else "Tests failed but continued",
        test_exit_code=test_exit_code,
        actions=actions
    )
    click.echo("\n" + md_output)


class PushContext:
    """Context object wrapper for push command."""
    
    def __init__(self, ctx_obj: Dict[str, Any]):
        self.obj = ctx_obj
    
    def get(self, key: str, default=None):
        return self.obj.get(key, default)


def execute_push_workflow(
    ctx_obj: Dict[str, Any],
    bump: str,
    no_tag: bool,
    no_changelog: bool,
    no_version_sync: bool,
    message: Optional[str],
    dry_run: bool,
    yes: bool,
    markdown: bool,
    split: bool,
    ticket: Optional[str],
    abstraction: Optional[str],
    todo: bool
) -> None:
    """Execute the complete push workflow."""
    
    # Use yes from context (includes -a from main command) or local --yes flag
    yes = ctx_obj.get('yes', False) or yes
    ctx_obj['yes'] = yes
    ctx_obj['bump'] = bump
    ctx_obj['message'] = message
    ctx_obj['markdown'] = markdown or ctx_obj.get('markdown', False)
    
    # Detect project types
    project_types = detect_project_types()
    if project_types and not dry_run:
        click.echo(f"Detected project types: {click.style(', '.join(project_types), fg='cyan')}")
    
    # Bootstrap project environments
    if not dry_run and project_types:
        deep_detected = detect_project_types_deep()
        for ptype, dirs in deep_detected.items():
            for pdir in dirs:
                bootstrap_project(pdir, ptype, yes=yes)
    
    # Stage all changes
    if not dry_run:
        run_git('add', '-A')
    
    # Get staged files
    files = get_staged_files()
    if not files or files == ['']:
        if markdown or ctx_obj.get('markdown'):
            try:
                from ..cli.version import get_current_version
                from ..formatter import format_push_result
            except ImportError:
                from goal.cli.version import get_current_version
                from goal.formatter import format_push_result
            
            current_version = get_current_version()
            md_output = format_push_result(
                project_types=project_types or [],
                files=[],
                stats={},
                current_version=current_version,
                new_version=current_version,
                commit_msg="(none)",
                commit_body="No staged changes detected.",
                test_result="Not executed",
                test_exit_code=0,
                actions=["Detected project types"],
                error="No changes to commit"
            )
            click.echo(md_output)
        else:
            click.echo(click.style("No changes to commit.", fg='yellow'))
        return
    
    # Get diff content
    diff_content = get_diff_content()
    
    # Generate commit message
    commit_title, commit_body, detailed_result = get_commit_message(
        ctx_obj, files, diff_content, message, ticket, abstraction
    )
    
    if not commit_title:
        click.echo(click.style("No changes to commit.", fg='yellow'))
        return
    
    commit_msg = commit_title
    
    # Get version info
    current_version, new_version = get_version_info()
    
    # Get diff stats
    stats = get_diff_stats()
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    
    # Enforce quality gates
    if not message and detailed_result and detailed_result.get('enhanced'):
        commit_msg = enforce_quality_gates(
            ctx_obj, commit_msg, detailed_result, files, total_adds, total_dels,
            ctx_obj['yes'], markdown
        )
    
    # Handle dry run
    if dry_run:
        handle_dry_run(ctx_obj, project_types, files, stats, current_version, new_version,
                      commit_msg, commit_body, detailed_result, split, ticket, bump,
                      no_version_sync, no_changelog, no_tag, markdown)
        return
    
    # Interactive workflow preview
    if not ctx_obj['yes']:
        show_workflow_preview(files, stats, current_version, new_version,
                             commit_msg, commit_body, markdown, ctx_obj)
    
    # Test stage
    test_result, test_exit_code = run_test_stage(
        project_types, ctx_obj['yes'], markdown, ctx_obj, files, stats,
        current_version, new_version, commit_msg, commit_body
    )
    
    try:
        from ..cli import confirm
    except ImportError:
        from goal.cli import confirm
    
    # Commit confirmation
    if not ctx_obj['yes']:
        if not confirm("Commit changes?"):
            click.echo(click.style("  🤖 AUTO: Aborting commit (user chose N)", fg='cyan'))
            click.echo(click.style("Aborted.", fg='red'))
            sys.exit(1)
    else:
        click.echo(click.style("🤖 AUTO: Committing changes (--all mode)", fg='cyan'))
    
    # Handle split commits or single commit
    if split and not message:
        run_git('reset')  # Unstage everything
        handle_split_commits(ctx_obj, files, ticket, new_version, current_version,
                            no_version_sync, no_changelog, ctx_obj['yes'])
        commit_body = None
        message = "__split__"
    else:
        # Version sync
        user_config = ctx_obj.get('user_config')
        handle_version_sync(new_version, no_version_sync, user_config, ctx_obj['yes'])
        
        # Changelog
        config_dict = (ctx_obj.get('config') or {}).to_dict() if ctx_obj.get('config') else None
        handle_changelog(new_version, files, commit_msg, config_dict, no_changelog)
        
        # Single commit
        handle_single_commit(commit_title, commit_body, commit_msg, message, ctx_obj['yes'])
    
    # Create tag
    tag_name = create_tag(new_version, no_tag)
    
    # Push to remote
    try:
        from ..git_ops import get_remote_branch
    except ImportError:
        from goal.git_ops import get_remote_branch
    
    branch = get_remote_branch()
    push_to_remote(branch, tag_name, no_tag, ctx_obj['yes'])
    
    # Publish
    publish_success = handle_publish(project_types, new_version, ctx_obj['yes'])
    
    # Final summary
    output_final_summary(ctx_obj, markdown, project_types, files, stats, current_version,
                        new_version, commit_msg, commit_body, test_exit_code,
                        publish_success, no_tag)
