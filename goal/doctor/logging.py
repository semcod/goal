"""Logging helpers for doctor diagnostics."""

import click
from .models import Issue


_SEVERITY_STYLE = {
    'error':   ('✗', 'red'),
    'warning': ('⚠', 'yellow'),
    'info':    ('ℹ', 'cyan'),
}


def _log_issue(issue: Issue):
    icon, color = _SEVERITY_STYLE.get(issue.severity, ('•', 'white'))
    tag = click.style(f"[{issue.code}]", fg='bright_black')
    msg = click.style(f"{icon} {issue.title}", fg=color, bold=issue.severity == 'error')
    click.echo(f"  {tag} {msg}")
    if issue.detail:
        for line in issue.detail.strip().splitlines():
            click.echo(click.style(f"       {line}", fg='bright_black'))


def _log_fix(issue: Issue):
    click.echo(click.style(f"  ✓ FIXED [{issue.code}]: {issue.fix_description}", fg='green'))
