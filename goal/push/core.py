"""Push workflow core - orchestrator and utilities."""

import sys
import time
from typing import Dict, List, Any, Optional

import click

from goal.git_ops import run_git, get_staged_files, get_diff_content, get_diff_stats
from goal.project_bootstrap import (
    detect_project_types_deep,
    bootstrap_project,
    refresh_test_dependencies,
)
from goal.toml_validation import check_pyproject_toml
from goal.push.stages import (
    get_commit_message,
    enforce_quality_gates,
    handle_single_commit,
    handle_split_commits,
    handle_version_sync,
    get_version_info,
    handle_changelog,
    run_test_stage,
    create_tag,
    push_to_remote,
    handle_publish,
    handle_dry_run,
    handle_todo_stage,
)


def run_git_local(*args, **kwargs) -> Any:
    """Local wrapper for run_git to avoid import issues."""
    return run_git(*args, **kwargs)


def show_workflow_preview(
    files,
    stats,
    current_version,
    new_version,
    commit_msg,
    commit_body,
    markdown,
    ctx_obj,
) -> None:
    """Show workflow preview for interactive mode."""
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    denom = (total_adds + total_dels) or 1
    deletion_pct = int((total_dels / denom) * 100)
    net = total_adds - total_dels

    if markdown or ctx_obj.get("markdown"):
        click.echo("\n## GOAL Workflow Preview\n")
        click.echo(
            f"- **Files:** {len(files)} (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)"
        )
        click.echo(f"- **Version:** {current_version} → {new_version}")
        click.echo(f"- **Commit:** `{commit_msg}`")
        if commit_body:
            click.echo(f"\n### Commit Body\n```\n{commit_body}\n```")
    else:
        click.echo(click.style("\n=== GOAL Workflow ===", fg="cyan", bold=True))
        click.echo(
            f"Will commit {len(files)} files (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)"
        )
        click.echo(f"Version bump: {current_version} -> {new_version}")
        click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
        if commit_body:
            click.echo(click.style("\nCommit body (preview):", fg="cyan"))
            click.echo(commit_body)


