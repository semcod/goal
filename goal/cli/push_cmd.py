"""Push command - extracted and refactored from cli.py."""

import click
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from ..git_ops import run_git, get_staged_files, get_diff_content, get_diff_stats, ensure_remote, get_remote_branch, _echo_cmd
    from ..commit_generator import CommitMessageGenerator
    from ..enhanced_summary import QualityValidator
    from ..formatter import format_push_result, format_enhanced_summary
    from ..project_bootstrap import detect_project_types_deep, bootstrap_project
    from ..changelog import update_changelog
    from . import main, confirm, apply_ticket_prefix, stage_paths
    from .version import get_current_version, bump_version, detect_project_types, sync_all_versions
    from .tests import run_tests
    from .publish import publish_project
except ImportError:
    from goal.git_ops import run_git, get_staged_files, get_diff_content, get_diff_stats, ensure_remote, get_remote_branch, _echo_cmd
    from goal.commit_generator import CommitMessageGenerator
    from goal.enhanced_summary import QualityValidator
    from goal.formatter import format_push_result, format_enhanced_summary
    from goal.project_bootstrap import detect_project_types_deep, bootstrap_project
    from goal.changelog import update_changelog
    from goal.cli import main, confirm, apply_ticket_prefix, stage_paths
    from goal.cli.version import get_current_version, bump_version, detect_project_types, sync_all_versions
    from goal.cli.tests import run_tests
    from goal.cli.publish import publish_project


def _get_commit_message(ctx, files: List[str], diff_content: str, message: Optional[str], 
                        ticket: Optional[str], abstraction: Optional[str]) -> tuple:
    """Generate or use provided commit message."""
    if message:
        return apply_ticket_prefix(message, ticket), None, None
    
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else None
    generator = CommitMessageGenerator(config=config_dict)
    
    use_enhanced = bool((config_dict or {}).get('quality', {}).get('enhanced_summary', {}).get('enabled', False))
    
    if use_enhanced:
        detailed = generator.generate_detailed_message(cached=True)
        if detailed and detailed.get('enhanced'):
            title = apply_ticket_prefix(detailed.get('title'), ticket)
            return title, detailed.get('body'), detailed
    
    # Use abstraction-based generation if available
    if abstraction != 'legacy' and config_dict:
        abstraction_result = generator.generate_abstraction_message(level=abstraction, cached=True)
        if abstraction_result:
            title = apply_ticket_prefix(abstraction_result.get('title'), ticket)
            return title, abstraction_result.get('body'), None
    
    # Fallback to detailed message
    detailed = generator.generate_detailed_message(cached=True)
    if detailed:
        title = apply_ticket_prefix(detailed.get('title'), ticket)
        return title, detailed.get('body'), detailed
    
    # Final fallback
    return None, None, None


def _enforce_quality_gates(ctx, commit_msg: str, detailed_result: Dict, files: List[str], 
                           total_adds: int, total_dels: int, yes: bool, markdown: bool) -> str:
    """Enforce commit quality gates for auto-generated messages."""
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else {}
    quality_cfg = (config_dict or {}).get('quality', {}).get('enhanced_summary', {})
    
    if not quality_cfg.get('enabled', True):
        return commit_msg
    
    try:
        validator = QualityValidator(config_dict or {})
        
        summary = {
            'title': commit_msg,
            'intent': detailed_result.get('intent'),
            'metrics': {
                'lines_added': total_adds,
                'lines_deleted': total_dels,
            }
        }
        
        validation = validator.validate(summary, detailed_result.get('files') or files)
        
        if validation.get('valid', True):
            return commit_msg
        
        suggested = validator.auto_fix(summary, files, total_adds, total_dels)
        suggested_title = (suggested or {}).get('title', '')
        
        if not suggested_title or suggested_title == commit_msg:
            return commit_msg
        
        apply_fix = True
        if not yes:
            apply_fix = confirm(f"Apply suggested title?\n\nCurrent: {commit_msg}\nSuggested: {suggested_title}")
        
        if apply_fix:
            commit_msg = suggested_title
            if markdown or ctx.obj.get('markdown'):
                click.echo(f"\n- **Applied title fix:** `{commit_msg}`")
            else:
                click.echo(click.style(f"\n✓ Applied title fix: {commit_msg}", fg='green'))
        
        return commit_msg
    except Exception:
        return commit_msg


