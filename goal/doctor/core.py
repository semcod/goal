"""Core diagnostic dispatcher and main functions."""

from pathlib import Path
from typing import Dict, List, Callable

import click

try:
    from ..doctor.models import Issue, DoctorReport
    from ..doctor.logging import _log_issue, _log_fix
except ImportError:
    from goal.doctor.models import Issue, DoctorReport
    from goal.doctor.logging import _log_issue, _log_fix

# Import language-specific diagnostics
try:
    from .python import diagnose_python
    from .nodejs import diagnose_nodejs
    from .rust import diagnose_rust
    from .go import diagnose_go
    from .ruby import diagnose_ruby
    from .php import diagnose_php
    from .dotnet import diagnose_dotnet
    from .java import diagnose_java
except ImportError:
    from goal.doctor.python import diagnose_python
    from goal.doctor.nodejs import diagnose_nodejs
    from goal.doctor.rust import diagnose_rust
    from goal.doctor.go import diagnose_go
    from goal.doctor.ruby import diagnose_ruby
    from goal.doctor.php import diagnose_php
    from goal.doctor.dotnet import diagnose_dotnet
    from goal.doctor.java import diagnose_java


# Dispatcher mapping project types to diagnostic functions
_DIAGNOSTICS: Dict[str, Callable[[Path, bool], List[Issue]]] = {
    'python': diagnose_python,
    'nodejs': diagnose_nodejs,
    'rust':   diagnose_rust,
    'go':     diagnose_go,
    'ruby':   diagnose_ruby,
    'php':    diagnose_php,
    'dotnet': diagnose_dotnet,
    'java':   diagnose_java,
}


def diagnose_project(project_dir: Path, project_type: str,
                     auto_fix: bool = True) -> DoctorReport:
    """Run diagnostics for a single project directory.

    Args:
        project_dir: Path to the project root.
        project_type: One of the known project type keys.
        auto_fix: If True, automatically fix issues where possible.

    Returns:
        A DoctorReport with all found (and optionally fixed) issues.
    """
    report = DoctorReport(project_dir=project_dir.resolve(), project_type=project_type)
    diag_fn = _DIAGNOSTICS.get(project_type)
    if diag_fn:
        report.issues = diag_fn(project_dir, auto_fix=auto_fix)
    return report


def diagnose_and_report(project_dir: Path, project_type: str,
                        auto_fix: bool = True) -> DoctorReport:
    """Diagnose, fix, and print a human-readable report."""
    try:
        rel = project_dir.relative_to(Path('.').resolve())
    except ValueError:
        rel = project_dir

    click.echo(click.style(f"\n🩺 Diagnosing {project_type} project in {rel}", fg='cyan', bold=True))
    report = diagnose_project(project_dir, project_type, auto_fix=auto_fix)

    if not report.issues:
        click.echo(click.style("  ✓ No issues found", fg='green'))
        return report

    for issue in report.issues:
        _log_issue(issue)
        if issue.fixed:
            _log_fix(issue)

    # Summary line
    n_err = len(report.errors)
    n_warn = len(report.warnings)
    n_fixed = len(report.fixed)
    parts = []
    if n_err:
        parts.append(click.style(f"{n_err} error(s)", fg='red'))
    if n_warn:
        parts.append(click.style(f"{n_warn} warning(s)", fg='yellow'))
    if n_fixed:
        parts.append(click.style(f"{n_fixed} auto-fixed", fg='green'))
    click.echo("  " + ", ".join(parts))

    return report