def add_slow_test_tickets_to_planfile(test_details: Dict[str, Any]) -> List[str]:
    """Create tasks in project/planfile-tickets.yaml for slow tests."""
    from pathlib import Path
    import yaml
    import os

    planfile_path = Path("project/planfile-tickets.yaml")
    if not planfile_path.exists():
        return []

    try:
        with open(planfile_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return []

    if not isinstance(data, dict):
        data = {}

    if "tickets" not in data or not isinstance(data["tickets"], list):
        data["tickets"] = []

    added_titles = []
    slow_tests = test_details.get("slow_tests", [])

    # Threshold of 0.5 seconds for a test to require improvement
    THRESHOLD = 0.5

    for test in slow_tests:
        duration = test.get("duration", 0.0)
        if duration < THRESHOLD:
            continue

        classname = test.get("classname", "unknown")
        name = test.get("name", "unknown")

        # Map classname to file
        parts = classname.split(".")
        file_path = "tests"  # fallback
        for i in range(len(parts), 0, -1):
            candidate = "/".join(parts[:i]) + ".py"
            if os.path.exists(candidate):
                file_path = candidate
                break

        title = f"Address slow test: {classname}.{name}"
        dedupe_key = f"test-optimization:{classname}:{name}"

        # Check if ticket already exists
        exists = False
        for ticket in data["tickets"]:
            if isinstance(ticket, dict) and ticket.get("dedupe_key") == dedupe_key:
                exists = True
                break

        if not exists:
            new_ticket = {
                "signal": "slow_test_warning",
                "title": title,
                "description": (
                    f"Test `{classname}.{name}` took {duration:.2f}s to run.\n\n"
                    f"Optimize its setup, mock slow external dependencies, or "
                    f"refactor its logic to reduce overall test suite execution time."
                ),
                "priority": "medium",
                "labels": ["llm-ready", "test-optimization", "slow-test"],
                "files": [file_path],
                "dedupe_key": dedupe_key
            }
            data["tickets"].append(new_ticket)
            added_titles.append(title)

    # Also add a general startup/collection overhead ticket if overhead is high (> 3.0s)
    startup_overhead = test_details.get("startup_overhead", 0.0)
    if startup_overhead > 3.0:
        title = "Address high test suite startup overhead"
        dedupe_key = "test-optimization:general:startup-overhead"
        exists = False
        for ticket in data["tickets"]:
            if isinstance(ticket, dict) and ticket.get("dedupe_key") == dedupe_key:
                exists = True
                break

        if not exists:
            new_ticket = {
                "signal": "slow_test_warning",
                "title": title,
                "description": (
                    f"The test suite startup and collection overhead is high: {startup_overhead:.2f}s.\n\n"
                    f"This overhead is spent on imports, collection, and test environment initialization.\n"
                    f"Analyze fixtures with broad scopes, reduce heavy imports on test collection, "
                    f"and optimize pytest-xdist startup settings to decrease the delay before tests start running."
                ),
                "priority": "high",
                "labels": ["llm-ready", "test-optimization", "startup-overhead"],
                "files": ["pyproject.toml"],
                "dedupe_key": dedupe_key
            }
            data["tickets"].append(new_ticket)
            added_titles.append(title)

    if added_titles:
        try:
            with open(planfile_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        except Exception:
            pass

    return added_titles


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
    no_tag: bool,
    publish_required: bool = False,
    publish_skip_reason: Optional[str] = None,
) -> None:
    """Output final summary in YAML or markdown format."""
    import yaml
    from datetime import datetime

    from goal.io.stdio import echo_via_markdown, use_markdown_stdio

    test_details = ctx_obj.get("test_details", {})
    added_tickets = []
    if test_details:
        added_tickets = add_slow_test_tickets_to_planfile(test_details)

    use_markdown = markdown or ctx_obj.get("markdown")
    is_all_mode = ctx_obj.get("yes") or use_markdown

    workflow_success = test_exit_code == 0 and (
        publish_success or not publish_required
    )

    if use_markdown and is_all_mode:
        from goal.formatter import format_goal_all_summary

        md_output = format_goal_all_summary(
            project_types=project_types,
            files=files,
            stats=stats,
            current_version=current_version,
            new_version=new_version,
            commit_msg=commit_msg,
            commit_body=commit_body,
            test_exit_code=test_exit_code,
            test_details=test_details,
            publish_success=publish_success,
            publish_required=publish_required,
            publish_skip_reason=publish_skip_reason,
            workflow_success=workflow_success,
            added_tickets=added_tickets,
        )
        echo_via_markdown("\n" + md_output)
        if not use_markdown_stdio():
            click.echo("")
        return

    if is_all_mode:
        # Build YAML report
        slowest = []
        needs_improvement = []
        for t in test_details.get("slow_tests", []):
            duration = t.get("duration", 0.0)
            formatted_test = f"{t.get('classname')}.{t.get('name')} ({duration:.2f}s)"
            if len(slowest) < 5:
                slowest.append(formatted_test)
            if duration >= 0.5:
                needs_improvement.append(formatted_test)

        workflow_success = test_exit_code == 0 and (
            publish_success or not publish_required
        )
        yaml_report = {
            "goal_summary": {
                "timestamp": datetime.now().isoformat(),
                "status": "SUCCESS" if workflow_success else "FAILED",
                "version_update": {
                    "from": current_version,
                    "to": new_version
                },
                "git": {
                    "commit_message": commit_msg,
                    "files_changed": len(files)
                },
                "test_execution": {
                    "status": "passed" if test_exit_code == 0 else "failed",
                    "total_wall_time_seconds": round(test_details.get("wall_time", 0.0), 2),
                    "sum_individual_test_time_seconds": round(test_details.get("total_test_time", 0.0), 2),
                    "startup_and_collection_overhead_seconds": round(test_details.get("startup_overhead", 0.0), 2),
                    "slowest_tests_top_5": slowest,
                    "tests_requiring_improvement": needs_improvement,
                },
                "planfile_updates": {
                    "tickets_added": added_tickets
                },
                "publish": _build_publish_summary(
                    publish_success, publish_required, publish_skip_reason
                )
            }
        }

        click.echo(click.style("\n=== GOAL RESULT (YAML) ===", fg="green", bold=True))
        click.echo(yaml.dump(yaml_report, sort_keys=False, allow_unicode=True))
        click.echo(click.style("==========================\n", fg="green", bold=True))

    if not (markdown or ctx_obj.get("markdown")):
        return

    from goal.formatter import format_push_result

    workflow_success = test_exit_code == 0 and (
        publish_success or not publish_required
    )
    success_emoji = "🎉" if workflow_success else "⚠"
    click.echo(
        click.style(
            f"\n{success_emoji} Process completed successfully!", fg="green", bold=True
        )
    )

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
    elif publish_required:
        actions.append("Publish failed")
    elif publish_skip_reason:
        actions.append(f"Publish skipped ({publish_skip_reason})")
    else:
        actions.append("Publish skipped")

    md_output = format_push_result(
        project_types=project_types,
        files=files,
        stats=stats,
        current_version=current_version,
        new_version=new_version,
        commit_msg=commit_msg,
        commit_body=commit_body,
        test_result="Tests passed"
        if test_exit_code == 0
        else "Tests failed but continued",
        test_exit_code=test_exit_code,
        actions=actions,
    )
    click.echo("\n" + md_output)


class PushContext:
    """Context object wrapper for push command."""

    def __init__(self, ctx_obj: Dict[str, Any]):
        self.obj = ctx_obj

    def get(self, key: str, default=None) -> Any:
        return self.obj.get(key, default)


def _validate_toml_or_exit(dry_run: bool) -> None:
    """Abort the workflow when ``pyproject.toml`` has a syntax error (skipped on dry-run)."""
    if dry_run:
        return
    toml_error = check_pyproject_toml()
    if toml_error:
        click.echo(click.style(toml_error, fg="red", bold=True), err=True)
        click.echo(
            click.style("\nFix the TOML syntax error and try again.", fg="yellow"),
            err=True,
        )
        sys.exit(1)


def _apply_enhanced_quality_gates(
    ctx_obj: Dict[str, Any],
    commit_msg: str,
    detailed_result: Dict,
    files: List[str],
    stats: Dict,
    message: Optional[str],
    markdown: bool,
) -> str:
    if message or not detailed_result or not detailed_result.get("enhanced"):
        return commit_msg

    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    return enforce_quality_gates(
        ctx_obj,
        commit_msg,
        detailed_result,
        files,
        total_adds,
        total_dels,
        ctx_obj["yes"],
        markdown,
    )


def _handle_no_files(
    ctx_obj: Dict[str, Any],
    project_types: List[str],
    dry_run: bool,
    markdown: bool,
    files: List[str],
) -> bool:
    if files and files != [""]:
        return False
    _handle_no_changes(ctx_obj, project_types, dry_run, markdown)
    return True


def _abort_if_missing_commit_title(commit_title: Optional[str]) -> bool:
    if commit_title:
        return False
    click.echo(click.style("No changes to commit.", fg="yellow"))
    return True


def _maybe_show_workflow_preview(
    ctx_obj: Dict[str, Any],
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: Optional[str],
    markdown: bool,
) -> None:
    if not ctx_obj["yes"]:
        show_workflow_preview(
            files,
            stats,
            current_version,
            new_version,
            commit_msg,
            commit_body,
            markdown,
            ctx_obj,
        )


def _run_test_stage_or_exit(
    project_types: List[str],
    ctx_obj: Dict[str, Any],
    markdown: bool,
    files: List[str],
    stats: Dict,
    current_version: str,
    new_version: str,
    commit_msg: str,
    commit_body: Optional[str],
):
    test_result, test_exit_code = run_test_stage(
        project_types,
        ctx_obj["yes"],
        markdown,
        ctx_obj,
        files,
        stats,
        current_version,
        new_version,
        commit_msg,
        commit_body,
    )

    if test_exit_code != 0 and ctx_obj["yes"]:
        click.echo(
            click.style("Aborting workflow because tests failed.", fg="red", bold=True)
        )
        sys.exit(1)

    return test_result, test_exit_code


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
    todo: bool,
    force: bool = False,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    no_publish: bool = False,
    force_publish: bool = False,
) -> None:
    """Execute the complete push workflow."""

    _validate_toml_or_exit(dry_run)

    start_time = time.time()

    _initialize_context(ctx_obj, bump, message, yes, markdown)

    yes = ctx_obj["yes"]
    no_publish = no_publish or ctx_obj.get("no_publish", False)
    force_publish = force_publish or ctx_obj.get("force_publish", False)

    project_types = _detect_project_types()

    # Run dependency updates before bootstrap: uv sync removes packages (like goal)
    # that are not listed in the project lockfile.
    if ctx_obj.get("upgrade_deps"):
        from goal.dependency_update import update_project_dependencies

        update_results = update_project_dependencies(
            yes=ctx_obj["yes"],
            dry_run=dry_run,
            recursive=ctx_obj.get("recursive", False),
        )
        if update_results and not all(result.success for result in update_results):
            click.echo(
                click.style(
                    "Aborting workflow because dependency updates failed.",
                    fg="red",
                    bold=True,
                )
            )
            sys.exit(1)

    _bootstrap_projects(project_types, dry_run, yes)

    if ctx_obj.get("upgrade_deps"):
        refresh_test_dependencies(project_types, yes=yes, dry_run=dry_run)

    # Handle TODO update via prefact
    ctx_obj["todo"] = todo
    todo_stage_ok = handle_todo_stage(ctx_obj, yes, dry_run)
    if not todo_stage_ok:
        click.echo(
            click.style(
                "Aborting workflow because TODO stage failed.", fg="red", bold=True
            )
        )
        sys.exit(2)

    if not dry_run:
        run_git("add", "-A")

    files = get_staged_files()
    if _handle_no_files(ctx_obj, project_types, dry_run, markdown, files):
        return

    _validate_staged_files(ctx_obj, dry_run, force)

    diff_content = get_diff_content()
    stats = get_diff_stats()

    commit_title, commit_body, detailed_result = get_commit_message(
        ctx_obj, files, diff_content, message, ticket, abstraction
    )

    if _abort_if_missing_commit_title(commit_title):
        return

    commit_msg = commit_title

    current_version, new_version = get_version_info()

    commit_msg = _apply_enhanced_quality_gates(
        ctx_obj, commit_msg, detailed_result, files, stats, message, markdown
    )

    if dry_run:
        handle_dry_run(
            ctx_obj,
            project_types,
            files,
            stats,
            current_version,
            new_version,
            commit_msg,
            commit_body,
            detailed_result,
            split,
            ticket,
            bump,
            no_version_sync,
            no_changelog,
            no_tag,
            markdown,
        )
        return

    _maybe_show_workflow_preview(
        ctx_obj,
        files,
        stats,
        current_version,
        new_version,
        commit_msg,
        commit_body,
        markdown,
    )

    test_result, test_exit_code = _run_test_stage_or_exit(
        project_types,
        ctx_obj,
        markdown,
        files,
        stats,
        current_version,
        new_version,
        commit_msg,
        commit_body,
    )

    _handle_commit_phase(
        ctx_obj,
        split,
        message,
        commit_title,
        commit_body,
        commit_msg,
        files,
        ticket,
        new_version,
        current_version,
        no_version_sync,
        no_changelog,
    )

    publish_config = ctx_obj.get("config")
    if hasattr(publish_config, "reload"):
        publish_config.reload()

    publish_success, publish_change_report = handle_publish(
        project_types,
        new_version,
        ctx_obj["yes"],
        no_publish=no_publish,
        config=publish_config,
        staged_files=files,
        force_publish=force_publish,
    )

    publish_skip_reason = (
        publish_change_report.skip_reason if publish_change_report else None
    )
    publish_required = (
        ctx_obj["yes"]
        and not no_publish
        and not publish_skip_reason
    )
    if publish_required and not publish_success:
        elapsed = time.time() - start_time
        ctx_obj["_elapsed_time"] = elapsed
        output_final_summary(
            ctx_obj,
            markdown,
            project_types,
            files,
            stats,
            current_version,
            new_version,
            commit_msg,
            commit_body,
            test_exit_code,
            publish_success,
            no_tag,
            publish_required=publish_required,
            publish_skip_reason=publish_skip_reason,
        )
        click.echo(click.style(f"\n⏱️  Total time: {elapsed:.1f}s", fg="cyan"))
        sys.exit(1)

    tag_name = create_tag(new_version, no_tag)

    from goal.git_ops import get_remote_branch

    branch = get_remote_branch()
    push_to_remote(branch, tag_name, no_tag, ctx_obj["yes"])

    elapsed = time.time() - start_time
    ctx_obj["_elapsed_time"] = elapsed

    output_final_summary(
        ctx_obj,
        markdown,
        project_types,
        files,
        stats,
        current_version,
        new_version,
        commit_msg,
        commit_body,
        test_exit_code,
        publish_success,
        no_tag,
        publish_required=publish_required,
        publish_skip_reason=publish_skip_reason,
    )

    click.echo(click.style(f"\n⏱️  Total time: {elapsed:.1f}s", fg="cyan"))