def _handle_dry_run(ctx, project_types, files, stats, current_version, new_version, 
                    commit_msg, commit_body, detailed_result, split, ticket, bump, 
                    no_version_sync, no_changelog, no_tag, markdown):
    """Handle dry run output."""
    if split and not ctx.obj.get('message'):
        config_dict = (ctx.obj.get('config') or {}).to_dict() if ctx.obj.get('config') else None
        generator = CommitMessageGenerator(config=config_dict)
        groups = stage_paths.__module__ and __import__('goal.cli', fromlist=['split_paths_by_type']).split_paths_by_type(files)
        
        plan_lines = []
        for gname in ['code', 'docs', 'ci', 'examples', 'other']:
            if gname not in groups:
                continue
            d = generator.generate_detailed_message(cached=True, paths=groups[gname])
            if not d:
                continue
            title = apply_ticket_prefix(d.get('title'), ticket)
            plan_lines.append(f"- {gname}: {title} ({len(groups[gname])} files)")
        
        if not no_version_sync or not no_changelog:
            plan_lines.append(f"- release: chore(release): bump to {new_version}")
        
        commit_body = (commit_body or '')
        commit_body = ("Planned split commits:\n" + "\n".join(plan_lines)).strip()
    
    if markdown or ctx.obj.get('markdown'):
        if detailed_result and detailed_result.get('enhanced'):
            md_output = format_enhanced_summary(
                commit_title=commit_msg,
                commit_body=commit_body or '',
                capabilities=detailed_result.get('capabilities'),
                roles=detailed_result.get('roles'),
                relations=detailed_result.get('relations'),
                metrics=detailed_result.get('metrics'),
                files=files,
                stats=stats,
                current_version=current_version,
                new_version=new_version
            )
        else:
            md_output = format_push_result(
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
                    "Planned push to remote"
                ]
            )
        click.echo(md_output)
    else:
        click.echo(click.style("=== DRY RUN ===", fg='cyan', bold=True))
        if project_types:
            click.echo(f"Project types: {', '.join(project_types)}")
        total_adds = sum(s[0] for s in stats.values())
        total_dels = sum(s[1] for s in stats.values())
        click.echo(f"Files to commit: {len(files)} (+{total_adds}/-{total_dels} lines)")
        click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
        click.echo(f"Version: {current_version} -> {new_version}")


def _show_workflow_preview(files, stats, current_version, new_version, commit_msg, commit_body, markdown, ctx):
    """Show workflow preview for interactive mode."""
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    denom = (total_adds + total_dels) or 1
    deletion_pct = int((total_dels / denom) * 100)
    net = total_adds - total_dels
    
    if markdown or ctx.obj.get('markdown'):
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


def _run_test_stage(project_types, yes, markdown, ctx, files, stats, current_version, 
                    new_version, commit_msg, commit_body):
    """Run tests with interactive or auto mode."""
    test_result = None
    test_exit_code = 0
    
    if not yes:
        if confirm("Run tests?"):
            click.echo(click.style("\nRunning tests...", fg='cyan'))
            test_success = run_tests(project_types)
            if not test_success:
                test_exit_code = 1
                if not confirm("Tests failed. Continue anyway?", default=False):
                    if markdown or ctx.obj.get('markdown'):
                        md_output = format_push_result(
                            project_types=project_types,
                            files=files,
                            stats=stats,
                            current_version=current_version,
                            new_version=new_version,
                            commit_msg=commit_msg,
                            commit_body=commit_body,
                            test_result="Tests failed - aborted by user",
                            test_exit_code=1,
                            actions=["Detected project types", "Staged changes", "Attempted to run tests"],
                            error="User aborted due to test failures"
                        )
                        click.echo(md_output)
                    click.echo(click.style("Aborted.", fg='red'))
                    sys.exit(1)
        else:
            click.echo(click.style("  🤖 AUTO: Skipping tests (user chose N)", fg='cyan'))
    else:
        click.echo(click.style("\n🤖 AUTO: Running tests (--all mode)", fg='cyan'))
        try:
            test_success = run_tests(project_types)
            if not test_success:
                test_exit_code = 1
                test_result = "Tests failed - continuing anyway"
                click.echo(click.style("⚠️  Tests failed, but continuing due to --all/--yes mode.", fg='yellow', bold=True))
            else:
                test_exit_code = 0
                test_result = "Tests passed"
                click.echo(click.style("✓ All tests passed successfully", fg='green', bold=True))
        except Exception as e:
            test_exit_code = 1
            test_result = f"Test execution error: {str(e)}"
            click.echo(click.style(f"⚠️  Error running tests: {str(e)}. Continuing...", fg='yellow', bold=True))
    
    return test_result, test_exit_code


