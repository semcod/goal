"""Push workflow core - orchestrator and utilities."""

import os
import re
import sys
import time
import tomllib
from pathlib import Path
from typing import Dict, List, Any, Optional

import click

from goal.git_ops import (
    run_git,
    get_staged_files,
    get_working_tree_files,
    get_diff_content,
    get_diff_stats,
)
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
from goal.push.preview import show_workflow_preview
from goal.push.stages.tag import reuse_exact_annotated_tag
from goal.push.tickets import add_slow_test_tickets_to_planfile


def run_git_local(*args, **kwargs) -> Any:
    """Local wrapper for run_git to avoid import issues."""
    return run_git(*args, **kwargs)


def _commit_only_requested(
    *, no_version_sync: bool, no_tag: bool, no_publish: bool
) -> bool:
    """Return whether every release side effect was explicitly disabled."""
    return no_version_sync and no_tag and no_publish


def _resolve_release_tag(
    new_version: str,
    tag_name: str | None,
    *,
    effective_no_tag: bool,
    delivery: Any,
    clean_force_publish: bool,
) -> str | None:
    """Recover only an exact annotated tag after an incomplete direct-main run."""
    if tag_name or effective_no_tag:
        return tag_name
    if clean_force_publish and delivery is not None and delivery.mode == "direct-main":
        return reuse_exact_annotated_tag(new_version)
    return None


def _release_requires_package_assets(project_types: List[str], config: Any) -> bool:
    """Package discovery does not override explicitly disabled registry delivery."""
    from goal.publish.github_fallback import _publishing_section

    return bool(project_types) and _publishing_section(config).get("enabled") is not False


def _recover_existing_generic_release_decision(
    current_version: str,
    version_decision: Any,
    *,
    clean_force_publish: bool,
    delivery: Any,
    project_types: List[str],
    publish_config: Any,
) -> tuple[Any, bool]:
    """Bind a clean generic Release repair to its exact current-version tag."""
    if (
        not clean_force_publish
        or delivery is None
        or delivery.mode != "direct-main"
        or _release_requires_package_assets(project_types, publish_config)
        or getattr(version_decision, "reason", None) != "normal-bump"
    ):
        return version_decision, False

    from dataclasses import replace

    from goal.publish.github_fallback import get_github_release_config

    release_config = get_github_release_config(publish_config)
    if not (release_config and release_config.create_on_tag):
        return version_decision, False

    reuse_exact_annotated_tag(current_version)
    return (
        replace(
            version_decision,
            target_version=current_version,
            reason="existing-tag-release-repair",
        ),
        True,
    )


def _configured_project_name(config: Any) -> str:
    """Return the stable project identity instead of the checkout directory."""
    value: Any = ""
    if isinstance(config, dict):
        project = config.get("project", {})
        value = project.get("name", "") if isinstance(project, dict) else ""
    elif hasattr(config, "get"):
        try:
            value = config.get("project.name", "")
        except Exception:
            value = ""
    return str(value or "").strip() or (Path.cwd().name or "package")


def _mirror_github_release(
    *,
    tag_name: str | None,
    effective_no_tag: bool,
    delivery: Any,
    project_types: List[str],
    new_version: str,
    publish_config: Any,
) -> None:
    """Mirror a release tag and fail governed direct-main when required."""
    if not tag_name or effective_no_tag:
        return
    from goal.publish.github_fallback import (
        get_github_release_config,
        try_github_release_on_tag,
    )

    release_config = get_github_release_config(publish_config)
    release_required = bool(release_config and release_config.create_on_tag)
    if not release_required:
        return

    package_name = _configured_project_name(publish_config)
    governed_direct_main = delivery is not None and delivery.mode == "direct-main"
    generic_project = not _release_requires_package_assets(project_types, publish_config)
    try:
        mirrored = try_github_release_on_tag(
            version=new_version,
            package_name=package_name,
            config=publish_config,
            artifacts=[] if generic_project else None,
            allow_empty_assets=generic_project,
        )
    except Exception as exc:
        if governed_direct_main:
            raise click.ClickException(
                f"governed GitHub Release creation failed: {exc}"
            ) from exc
        click.echo(
            click.style(
                f"  ⚠ GitHub release-on-tag skipped: {exc}",
                fg="yellow",
            )
        )
        return
    if governed_direct_main and not mirrored:
        raise click.ClickException("governed GitHub Release creation failed")