def _build_publish_summary(
    publish_success: bool,
    publish_required: bool,
    publish_skip_reason: Optional[str],
) -> Dict[str, Any]:
    """Build the publish section for the YAML goal summary."""
    if publish_success:
        return {"status": "passed"}
    if publish_skip_reason:
        return {
            "status": "skipped",
            "reason": publish_skip_reason,
        }
    if publish_required:
        return {"status": "failed"}
    return {"status": "skipped"}


def _initialize_context(
    ctx_obj: Dict[str, Any],
    bump: str,
    message: Optional[str],
    yes: bool,
    markdown: bool,
) -> None:
    """Initialize context with common values."""
    from goal.io.stdio import set_stdio_markdown

    # Use yes from context (includes -a from main command) or local --yes flag
    yes = ctx_obj.get("yes", False) or yes
    ctx_obj["yes"] = yes
    ctx_obj["bump"] = bump
    ctx_obj["message"] = message
    effective_markdown = markdown or ctx_obj.get("markdown", False)
    ctx_obj["markdown"] = effective_markdown
    set_stdio_markdown(effective_markdown)


def _detect_project_types() -> List[str]:
    """Detect project types without bootstrapping environments."""
    from goal.cli.version import detect_project_types

    project_types = detect_project_types()
    if project_types:
        click.echo(
            f"Detected project types: {click.style(', '.join(project_types), fg='cyan')}"
        )
    return project_types


