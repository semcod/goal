"""Validation command for managing custom validation rules."""

import click
from pathlib import Path

from goal.cli import main
from goal.validation import ValidationRuleManager, run_custom_validations


@main.group()
def validation():
    """Manage custom validation rules."""
    pass


@validation.command(name='run')
def validation_run():
    """Run custom validation rules."""
    manager = ValidationRuleManager()
    if manager.validate_all():
        click.echo()
        click.echo(click.style("✓ All validation rules passed", fg='green'))
    else:
        click.echo()
        click.echo(click.style("✗ Some validation rules failed", fg='red'))


@validation.command(name='list')
def validation_list():
    """List configured validation rules."""
    manager = ValidationRuleManager()
    manager.list_rules()


@validation.command(name='validate')
def validation_validate():
    """Validate rule configurations."""
    manager = ValidationRuleManager()
    click.echo()
    click.echo(click.style("Validating rule configurations...", fg='cyan'))
    if manager.validate_config():
        click.echo()
        click.echo(click.style("✓ All rule configurations are valid", fg='green'))
    else:
        click.echo()
        click.echo(click.style("✗ Some rule configurations have errors", fg='red'))


@validation.command(name='info')
def validation_info():
    """Show information about available validation rules."""
    from goal.validation import AVAILABLE_RULES
    
    click.echo()
    click.echo(click.style("Available Validation Rules:", fg='cyan', bold=True))
    click.echo("-" * 40)
    
    for name, rule_class in AVAILABLE_RULES.items():
        rule = rule_class({})
        click.echo()
        click.echo(click.style(f"• {name}", fg='green'))
        
        if name == 'message_pattern':
            click.echo("  Validate commit message against regex pattern")
            click.echo("  Config: pattern (required), error_message (optional)")
        elif name == 'file_pattern':
            click.echo("  Validate staged files match/don't match patterns")
            click.echo("  Config: pattern (required), min_count, max_count, forbidden")
        elif name == 'script':
            click.echo("  Run custom validation script")
            click.echo("  Config: command (required), working_dir, timeout")
        elif name == 'commit_size':
            click.echo("  Validate commit size (lines/files)")
            click.echo("  Config: max_lines, max_files, min_files")
        elif name == 'message_length':
            click.echo("  Validate commit message length")
            click.echo("  Config: min_length, max_length, max_title_length")


__all__ = [
    'validation',
    'validation_run',
    'validation_list',
    'validation_validate',
    'validation_info',
]