def _handle_split_commits(ctx, files, ticket, new_version, current_version, no_version_sync, no_changelog, yes):
    """Handle split commits per file group."""
    config_dict = (ctx.obj.get('config') or {}).to_dict() if ctx.obj.get('config') else None
    generator = CommitMessageGenerator(config=config_dict)
    
    from . import split_paths_by_type
    groups = split_paths_by_type(files)
    
    if not yes:
        click.echo(click.style("\nSplit commits plan:", fg='cyan', bold=True))
        for gname in ['code', 'docs', 'ci', 'examples', 'other']:
            if gname in groups:
                d = generator.generate_detailed_message(cached=False, paths=groups[gname])
                title = apply_ticket_prefix(d.get('title'), ticket) if d else gname
                click.echo(f"- {gname}: {title} ({len(groups[gname])} files)")
    
    # Commit each group
    for gname in ['code', 'docs', 'ci', 'examples', 'other']:
        if gname not in groups:
            continue
        
        stage_paths(groups[gname])
        d = generator.generate_detailed_message(cached=True, paths=groups[gname])
        if not d:
            continue
        
        title = apply_ticket_prefix(d.get('title'), ticket)
        body = d.get('body')
        result = run_git('commit', '-m', title, '-m', body)
        
        if result.returncode != 0:
            click.echo(click.style(f"✗ Error committing split group {gname}: {result.stderr}", fg='red'))
            if not yes:
                sys.exit(1)
            continue
        
        click.echo(click.style(f"✓ Committed ({gname}): {title}", fg='green'))
    
    # Release meta commit
    if (not no_version_sync) or (not no_changelog):
        if not no_version_sync:
            user_config = ctx.obj.get('user_config')
            updated_files = sync_all_versions(new_version, user_config)
            stage_paths(updated_files)
        else:
            Path('VERSION').write_text(new_version + '\n')
            stage_paths(['VERSION'])
        
        if not no_changelog:
            config_dict = (ctx.obj.get('config') or {}).to_dict() if ctx.obj.get('config') else None
            update_changelog(new_version, files, f"chore(release): bump version to {new_version}", config=config_dict)
            stage_paths(['CHANGELOG.md'])
        
        release_title = apply_ticket_prefix(f"chore(release): bump version to {new_version}", ticket)
        release_body = f"Release metadata\n\nVersion: {current_version} -> {new_version}"
        result = run_git('commit', '-m', release_title, '-m', release_body)
        
        if result.returncode != 0:
            click.echo(click.style(f"Error committing release metadata: {result.stderr}", fg='red'))
        else:
            click.echo(click.style(f"✓ Committed (release): {release_title}", fg='green'))


def _handle_single_commit(commit_title, commit_body, commit_msg, message, yes):
    """Handle single commit (non-split mode)."""
    if message == "__split__":
        return True
    
    if commit_body and not message:
        result = run_git('commit', '-m', commit_title, '-m', commit_body)
    else:
        result = run_git('commit', '-m', commit_msg)
    
    if result.returncode != 0:
        click.echo(click.style(f"✗ Error committing: {result.stderr}", fg='red'))
        if not yes:
            sys.exit(1)
        return False
    
    if message != "__split__":
        click.echo(click.style(f"✓ Committed successfully: {commit_msg}", fg='green'))
    
    return True


def _handle_version_sync(new_version, no_version_sync, user_config, yes):
    """Sync versions to all project files."""
    if not no_version_sync:
        updated_files = sync_all_versions(new_version, user_config)
        for f in updated_files:
            run_git('add', f)
            click.echo(click.style(f"✓ Updated {f} to {new_version}", fg='green'))
    else:
        Path('VERSION').write_text(new_version + '\n')
        run_git('add', 'VERSION')
        click.echo(click.style(f"✓ Updated VERSION to {new_version}", fg='green'))