def _bootstrap_projects(project_types: List[str], dry_run: bool, yes: bool) -> None:
    """Bootstrap project environments (venv, deps, tests)."""
    if dry_run or not project_types:
        return

    deep_detected = detect_project_types_deep()
    for ptype, dirs in deep_detected.items():
        for pdir in dirs:
            bootstrap_project(pdir, ptype, yes=yes)


def _detect_and_bootstrap_projects(
    ctx_obj: Dict[str, Any], dry_run: bool, yes: bool
) -> List[str]:
    """Detect project types and bootstrap environments."""
    project_types = _detect_project_types()
    _bootstrap_projects(project_types, dry_run, yes)
    return project_types


def _handle_no_changes(
    ctx_obj: Dict[str, Any], project_types: List[str], dry_run: bool, markdown: bool
) -> None:
    """Handle case when no changes are staged."""
    if markdown or ctx_obj.get("markdown"):
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
            error="No changes to commit",
        )
        click.echo(md_output)
    else:
        click.echo(click.style("No changes to commit.", fg="yellow"))


def _validate_staged_files(ctx_obj: Dict[str, Any], dry_run: bool, force: bool) -> None:
    """Validate staged files for security issues."""
    if not dry_run and not force:
        from goal.validators import validate_staged_files

        try:
            validate_staged_files(ctx_obj.get("config"))
        except Exception as e:
            click.echo(
                click.style(f"\n❌ Validation Error: {str(e)}", fg="red", bold=True)
            )
            click.echo(
                click.style(
                    "\nFor security reasons, the commit has been blocked.", fg="red"
                )
            )
            click.echo(click.style("\nTo bypass this check, you can:", fg="yellow"))
            click.echo(
                click.style("1. Remove the sensitive/large file(s)", fg="yellow")
            )
            click.echo(click.style("2. Add the file(s) to .gitignore", fg="yellow"))
            click.echo(
                click.style(
                    "3. Use --force to bypass validation (not recommended)", fg="yellow"
                )
            )
            sys.exit(1)
    elif force and not dry_run:
        click.echo(
            click.style(
                "⚠️  Security validation bypassed with --force", fg="yellow", bold=True
            )
        )