def _prepare_slow_test_tickets(ctx_obj: Dict[str, Any], files: List[str]) -> List[str]:
    """Generate and stage slow-test tickets before the workflow commits."""
    if ctx_obj.get("delivery_mode") in {"pull-request", "publish-only", "direct-main"}:
        # Performance observations do not expand a governed ticket's write
        # scope. Keep the metrics for the summary and let intake own new tasks.
        ctx_obj["added_slow_test_tickets"] = []
        return files
    test_details = ctx_obj.get("test_details", {})
    added_tickets = (
        add_slow_test_tickets_to_planfile(test_details) if test_details else []
    )
    ctx_obj["added_slow_test_tickets"] = added_tickets
    if not added_tickets:
        return files

    ticket_path = "project/planfile-tickets.yaml"
    from goal.cli import stage_paths

    stage_paths([ticket_path])
    return list(dict.fromkeys([*files, ticket_path]))


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
    added_tickets = list(ctx_obj.get("added_slow_test_tickets", []))

    use_markdown = markdown or ctx_obj.get("markdown")
    is_all_mode = ctx_obj.get("yes") or use_markdown

    workflow_success = test_exit_code == 0 and (publish_success or not publish_required)

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
                "version_update": {"from": current_version, "to": new_version},
                "git": {"commit_message": commit_msg, "files_changed": len(files)},
                "test_execution": {
                    "status": "passed" if test_exit_code == 0 else "failed",
                    "total_wall_time_seconds": round(
                        test_details.get("wall_time", 0.0), 2
                    ),
                    "sum_individual_test_time_seconds": round(
                        test_details.get("total_test_time", 0.0), 2
                    ),
                    "startup_and_collection_overhead_seconds": round(
                        test_details.get("startup_overhead", 0.0), 2
                    ),
                    "slowest_tests_top_5": slowest,
                    "tests_requiring_improvement": needs_improvement,
                },
                "planfile_updates": {"tickets_added": added_tickets},
                "publish": _build_publish_summary(
                    publish_success, publish_required, publish_skip_reason
                ),
            }
        }

        click.echo(click.style("\n=== GOAL RESULT (YAML) ===", fg="green", bold=True))
        click.echo(yaml.dump(yaml_report, sort_keys=False, allow_unicode=True))
        click.echo(click.style("==========================\n", fg="green", bold=True))

    if not (markdown or ctx_obj.get("markdown")):
        return

    from goal.formatter import format_push_result

    workflow_success = test_exit_code == 0 and (publish_success or not publish_required)
    success_emoji = "🎉" if workflow_success else "⚠"
    click.echo(
        click.style(
            f"\n{success_emoji} Process completed successfully!", fg="green", bold=True
        )
    )

    tagged = not no_tag and not publish_skip_reason
    actions = [
        "Detected project types",
        "Staged changes",
        "Ran tests" if test_exit_code == 0 else "Tests failed but continued",
        "Committed changes",
        f"Updated version to {new_version}",
        "Updated changelog",
        f"Created tag v{new_version}" if tagged else "Skipped tag creation",
        "Pushed to remote" if tagged else "Pushed to remote without tags",
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


def _has_committed_unreleased_sources() -> bool:
    """Return whether a clean tree still contains source after its last tag.

    The legacy no-change shortcut remains useful for an empty, synchronized
    repository. In ``-a`` mode we only cross that boundary when a registry
    package has committed source waiting for publication.
    """
    from goal.publish.changes import committed_unreleased_source_files

    project_types = list(detect_project_types_deep().keys())
    files = committed_unreleased_source_files(project_types)
    if files:
        return True
    # A publish-only release leaves no tag on the base branch, so the version
    # transition commit becomes its own boundary and the diff-vs-boundary
    # check comes back empty even though the registry never received the
    # release. A tree version newer than the published registry baseline is
    # pending publication regardless of that empty diff.
    return _registry_publication_pending(project_types)


def _managed_version_values() -> List[str]:
    """Return the distinct managed version declarations in the tree."""
    try:
        from goal.cli.version_state import collect_version_sources

        sources = collect_version_sources()
    except (ImportError, OSError, ValueError):
        return []
    return sorted({source.value for source in sources if source.value is not None})


def _registry_publication_pending(project_types: List[str]) -> bool:
    """Return whether the tree version is newer than the published registry."""
    if not project_types:
        return False
    try:
        from goal.cli.version_state import collect_version_sources
        from goal.version_validation import get_registry_version
    except ImportError:
        return False
    try:
        sources = collect_version_sources()
    except (OSError, ValueError):
        return False
    values = {getattr(source, "value", None) for source in sources}
    values.discard(None)
    if len(values) != 1:
        return False
    current = next(iter(values))

    registry = "pypi" if "python" in project_types else None
    if registry is None:
        return False
    try:
        package = tomllib.loads(
            Path("pyproject.toml").read_text(encoding="utf-8")
        )["project"]["name"]
    except (OSError, tomllib.TOMLDecodeError, KeyError):
        return False
    published = get_registry_version(registry, package)
    if not published or published == current:
        return False
    # The registry's "latest" document is CDN-cached right after an upload, so
    # a just-published tree can still look newer. Trust the version-specific
    # document before claiming that publication is pending.
    from goal.version_validation import exact_version_published

    if exact_version_published(registry, package, current):
        return False

    def _key(version: str) -> tuple:
        parts = re.findall(r"\d+", version.split("+")[0])
        return tuple(int(part) for part in parts) or (0,)

    try:
        return _key(current) > _key(published)
    except (TypeError, ValueError):
        return current != published


def _resume_pending_pull_request(
    ctx_obj: Dict[str, Any],
    project_types: List[str],
    markdown: bool,
    delivery: Any,
    ticket: str,
    candidate: Any,
) -> None:
    """Retest and deliver an immutable already committed PR candidate."""
    from goal.cli.version import get_current_version
    from goal.governance.delivery import (
        deliver_pull_request,
        pending_pull_request_delivery,
        record_delivery_event,
    )

    short_head = candidate.head_sha[:12]
    click.echo(
        click.style(
            f"Resuming governed pull-request delivery for committed HEAD {short_head}.",
            fg="yellow",
        )
    )
    current_version = get_current_version()
    record_delivery_event(
        delivery,
        "started",
        detail="resume already committed pull-request candidate",
    )
    _run_test_stage_or_exit(
        project_types,
        ctx_obj,
        markdown,
        list(candidate.files),
        {},
        current_version,
        current_version,
        candidate.title,
        "Already committed candidate; no new commit will be created.",
    )

    revalidated = pending_pull_request_delivery(delivery, ticket=ticket)
    if revalidated != candidate:
        raise click.ClickException(
            "pull-request resume candidate changed during test execution"
        )

    head, pr_url = deliver_pull_request(
        delivery,
        ticket=ticket,
        title=candidate.title,
    )
    record_delivery_event(
        delivery,
        "pull-request",
        detail=pr_url,
        head=head,
    )
    click.echo(click.style(f"Pull request: {pr_url}", fg="green"))
    if "_start_time" in ctx_obj:
        elapsed = time.time() - ctx_obj["_start_time"]
        ctx_obj["_elapsed_time"] = elapsed
        click.echo(click.style(f"\n⏱️  Total time: {elapsed:.1f}s", fg="cyan"))


def _remote_release_tag_commit_sha(remote: str, tag_name: str) -> str | None:
    """Resolve the remote commit SHA for a release tag without mutating refs."""
    result = run_git(
        "ls-remote",
        "--tags",
        remote,
        f"refs/tags/{tag_name}",
        f"refs/tags/{tag_name}^{{}}",
    )
    if getattr(result, "returncode", 1) != 0:
        detail = (getattr(result, "stderr", "") or "remote tag lookup failed").strip()
        raise click.ClickException(
            f"canonical direct-main release could not inspect remote tags on {remote}: {detail}"
        )
    stdout = getattr(result, "stdout", "") or ""
    direct_sha: str | None = None
    peeled_sha: str | None = None
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref == f"refs/tags/{tag_name}^{{}}":
            peeled_sha = sha
        elif ref == f"refs/tags/{tag_name}":
            direct_sha = sha
    return peeled_sha or direct_sha


def _push_completion_release_tag(delivery: Any, new_version: str) -> bool:
    """Create and push the annotated release tag after a completed publish.

    Governed modes skip the remote release tag before the merge because the
    commit is not on the base branch yet. Once the publication completed on
    the synchronized base, the release is final evidence and the tag belongs
    on that HEAD. Only the tag is pushed - no branch is ever moved.
    """
    from goal.governance.delivery import authorized_push

    tag_name = f"v{new_version}"
    existing = run_git("rev-parse", "-q", "--verify", f"refs/tags/{tag_name}")
    if existing.returncode != 0:
        created = run_git("tag", "-a", tag_name, "-m", f"Release {new_version}")
        if created.returncode != 0:
            click.echo(
                click.style(
                    f"⚠ Could not create release tag {tag_name}.", fg="yellow"
                )
            )
            return False
    with authorized_push(delivery):
        pushed = run_git("push", delivery.remote, tag_name, capture=True)
    if pushed.returncode != 0:
        click.echo(
            click.style(f"⚠ Could not push release tag {tag_name}.", fg="yellow")
        )
        return False
    click.echo(click.style(f"✓ Release tag {tag_name} pushed.", fg="green"))
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
    goal_skip_costs_badge = os.environ.pop("GOAL_SKIP_COSTS_BADGE", None)
    try:
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
    finally:
        if goal_skip_costs_badge is not None:
            os.environ["GOAL_SKIP_COSTS_BADGE"] = goal_skip_costs_badge

    if test_exit_code != 0 and ctx_obj["yes"]:
        if "_start_time" in ctx_obj:
            elapsed = time.time() - ctx_obj["_start_time"]
            ctx_obj["_elapsed_time"] = elapsed
            click.echo(click.style(f"\n⏱️  Total time: {elapsed:.1f}s", fg="cyan"))
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
    koru: bool = False,
) -> None:
    """Execute the complete push workflow."""

    start_time = time.time()
    ctx_obj["_start_time"] = start_time
    ctx_obj["_preflight_time"] = 0.0

    # Keep the invariant at the workflow boundary as well as in the Click
    # context. This covers library callers and compatibility shims that pass
    # only ``all_flags`` instead of going through ``_configure_main_context``.
    all_flags = bool(ctx_obj.get("all_flags", False))
    if model is not None:
        ctx_obj.setdefault("model", model)
    if api_key is not None:
        ctx_obj.setdefault("api_key", api_key)
    koru_enabled = koru or bool(ctx_obj.get("koru", False))

    if koru_enabled:
        from goal.governance.remediation import format_koru_repair_summary, run_koru_repair

        verbose = bool(ctx_obj.get("verbose", False))
        click.echo(click.style("Running Koru auto-repair (--doctor --repair)...", fg="cyan"))
        success, repair_detail = run_koru_repair()
        if success:
            summary = format_koru_repair_summary(repair_detail)
            click.echo(click.style(f"✓ Koru auto-repair succeeded{summary}", fg="green"))
            if verbose and repair_detail:
                click.echo(repair_detail)
        else:
            click.echo(click.style(f"⚠ Koru auto-repair: {repair_detail}", fg="yellow"))

    explicit_force_publish = bool(force_publish)
    explicit_force_publish = explicit_force_publish or bool(
        ctx_obj.get("force_publish_explicit", False)
    )
    # A context carrying force_publish without the provenance marker is an
    # older direct caller, so retain its explicit-force semantics unless it is
    # the value derived from --all.
    explicit_force_publish = explicit_force_publish or bool(
        ctx_obj.get("force_publish", False) and not all_flags
    )
    force_publish = explicit_force_publish or all_flags

    from goal.governance.delivery import (
        CanonicalReleaseAdmission,
        authorized_push,
        deliver_pull_request,
        pending_pull_request_delivery,
        record_delivery_event,
        resolve_pull_request_ticket,
        resolve_delivery_policy,
        validate_canonical_release_checkout,
        validate_delivery_ready,
        validate_legacy_governance,
    )

    delivery = resolve_delivery_policy(
        ctx_obj.get("config"),
        ctx_obj.get("delivery_mode"),
        all_flags=bool(ctx_obj.get("all_flags", False)),
    )
    canonical_release: CanonicalReleaseAdmission | None = None
    if delivery is not None:
        if delivery.mode == "publish-only" and (
            no_publish or ctx_obj.get("no_publish", False)
        ):
            raise click.ClickException("publish-only conflicts with --no-publish")
        if delivery.mode == "pull-request" and ticket is not None:
            ticket = resolve_pull_request_ticket(delivery, ticket)
        preflight_start = time.time()
        try:
            if delivery.mode == "direct-main" and ticket is not None:
                maybe_admission = validate_delivery_ready(delivery, ticket=ticket)
            else:
                maybe_admission = validate_delivery_ready(delivery)
            if isinstance(maybe_admission, CanonicalReleaseAdmission):
                canonical_release = maybe_admission
        finally:
            ctx_obj["_preflight_time"] = (
                ctx_obj.get("_preflight_time", 0.0) + (time.time() - preflight_start)
            )
            ctx_obj["_elapsed_time"] = time.time() - start_time
        ctx_obj["delivery_mode"] = delivery.mode
        if canonical_release is not None:
            ctx_obj["_suppress_goal_owned_cost_badge"] = True
            record_delivery_event(
                delivery,
                "release-preflight",
                detail=(
                    f"ticket={canonical_release.ticket} "
                    f"lease={canonical_release.lease_id} "
                    f"receipt={canonical_release.merge_receipt_ref}"
                ),
                head=canonical_release.head_sha,
            )
    else:
        preflight_start = time.time()
        try:
            no_change = validate_legacy_governance(
                check_no_change=all_flags
                and not any(
                    (ticket, force, explicit_force_publish, ctx_obj.get("version"))
                )
            )
        finally:
            ctx_obj["_preflight_time"] = (
                ctx_obj.get("_preflight_time", 0.0) + (time.time() - preflight_start)
            )
            ctx_obj["_elapsed_time"] = time.time() - start_time
        if no_change is True:
            if all_flags and _has_committed_unreleased_sources():
                click.echo(
                    "Committed package source is pending publication; continuing -a workflow."
                )
                no_change = False
            else:
                click.echo("No changes to deliver; the remote default branch is synchronized.")
                return

    _validate_toml_or_exit(dry_run)

    _initialize_context(ctx_obj, bump, message, yes, markdown)

    yes = ctx_obj["yes"]
    no_publish = no_publish or ctx_obj.get("no_publish", False)
    if delivery is not None and delivery.mode == "pull-request":
        no_publish = True
        ctx_obj["_suppress_goal_owned_cost_badge"] = True
        click.echo(
            click.style(
                "Governed pull-request mode: registry publish waits for merge.",
                fg="yellow",
            )
        )

    if delivery is not None:
        if ticket is None:
            ticket = resolve_pull_request_ticket(delivery, ticket)
        if delivery.mode == "pull-request" and ticket is None:
            disagreeing = _managed_version_values()
            if len(disagreeing) > 1:
                # A coordinated release lands its version projection across
                # workstream tickets; between them the managed declarations
                # disagree. Name that exact state instead of a generic
                # release-ticket or clean force-publish message.
                raise click.ClickException(
                    "Managed version sources disagree ("
                    + ", ".join(disagreeing)
                    + "): land the remaining coordinated release tickets "
                    "(version files and runtime banner) before running goal -a."
                )
            if _has_committed_unreleased_sources():
                if not _registry_publication_pending(
                    list(detect_project_types_deep().keys())
                ):
                    # Sources landed after the last release tag but the tree
                    # version still matches the registry: this is ordinary
                    # unreleased work, not a pre-bumped release waiting for
                    # its publish. Governed delivery cannot commit on the base
                    # branch, so name the actionable route instead of failing
                    # later in the clean publish-only validation.
                    from goal.publish.changes import _latest_release_tag

                    latest = _latest_release_tag() or "the last release"
                    raise click.ClickException(
                        "Committed package sources are unreleased since "
                        f"{latest}; governed pull-request delivery requires a "
                        "release ticket. Allocate one and run goal -a from its "
                        "ticket branch."
                    )
                click.echo(
                    click.style(
                        "Merged release is pending publication; completing the "
                        "publish on the synchronized base.",
                        fg="yellow",
                    )
                )
                # The protected merge already happened: finish tag + registry
                # publish without creating a new commit. ``clean_force_publish``
                # downstream skips the commit and the release machinery
                # publishes the committed package sources.
                no_publish = False
                ctx_obj["no_publish"] = False
                force_publish = True
                ctx_obj["force_publish"] = True
                ctx_obj["_publish_completion"] = True
                record_delivery_event(
                    delivery,
                    "publish-completion",
                    detail="pending publication on synchronized base",
                )
            else:
                record_delivery_event(delivery, "no-change", detail="clean synchronized base")
                click.echo("No changes to deliver; base is synchronized and no ticket is active.")
                return

    project_types = _detect_project_types()

    if (
        not dry_run
        and delivery is not None
        and delivery.mode == "pull-request"
        and ticket
    ):
        pending_delivery = pending_pull_request_delivery(delivery, ticket=ticket)
        if pending_delivery is not None:
            _resume_pending_pull_request(
                ctx_obj,
                project_types,
                markdown,
                delivery,
                ticket,
                pending_delivery,
            )
            return

    # Run dependency updates before bootstrap: uv sync removes packages (like goal)
    # that are not listed in the project lockfile.
    if ctx_obj.get("upgrade_deps"):
        from goal.dependency_update import update_project_dependencies

        update_results = update_project_dependencies(
            yes=ctx_obj["yes"],
            dry_run=dry_run or ctx_obj.get("dry_run", False),
            recursive=ctx_obj.get("recursive", False),
            interactive=ctx_obj.get("interactive", False),
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

    _bootstrap_projects_for_delivery(
        project_types,
        dry_run,
        yes,
        "publish-only"
        if canonical_release is not None
        else (delivery.mode if delivery is not None else None),
    )

    if ctx_obj.get("upgrade_deps"):
        refresh_test_dependencies(project_types, yes=yes, dry_run=dry_run)

    _require_publish_bootstrap_read_only(
        delivery, canonical_release=canonical_release is not None
    )

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

    if delivery is not None and delivery.mode == "pull-request":
        preflight_start = time.time()
        try:
            validate_delivery_ready(delivery)
        finally:
            ctx_obj["_preflight_time"] = (
                ctx_obj.get("_preflight_time", 0.0) + (time.time() - preflight_start)
            )
            ctx_obj["_elapsed_time"] = time.time() - start_time

    if not dry_run:
        run_git("add", "-A")

    files = get_staged_files()
    has_staged_files = bool(files and files != [""])
    if canonical_release is not None:
        if has_staged_files or get_working_tree_files():
            raise click.ClickException(
                "canonical direct-main release requires a clean release worktree; "
                "source changes must land via pull-request before release publication"
            )
        force_publish = True
        ctx_obj["force_publish"] = True
    clean_force_publish = bool(
        (force_publish and not no_publish and not has_staged_files)
        or (canonical_release is not None and not has_staged_files)
    )
    if not clean_force_publish and _handle_no_files(
        ctx_obj, project_types, dry_run, markdown, files
    ):
        return

    _validate_staged_files(ctx_obj, dry_run, force)

    # Decide early whether this run should bump+commit+release. When the project
    # is a registry project but no staged file is package source (only docs,
    # metadata, lockfiles, tests or generated caches), bumping the version and
    # committing produces churn: the version races ahead of what is published.
    # Skip the release machinery in that case. A non-registry repository also
    # gets a plain commit: there is no package version or release to advance.
    # --force-publish overrides to release anyway.
    from goal.publish.changes import analyze_publishable_changes

    commit_only = _commit_only_requested(
        no_version_sync=no_version_sync,
        no_tag=no_tag,
        no_publish=no_publish,
    )
    early_change_report = (
        None if force_publish else analyze_publishable_changes(files, project_types)
    )
    skip_release = commit_only or bool(
        early_change_report
        and early_change_report.reason
        in {"no_package_source_changes", "no_registry_project_types"}
    )
    if skip_release and not commit_only:
        # Staged files alone miss source changes that are already committed
        # (agents commit, then a later `goal -a` sees a clean tree and skips
        # while the registry stays behind HEAD). Release when the last v* tag
        # is missing committed package source.
        from goal.publish.changes import committed_unreleased_source_files

        pending_committed = committed_unreleased_source_files(project_types)
        if pending_committed:
            preview = ", ".join(pending_committed[:3])
            more = (
                f" (+{len(pending_committed) - 3} more)"
                if len(pending_committed) > 3
                else ""
            )
            click.echo(
                click.style(
                    f"📦 {len(pending_committed)} package source file(s) committed since the "
                    f"last release tag — releasing: {preview}{more}",
                    fg="yellow",
                )
            )
            skip_release = False

    diff_content = get_diff_content()
    stats = get_diff_stats()

    if clean_force_publish:
        commit_title = message or "release: publish pre-merged version"
        commit_body = "Clean publish-only release; no commit was created."
        detailed_result = {}
    else:
        commit_title, commit_body, detailed_result = get_commit_message(
            ctx_obj, files, diff_content, message, ticket, abstraction
        )

        if _abort_if_missing_commit_title(commit_title):
            return

    commit_msg = commit_title

    try:
        resolved_version = get_version_info(
            bump=bump,
            target_version=ctx_obj.get("version"),
            config=ctx_obj.get("config"),
            project_types=project_types,
            include_decision=True,
            release_required=not skip_release,
            allow_registry_ahead_repair=bool(ctx_obj.get("all_flags", False)),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if len(resolved_version) == 3:
        current_version, new_version, version_decision = resolved_version
    else:  # compatibility with extensions/tests returning the legacy tuple
        current_version, new_version = resolved_version
        version_decision = None
        if skip_release:
            new_version = current_version

    existing_release_repair = False
    if version_decision is not None:
        version_decision, existing_release_repair = (
            _recover_existing_generic_release_decision(
                current_version,
                version_decision,
                clean_force_publish=clean_force_publish,
                delivery=delivery,
                project_types=project_types,
                publish_config=ctx_obj.get("config"),
            )
        )
        if existing_release_repair:
            new_version = current_version

    version_release_intent = bool(
        not commit_only
        and skip_release
        and version_decision is not None
        and version_decision.reason
        in {"already-bumped", "partial-bump", "explicit-target"}
        and new_version != current_version
    )
    if version_release_intent:
        skip_release = False
        click.echo(
            click.style(
                "📦 Explicit/pre-bumped version state requests a release despite "
                "metadata-only staged changes.",
                fg="yellow",
            )
        )

    if version_decision is not None:
        from goal.cli.version_state import format_version_decision

        for line in format_version_decision(version_decision):
            click.echo(line)

    ctx_obj["version_decision"] = version_decision

    if clean_force_publish:
        if version_decision is None or version_decision.reason not in {
            "already-bumped",
            "explicit-target",
            "existing-tag-release-repair",
        }:
            reason = getattr(version_decision, "reason", "unresolved")
            raise click.ClickException(
                "clean --force-publish requires an already synchronized, "
                f"pre-bumped release version (decision: {reason})"
            )
        from goal.cli.version_state import validate_version_sources

        validate_version_sources(version_decision.managed_specs, new_version)

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

    if delivery is not None:
        record_delivery_event(delivery, "started")

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

    if canonical_release is not None:
        revalidated = validate_canonical_release_checkout(
            delivery, ticket=canonical_release.ticket
        )
        if revalidated != canonical_release:
            raise click.ClickException(
                "canonical direct-main release state changed during test execution"
            )
        if not no_tag:
            expected_tag = f"v{new_version}"
            remote_tag_sha = _remote_release_tag_commit_sha(
                delivery.remote, expected_tag
            )
            if remote_tag_sha is not None:
                if not existing_release_repair:
                    raise click.ClickException(
                        f"canonical direct-main release tag {expected_tag} already exists on {delivery.remote}"
                    )
                if remote_tag_sha != canonical_release.head_sha:
                    raise click.ClickException(
                        f"canonical direct-main release repair tag {expected_tag} on {delivery.remote} "
                        f"points to {remote_tag_sha[:12]}, expected {canonical_release.head_sha[:12]}"
                    )
        record_delivery_event(
            delivery,
            "release-tests-qualified",
            detail=f"ticket={canonical_release.ticket} version=v{new_version}",
            head=canonical_release.head_sha,
        )

    if clean_force_publish:
        # This path intentionally creates no commit, so it must remain clean.
        ctx_obj["added_slow_test_tickets"] = []
    else:
        files = _prepare_slow_test_tickets(ctx_obj, files)
        stats = get_diff_stats()

    if clean_force_publish:
        click.echo(
            click.style(
                f"📦 Publishing pre-merged clean release v{new_version}; "
                "no commit will be created.",
                fg="yellow",
            )
        )
    elif skip_release:
        skip_reason = (
            "explicit commit-only flags" if commit_only else "no package source changes"
        )
        click.echo(
            click.style(
                f"⏭ Skipping version bump and publish (staying on v{current_version}) "
                f"— {skip_reason}. Use --force-publish to release anyway.",
                fg="yellow",
            )
        )
        # Still commit + push the docs/metadata changes (README badge,
        # local.dev.txt, lockfiles — often goal's own generated output) so the
        # working tree doesn't accumulate them uncommitted forever. This is a
        # plain commit with NO version bump, changelog, tag, or publish.
        if version_decision is not None and version_decision.local_drift:
            handle_version_sync(
                new_version,
                no_version_sync,
                ctx_obj.get("user_config"),
                ctx_obj["yes"],
                version_decision,
            )
        commit_succeeded = _commit_without_release(
            ctx_obj, commit_title, commit_body, commit_msg, message
        )
        if commit_succeeded is False:
            if delivery is not None:
                record_delivery_event(
                    delivery,
                    "commit-failed",
                    detail="docs/metadata commit failed",
                )
            raise click.ClickException(
                "docs/metadata commit failed; publish, tag, and push were not attempted"
            )
    else:
        commit_succeeded = _handle_commit_phase(
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
        if commit_succeeded is False:
            if delivery is not None:
                record_delivery_event(
                    delivery,
                    "commit-failed",
                    detail="release commit failed",
                )
            raise click.ClickException(
                "release commit failed; publish, tag, and push were not attempted"
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
        force_publish=force_publish or version_release_intent,
    )

    publish_skip_reason = (
        publish_change_report.skip_reason if publish_change_report else None
    )
    publish_required = ctx_obj["yes"] and not no_publish and not publish_skip_reason
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

    # Don't create an orphan release tag when publish was skipped because there
    # were no package source changes — avoids tags that map to no registry release.
    skip_tag_no_source = bool(publish_skip_reason)
    if skip_tag_no_source and not no_tag:
        click.echo(
            click.style(
                f"⏭ Skipping tag v{new_version} — no package source changes to release",
                fg="yellow",
            )
        )
    governed_no_tag = bool(
        delivery is not None and delivery.mode in {"publish-only", "pull-request"}
    )
    effective_no_tag = no_tag or skip_tag_no_source or governed_no_tag
    if governed_no_tag and not no_tag:
        click.echo(
            click.style(
                f"Governed {delivery.mode} mode: remote release tag skipped.",
                fg="yellow",
            )
        )
    tag_name = create_tag(new_version, effective_no_tag)
    tag_name = _resolve_release_tag(
        new_version,
        tag_name,
        effective_no_tag=effective_no_tag,
        delivery=delivery,
        clean_force_publish=clean_force_publish,
    )

    if delivery is None:
        from goal.git_ops import get_remote_branch

        branch = get_remote_branch()
        pushed = push_to_remote(branch, tag_name, no_tag, ctx_obj["yes"])
        if pushed is False:
            raise click.ClickException("Git remote push failed")
    elif delivery.mode == "publish-only":
        record_delivery_event(
            delivery,
            "published" if publish_success else "publish-skipped",
            detail=publish_skip_reason or "",
        )
        click.echo(
            click.style(
                "Governed publish-only mode: Git remote push skipped.",
                fg="green",
            )
        )
    elif delivery.mode == "direct-main":
        if canonical_release is not None:
            revalidated = validate_canonical_release_checkout(
                delivery, ticket=canonical_release.ticket
            )
            if revalidated != canonical_release:
                raise click.ClickException(
                    "canonical direct-main release state changed before tag publication"
                )
            pushed = True
            if tag_name and not effective_no_tag:
                remote_tag_sha = _remote_release_tag_commit_sha(
                    delivery.remote, tag_name
                )
                if remote_tag_sha is not None:
                    if (
                        existing_release_repair
                        and remote_tag_sha == canonical_release.head_sha
                    ):
                        record_delivery_event(
                            delivery,
                            "release-tag-reused",
                            detail=f"ticket={canonical_release.ticket} tag={tag_name}",
                            head=canonical_release.head_sha,
                        )
                    else:
                        raise click.ClickException(
                            f"canonical direct-main release tag {tag_name} already exists on {delivery.remote}"
                        )
                else:
                    with authorized_push(delivery):
                        push_result = run_git(
                            "push",
                            delivery.remote,
                            f"refs/tags/{tag_name}",
                            capture=True,
                        )
                    pushed = getattr(push_result, "returncode", 1) == 0
                    if pushed:
                        record_delivery_event(
                            delivery,
                            "release-tag",
                            detail=f"ticket={canonical_release.ticket} tag={tag_name}",
                            head=canonical_release.head_sha,
                        )
            record_delivery_event(
                delivery,
                "pushed" if pushed else "push-failed",
                detail=f"ticket={canonical_release.ticket} tag={tag_name or 'none'}",
                head=canonical_release.head_sha,
            )
            if not pushed:
                raise click.ClickException("governed direct-main push failed")
        else:
            with authorized_push(delivery):
                pushed = push_to_remote(
                    delivery.base_branch,
                    tag_name,
                    no_tag,
                    ctx_obj["yes"],
                    remote=delivery.remote,
                )
            record_delivery_event(delivery, "pushed" if pushed else "push-failed")
            if not pushed:
                raise click.ClickException("governed direct-main push failed")
    else:
        if ctx_obj.get("_publish_completion"):
            # The completion already finished the cycle on the synchronized
            # base (the registry upload is done). A pull-request epilogue has
            # no commit to deliver and would only push an empty branch. The
            # release tag skipped before the merge is created here instead.
            tag_pushed = False
            if publish_success and not no_tag:
                tag_pushed = _push_completion_release_tag(delivery, new_version)
            detail = "publish completion on synchronized base"
            if tag_pushed:
                detail += "; release tag pushed"
            record_delivery_event(
                delivery,
                "published" if publish_success else "publish-skipped",
                detail=detail,
            )
            click.echo(
                click.style(
                    "Governed pull-request mode: publication completed on the "
                    "synchronized base; no pull request needed.",
                    fg="green",
                )
            )
        else:
            head, pr_url = deliver_pull_request(
                delivery,
                ticket=ticket,
                title=commit_title,
            )
            record_delivery_event(delivery, "pull-request", detail=pr_url, head=head)
            click.echo(click.style(f"Pull request: {pr_url}", fg="green"))

    # Optionally mirror the git tag as a GitHub Release (Releases page ≠ tags).
    # Without this, tags advance while /releases/latest stays frozen until PyPI
    # is blocked and the fallback path runs.
    _mirror_github_release(
        tag_name=tag_name,
        effective_no_tag=effective_no_tag,
        delivery=delivery,
        project_types=project_types,
        new_version=new_version,
        publish_config=publish_config,
    )

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


def _bootstrap_projects_for_delivery(
    project_types: List[str],
    dry_run: bool,
    yes: bool,
    delivery_mode: Optional[str],
) -> None:
    """Keep Goal-owned badge generation out of governed delivery trees."""
    if delivery_mode not in {"publish-only", "pull-request"}:
        _bootstrap_projects(project_types, dry_run, yes)
        return

    markers = ("GOAL_SKIP_COSTS_BADGE", "GOAL_BOOTSTRAP_READ_ONLY")
    previous = {marker: os.environ.get(marker) for marker in markers}
    for marker in markers:
        os.environ[marker] = "1"
    try:
        _bootstrap_projects(project_types, dry_run, yes)
    finally:
        for marker, value in previous.items():
            if value is None:
                os.environ.pop(marker, None)
            else:
                os.environ[marker] = value


def _require_publish_bootstrap_read_only(
    delivery: Any, *, canonical_release: bool = False
) -> None:
    """Abort before staging when publish-only or canonical release bootstrap changed the source tree."""
    if delivery is None or (
        delivery.mode != "publish-only" and not canonical_release
    ):
        return

    changed = list(dict.fromkeys([*get_staged_files(), *get_working_tree_files()]))
    if changed:
        preview = ", ".join(changed[:5])
        suffix = f" (+{len(changed) - 5} more)" if len(changed) > 5 else ""
        raise click.ClickException(
            "publish-only bootstrap modified the trusted source tree: "
            f"{preview}{suffix}"
        )


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
        click.echo(
            "# Goal Push Result\n\n"
            "No changes to commit. No commit was created and the version was unchanged."
        )
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


def _commit_without_release(
    ctx_obj: Dict[str, Any],
    commit_title: str,
    commit_body: Optional[str],
    commit_msg: str,
    message: Optional[str],
) -> bool:
    """Commit already-staged docs/metadata changes with no bump/tag/publish.

    Used in ``skip_release`` mode so the working tree doesn't keep accumulating
    goal's own generated docs/metadata (badges, lockfiles) as uncommitted noise.
    """
    from goal.cli import confirm

    if not ctx_obj["yes"]:
        if not confirm("Commit docs/metadata changes (no release)?"):
            click.echo(click.style("  Skipping commit (user chose N).", fg="yellow"))
            return True
    else:
        click.echo(
            click.style(
                "🤖 AUTO: Committing docs/metadata, no release (--all mode)", fg="cyan"
            )
        )
    return handle_single_commit(
        commit_title, commit_body, commit_msg, message, ctx_obj["yes"]
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
) -> bool:
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
        return handle_split_commits(
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
        version_decision = ctx_obj.get("version_decision")
        if version_decision is None:
            handle_version_sync(
                new_version, no_version_sync, user_config, ctx_obj["yes"]
            )
        else:
            handle_version_sync(
                new_version,
                no_version_sync,
                user_config,
                ctx_obj["yes"],
                version_decision,
            )

        # Changelog
        config_dict = (
            (ctx_obj.get("config") or {}).to_dict() if ctx_obj.get("config") else None
        )
        handle_changelog(new_version, files, commit_msg, config_dict, no_changelog)

        # Refresh costs README content before committing so the update is included.
        suppress_cost_badge = bool(
            os.getenv("GOAL_SKIP_COSTS_BADGE")
            or ctx_obj.get("_suppress_goal_owned_cost_badge")
        )
        if not suppress_cost_badge and _update_cost_badges(ctx_obj, new_version):
            run_git_local("add", "README.md")

        # Single commit
        return handle_single_commit(
            commit_title, commit_body, commit_msg, message, ctx_obj["yes"]
        )


# Backward-compat shims — moved to goal.push.stages.costs
from goal.push.stages.costs import (  # noqa: E402
    update_cost_badges as _update_cost_badges,
)