def _handle_changelog(new_version, files, commit_msg, config, no_changelog):
    """Update changelog."""
    if not no_changelog:
        update_changelog(new_version, files, commit_msg, config=config)
        run_git('add', 'CHANGELOG.md')
        click.echo(click.style(f"✓ Updated CHANGELOG.md", fg='green'))


def _create_tag(new_version, no_tag):
    """Create git tag for release."""
    if no_tag:
        return None
    
    tag_name = f"v{new_version}"
    tag_exists = run_git('rev-parse', '-q', '--verify', f"refs/tags/{tag_name}")
    
    if tag_exists.returncode == 0:
        click.echo(click.style(f"Warning: Tag already exists: {tag_name}", fg='yellow'))
        return None
    
    result = run_git('tag', '-a', tag_name, '-m', f"Release {new_version}")
    if result.returncode != 0:
        click.echo(click.style(f"⚠ Warning: Could not create tag: {result.stderr}", fg='yellow'))
        return None
    
    click.echo(click.style(f"✓ Created tag: {tag_name}", fg='green'))
    return tag_name


def _push_to_remote(branch, tag_name, no_tag, yes):
    """Push commits and tags to remote."""
    has_remote = ensure_remote(auto=yes)
    
    if not has_remote:
        click.echo(click.style("  ℹ  No remote configured — commit saved locally.", fg='yellow'))
        return False
    
    if not yes:
        if not confirm("Push to remote?"):
            click.echo(click.style("  Skipping push (user chose N).", fg='yellow'))
            return False
    
    if not yes:
        click.echo(click.style("Pushing to remote...", fg='cyan'))
    else:
        click.echo(click.style("🤖 AUTO: Pushing to remote (--all mode)", fg='cyan'))
    
    try:
        _echo_cmd(['git', 'push', 'origin', branch])
        result = run_git('push', 'origin', branch, capture=False)
        if result.returncode != 0:
            click.echo(click.style(f"✗ Push failed (exit {result.returncode}). Check remote access.", fg='red'))
            if not yes:
                sys.exit(1)
            return False
        
        if tag_name and not no_tag:
            _echo_cmd(['git', 'push', 'origin', tag_name])
            result = run_git('push', 'origin', tag_name, capture=False)
            if result.returncode != 0:
                click.echo(click.style(f"⚠  Could not push tag {tag_name}.", fg='yellow'))
        
        click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
        return True
    except Exception as e:
        click.echo(click.style(f"✗ Push error: {e}", fg='red'))
        if not yes:
            sys.exit(1)
        return False


def _handle_publish(project_types, new_version, yes):
    """Publish to package registries."""
    if not yes:
        if not confirm(f"Publish version {new_version}?"):
            click.echo(click.style("  🤖 AUTO: Skipping publish (user chose N)", fg='yellow'))
            return False
    else:
        click.echo(click.style(f"\n🤖 AUTO: Publishing version {new_version} (--all mode)", fg='cyan'))
    
    try:
        publish_success = publish_project(project_types, new_version, yes)
        if publish_success:
            click.echo(click.style(f"\n✓ Published version {new_version}", fg='green', bold=True))
        else:
            click.echo(click.style("⚠ Publish failed. Continuing with remaining tasks.", fg='yellow'))
        return publish_success
    except Exception as e:
        click.echo(click.style(f"⚠ Publish error: {str(e)}. Continuing...", fg='yellow'))
        return False


def _output_final_summary(ctx, markdown, project_types, files, stats, current_version, 
                          new_version, commit_msg, commit_body, test_exit_code, 
                          publish_success, no_tag):
    """Output final summary in markdown format if requested."""
    if not (markdown or ctx.obj.get('markdown')):
        return
    
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


