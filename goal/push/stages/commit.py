"""Push workflow stages - commit handling."""

import sys
from typing import Dict, List, Optional, Tuple, Any

import click

from goal.git_ops import run_git, apply_ticket_prefix, get_staged_files
from goal.commit_generator import CommitMessageGenerator
from goal.enhanced_summary import QualityValidator
from goal.cli import split_paths_by_type, stage_paths, confirm


def get_commit_message(
    ctx_obj: Dict[str, Any],
    files: List[str],
    diff_content: str,
    message: Optional[str],
    ticket: Optional[str],
    abstraction: Optional[str]
) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
    """Generate or use provided commit message."""
    if message:
        return apply_ticket_prefix(message, ticket), None, None
    
    config_obj = ctx_obj.get('config')
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


def _build_validation_summary(commit_msg: str, detailed_result: Dict, total_adds: int, total_dels: int) -> Dict[str, Any]:
    return {
        'title': commit_msg,
        'intent': detailed_result.get('intent'),
        'metrics': {
            'lines_added': total_adds,
            'lines_deleted': total_dels,
        }
    }


def _confirm_suggested_title(commit_msg: str, suggested_title: str, yes: bool) -> bool:
    if not suggested_title or suggested_title == commit_msg:
        return False
    if yes:
        return True
    return confirm(f"Apply suggested title?\n\nCurrent: {commit_msg}\nSuggested: {suggested_title}")


def _echo_applied_title_fix(ctx_obj: Dict[str, Any], commit_msg: str, markdown: bool) -> None:
    if markdown or ctx_obj.get('markdown'):
        click.echo(f"\n- **Applied title fix:** `{commit_msg}`")
    else:
        click.echo(click.style(f"\n✓ Applied title fix: {commit_msg}", fg='green'))


def enforce_quality_gates(
    ctx_obj: Dict[str, Any],
    commit_msg: str,
    detailed_result: Dict,
    files: List[str],
    total_adds: int,
    total_dels: int,
    yes: bool,
    markdown: bool
) -> str:
    """Enforce commit quality gates for auto-generated messages."""
    config_obj = ctx_obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else {}
    quality_cfg = (config_dict or {}).get('quality', {}).get('enhanced_summary', {})
    
    if not quality_cfg.get('enabled', True):
        return commit_msg
    
    try:
        validator = QualityValidator(config_dict or {})
        summary = _build_validation_summary(commit_msg, detailed_result, total_adds, total_dels)
        validation = validator.validate(summary, detailed_result.get('files') or files)
        
        if validation.get('valid', True):
            return commit_msg
        
        suggested = validator.auto_fix(summary, files, total_adds, total_dels)
        suggested_title = (suggested or {}).get('title', '')
        
        if _confirm_suggested_title(commit_msg, suggested_title, yes):
            commit_msg = suggested_title
            _echo_applied_title_fix(ctx_obj, commit_msg, markdown)
        
        return commit_msg
    except Exception:
        return commit_msg


def handle_single_commit(
    commit_title: str,
    commit_body: Optional[str],
    commit_msg: str,
    message: Optional[str],
    yes: bool
) -> bool:
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


_GROUP_ORDER = ['code', 'docs', 'ci', 'examples', 'other']


def _commit_file_group(gname: str, paths: List[str], generator: CommitMessageGenerator,
                       ticket: Optional[str], yes: bool) -> None:
    """Stage and commit a single file group."""
    stage_paths(paths)
    if not get_staged_files():
        click.echo(click.style(f"  ℹ Skipping {gname}: no changes to commit", fg='yellow'))
        return
    d = generator.generate_detailed_message(cached=True, paths=paths)
    if not d:
        return
    title = apply_ticket_prefix(d.get('title'), ticket)
    result = run_git('commit', '-m', title, '-m', d.get('body'))
    if result.returncode != 0:
        click.echo(click.style(f"✗ Error committing split group {gname}: {result.stderr}", fg='red'))
        if not yes:
            sys.exit(1)
    else:
        click.echo(click.style(f"✓ Committed ({gname}): {title}", fg='green'))


def _commit_release_metadata(
    ctx_obj: Dict[str, Any], files: List[str], config_dict, ticket: Optional[str],
    new_version: str, current_version: str, no_version_sync: bool, no_changelog: bool
) -> None:
    """Sync versions, update changelog, update cost badges, and commit release metadata."""
    from ..core import _update_cost_badges

    if not no_version_sync:
        from .version import sync_all_versions_wrapper
        stage_paths(sync_all_versions_wrapper(new_version, ctx_obj.get('user_config')))
    else:
        from pathlib import Path
        Path('VERSION').write_text(f"{new_version}\n")
        stage_paths(['VERSION'])

    if not no_changelog:
        from ...changelog import update_changelog
        update_changelog(new_version, files, f"chore(release): bump version to {new_version}", config=config_dict)
        stage_paths(['CHANGELOG.md'])

    if _update_cost_badges(ctx_obj, new_version):
        run_git('add', 'README.md')

    release_title = apply_ticket_prefix(f"chore(release): bump version to {new_version}", ticket)
    release_body = f"Release metadata\n\nVersion: {current_version} -> {new_version}"
    result = run_git('commit', '-m', release_title, '-m', release_body)
    if result.returncode != 0:
        click.echo(click.style(f"Error committing release metadata: {result.stderr}", fg='red'))
    else:
        click.echo(click.style(f"✓ Committed (release): {release_title}", fg='green'))


def handle_split_commits(
    ctx_obj: Dict[str, Any],
    files: List[str],
    ticket: Optional[str],
    new_version: str,
    current_version: str,
    no_version_sync: bool,
    no_changelog: bool,
    yes: bool
) -> None:
    """Handle split commits per file group."""
    config_dict = (ctx_obj.get('config') or {}).to_dict() if ctx_obj.get('config') else None
    generator = CommitMessageGenerator(config=config_dict)
    groups = split_paths_by_type(files)

    if not yes:
        click.echo(click.style("\nSplit commits plan:", fg='cyan', bold=True))
        for gname in _GROUP_ORDER:
            if gname in groups:
                d = generator.generate_detailed_message(cached=False, paths=groups[gname])
                title = apply_ticket_prefix(d.get('title'), ticket) if d else gname
                click.echo(f"- {gname}: {title} ({len(groups[gname])} files)")

    for gname in _GROUP_ORDER:
        if gname in groups:
            _commit_file_group(gname, groups[gname], generator, ticket, yes)

    from ..core import _update_cost_badges
    if (not no_version_sync) or (not no_changelog):
        _commit_release_metadata(
            ctx_obj, files, config_dict, ticket,
            new_version, current_version, no_version_sync, no_changelog
        )
    else:
        if _update_cost_badges(ctx_obj, new_version):
            run_git('add', 'README.md')
            if get_staged_files():
                msg = f'chore: update AI cost badges for v{new_version}'
                result = run_git('commit', '-m', msg)
                if result.returncode != 0:
                    click.echo(click.style(f"Error committing badge update: {result.stderr}", fg='red'))
                else:
                    click.echo(click.style(f"✓ Committed (badges): {msg}", fg='green'))
