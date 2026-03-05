"""Commit command - extracted from cli.py."""

import click
import sys

try:
    from ..commit_generator import CommitMessageGenerator
    from ..git_ops import get_staged_files, get_diff_content, get_diff_stats
    from ..enhanced_summary import EnhancedSummaryGenerator
    from ..formatter import format_enhanced_summary
    from . import main, apply_ticket_prefix
except ImportError:
    from goal.commit_generator import CommitMessageGenerator
    from goal.git_ops import get_staged_files, get_diff_content, get_diff_stats
    from goal.enhanced_summary import EnhancedSummaryGenerator
    from goal.formatter import format_enhanced_summary
    from goal.cli import main, apply_ticket_prefix


@main.command()
@click.option('--detailed', is_flag=True, help='Generate detailed commit message with body')
@click.option('--unstaged', is_flag=True, help='Include unstaged changes')
@click.option('--markdown/--ascii', default=False, help='Output format')
@click.option('--ticket', default=None, help='Ticket ID for commit prefix')
@click.option('--abstraction', default=None, help='Abstraction level for commit message')
@click.pass_context
def commit(ctx, detailed, unstaged, markdown, ticket, abstraction):
    """Generate a smart commit message for current changes."""
    files = get_staged_files()
    
    if not files or files == ['']:
        click.echo(click.style("No staged changes. Stage files first with 'git add'.", fg='yellow'))
        return
    
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else None
    
    generator = CommitMessageGenerator(config=config_dict)
    
    if detailed:
        result = generator.generate_detailed_message(cached=not unstaged)
        if result:
            title = apply_ticket_prefix(result.get('title'), ticket)
            body = result.get('body', '')
            
            if markdown or ctx.obj.get('markdown'):
                click.echo(f"## Commit Message\n\n**{title}**\n\n{body}")
            else:
                click.echo(click.style("Generated commit message:", fg='cyan', bold=True))
                click.echo(f"\n{click.style(title, fg='green', bold=True)}")
                if body:
                    click.echo(f"\n{body}")
        else:
            click.echo(click.style("Could not generate detailed message.", fg='yellow'))
    else:
        # Simple commit message
        message = generator.generate_commit_message(cached=not unstaged)
        title = apply_ticket_prefix(message, ticket)
        
        if markdown or ctx.obj.get('markdown'):
            click.echo(f"## Commit Message\n\n**{title}**")
        else:
            click.echo(click.style("Generated commit message:", fg='cyan'))
            click.echo(click.style(title, fg='green'))


@main.command()
@click.option('--fix', is_flag=True, help='Auto-fix issues')
@click.option('--preview', is_flag=True, help='Show preview only')
@click.option('--cached', is_flag=True, default=True, help='Use cached/staged changes')
@click.pass_context
def fix_summary(ctx, fix, preview, cached):
    """Auto-fix commit summary quality issues."""
    from ..enhanced_summary import QualityValidator
    
    files = get_staged_files()
    stats = get_diff_stats()
    
    if not files:
        click.echo(click.style("No changes to analyze.", fg='yellow'))
        return
    
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else {}
    
    generator = CommitMessageGenerator(config=config_dict)
    detailed = generator.generate_detailed_message(cached=cached)
    
    if not detailed:
        click.echo(click.style("Could not generate summary.", fg='yellow'))
        return
    
    validator = QualityValidator(config_dict)
    
    summary = {
        'title': detailed.get('title', ''),
        'body': detailed.get('body', ''),
        'intent': detailed.get('intent', ''),
        'metrics': {
            'lines_added': sum(s[0] for s in stats.values()),
            'lines_deleted': sum(s[1] for s in stats.values()),
        }
    }
    
    validation = validator.validate(summary, files)
    
    if validation.get('valid', True):
        click.echo(click.style("✓ Summary passes quality gates", fg='green'))
        return
    
    if preview or not fix:
        click.echo(click.style("Quality issues found:", fg='yellow', bold=True))
        for error in validation.get('errors', []):
            click.echo(f"  ✗ {error}")
        
        fixed = validator.auto_fix(summary, files)
        if fixed:
            click.echo(f"\nSuggested title: {click.style(fixed.get('title', ''), fg='cyan')}")
    else:
        # Apply fixes
        fixed = validator.auto_fix(summary, files)
        if fixed:
            click.echo(click.style(f"✓ Fixed: {fixed.get('title', '')}", fg='green'))


@main.command()
@click.option('--fix', is_flag=True, help='Auto-fix issues')
@click.option('--cached', is_flag=True, default=True, help='Use cached/staged changes')
@click.pass_context
def validate(ctx, fix, cached):
    """Validate commit summary against quality gates."""
    from ..enhanced_summary import QualityValidator
    
    files = get_staged_files()
    stats = get_diff_stats()
    
    if not files:
        click.echo(click.style("No changes to validate.", fg='yellow'))
        return
    
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else {}
    
    generator = CommitMessageGenerator(config=config_dict)
    detailed = generator.generate_detailed_message(cached=cached)
    
    if not detailed:
        click.echo(click.style("Could not generate summary.", fg='yellow'))
        return
    
    validator = QualityValidator(config_dict)
    
    summary = {
        'title': detailed.get('title', ''),
        'body': detailed.get('body', ''),
        'intent': detailed.get('intent', ''),
        'metrics': {
            'lines_added': sum(s[0] for s in stats.values()),
            'lines_deleted': sum(s[1] for s in stats.values()),
        }
    }
    
    validation = validator.validate(summary, files)
    score = validation.get('score', 0)
    
    click.echo(click.style(f"Quality Score: {score}/100", fg='cyan', bold=True))
    
    if validation.get('errors'):
        click.echo(click.style("\nErrors:", fg='red'))
        for error in validation.get('errors'):
            click.echo(f"  ✗ {error}")
    
    if validation.get('warnings'):
        click.echo(click.style("\nWarnings:", fg='yellow'))
        for warning in validation.get('warnings'):
            click.echo(f"  ⚠ {warning}")
    
    if validation.get('valid', True):
        click.echo(click.style("\n✓ Validation passed", fg='green'))
    else:
        click.echo(click.style("\n✗ Validation failed", fg='red'))
        if fix:
            fixed = validator.auto_fix(summary, files)
            if fixed:
                click.echo(click.style(f"\n✓ Fixed title: {fixed.get('title', '')}", fg='green'))
        else:
            click.echo("\nRun with --fix to auto-correct issues")


__all__ = [
    'commit',
    'fix_summary',
    'validate',
]