def _handle_commit_phase(
    ctx_obj: Dict[str, Any],
    split: bool,
    message: Optional[str],
    commit_title: str,
    commit_body: Optional[str],
    commit_msg: str,
    files: List[str],
    ticket: Optional[str],
    new_version: str,
    current_version: str,
    no_version_sync: bool,
    no_changelog: bool,
) -> None:
    """Handle the commit phase of the workflow."""
    from goal.cli import confirm

    # Commit confirmation
    if not ctx_obj["yes"]:
        if not confirm("Commit changes?"):
            click.echo(
                click.style("  🤖 AUTO: Aborting commit (user chose N)", fg="cyan")
            )
            click.echo(click.style("Aborted.", fg="red"))
            sys.exit(1)
    else:
        click.echo(click.style("🤖 AUTO: Committing changes (--all mode)", fg="cyan"))

    # Handle split commits or single commit
    if split and not message:
        run_git("reset")  # Unstage everything
        handle_split_commits(
            ctx_obj,
            files,
            ticket,
            new_version,
            current_version,
            no_version_sync,
            no_changelog,
            ctx_obj["yes"],
        )
    else:
        # Version sync
        user_config = ctx_obj.get("user_config")
        handle_version_sync(new_version, no_version_sync, user_config, ctx_obj["yes"])

        # Changelog
        config_dict = (
            (ctx_obj.get("config") or {}).to_dict() if ctx_obj.get("config") else None
        )
        handle_changelog(new_version, files, commit_msg, config_dict, no_changelog)

        # Refresh costs README content before committing so the update is included.
        if _update_cost_badges(ctx_obj, new_version):
            run_git_local("add", "README.md")

        # Single commit
        handle_single_commit(
            commit_title, commit_body, commit_msg, message, ctx_obj["yes"]
        )


# Backward-compat shims — moved to goal.push.stages.costs
from goal.push.stages.costs import (  # noqa: E402
    update_cost_badges as _update_cost_badges,
)