@main.command()
@click.option('--bump', default='patch', help='Version bump type (major, minor, patch)')
@click.option('--no-tag', is_flag=True, help='Skip creating git tag')
@click.option('--no-changelog', is_flag=True, help='Skip updating CHANGELOG.md')
@click.option('--no-version-sync', is_flag=True, help='Skip syncing version to all files')
@click.option('--message', '-m', default=None, help='Custom commit message')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all prompts')
@click.option('--markdown/--ascii', default=False, help='Output format')
@click.option('--split', is_flag=True, help='Split commits by file type')
@click.option('--ticket', default=None, help='Ticket ID for commit prefix')
@click.option('--abstraction', default=None, help='Abstraction level for commit message')
@click.option('--todo', '-t', is_flag=True, help='Create TODO.md with detected issues')
@click.pass_context
def push(ctx, bump, no_tag, no_changelog, no_version_sync, message, dry_run, yes, 
         markdown, split, ticket, abstraction, todo):
    """Add, commit, tag, and push changes to remote."""
    
    # Use yes from context (includes -a from main command) or local --yes flag
    yes = ctx.obj.get('yes', False) or yes
    ctx.obj['yes'] = yes
    ctx.obj['bump'] = bump
    ctx.obj['message'] = message
    ctx.obj['markdown'] = markdown or ctx.obj.get('markdown', False)
    
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
        if markdown or ctx.obj.get('markdown'):
            from ..formatter import format_push_result
            md_output = format_push_result(
                project_types=project_types or [],
                files=[],
                stats={},
                current_version=get_current_version(),
                new_version=get_current_version(),
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
    commit_title, commit_body, detailed_result = _get_commit_message(
        ctx, files, diff_content, message, ticket, abstraction
    )
    
    if not commit_title:
        click.echo(click.style("No changes to commit.", fg='yellow'))
        return
    
    commit_msg = commit_title
    
    # Get version info
    current_version = get_current_version()
    new_version = bump_version(current_version, bump)
    
    # Get diff stats
    stats = get_diff_stats()
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    
    # Enforce quality gates
    if not message and detailed_result and detailed_result.get('enhanced'):
        commit_msg = _enforce_quality_gates(
            ctx, commit_msg, detailed_result, files, total_adds, total_dels, 
            ctx.obj['yes'], markdown
        )
    
    # Handle dry run
    if dry_run:
        _handle_dry_run(ctx, project_types, files, stats, current_version, new_version,
                       commit_msg, commit_body, detailed_result, split, ticket, bump,
                       no_version_sync, no_changelog, no_tag, markdown)
        return
    
    # Interactive workflow preview
    if not ctx.obj['yes']:
        _show_workflow_preview(files, stats, current_version, new_version, 
                              commit_msg, commit_body, markdown, ctx)
    
    # Test stage
    test_result, test_exit_code = _run_test_stage(
        project_types, ctx.obj['yes'], markdown, ctx, files, stats, current_version,
        new_version, commit_msg, commit_body
    )
    
    # Commit confirmation
    if not ctx.obj['yes']:
        if not confirm("Commit changes?"):
            click.echo(click.style("  🤖 AUTO: Aborting commit (user chose N)", fg='cyan'))
            click.echo(click.style("Aborted.", fg='red'))
            sys.exit(1)
    else:
        click.echo(click.style("🤖 AUTO: Committing changes (--all mode)", fg='cyan'))
    
    # Handle split commits or single commit
    if split and not message:
        run_git('reset')  # Unstage everything
        _handle_split_commits(ctx, files, ticket, new_version, current_version, 
                             no_version_sync, no_changelog, ctx.obj['yes'])
        commit_body = None
        message = "__split__"
    else:
        # Version sync
        user_config = ctx.obj.get('user_config')
        _handle_version_sync(new_version, no_version_sync, user_config, ctx.obj['yes'])
        
        # Changelog
        config_dict = (ctx.obj.get('config') or {}).to_dict() if ctx.obj.get('config') else None
        _handle_changelog(new_version, files, commit_msg, config_dict, no_changelog)
        
        # Single commit
        _handle_single_commit(commit_title, commit_body, commit_msg, message, ctx.obj['yes'])
    
    # Create tag
    tag_name = _create_tag(new_version, no_tag)
    
    # Push to remote
    branch = get_remote_branch()
    _push_to_remote(branch, tag_name, no_tag, ctx.obj['yes'])
    
    # Publish
    publish_success = _handle_publish(project_types, new_version, ctx.obj['yes'])
    
    # Final summary
    _output_final_summary(ctx, markdown, project_types, files, stats, current_version,
                         new_version, commit_msg, commit_body, test_exit_code,
                         publish_success, no_tag)


__all__ = ['push']
