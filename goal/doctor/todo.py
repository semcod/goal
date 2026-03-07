"""TODO.md management for doctor diagnostics."""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Set

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def _generate_ticket_id(issue: Issue) -> str:
    """Generate unique ticket ID from issue code and title."""
    # Use code + first 50 chars of title (normalized) as unique identifier
    title_normalized = re.sub(r'[^a-zA-Z0-9]', '', issue.title.lower())[:50]
    return f"{issue.code}-{title_normalized}"


def _read_existing_tickets(todo_file: Path) -> Set[str]:
    """Read existing ticket IDs from TODO.md."""
    if not todo_file.exists():
        return set()
    
    content = todo_file.read_text(encoding='utf-8')
    tickets = set()
    
    # Look for ticket IDs in format: - [PY001-...] Issue title
    for line in content.splitlines():
        match = re.match(r'^-\s*\[([A-Z]+\d+-[a-zA-Z0-9]+)\]', line)
        if match:
            tickets.add(match.group(1))
    
    return tickets


def _format_todo_entry(issue: Issue) -> str:
    """Format issue as TODO.md entry."""
    ticket_id = _generate_ticket_id(issue)
    severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity, "⚪")
    
    entry = f"- [{ticket_id}] {severity_icon} **{issue.title}**"
    
    if issue.file:
        entry += f" (`{issue.file}`)"
    
    entry += f"\n  - {issue.detail}"
    
    if issue.fixed:
        entry += f"\n  - ✅ **Fixed**: {issue.fix_description}"
    
    return entry


def add_issues_to_todo(project_dir: Path, issues: List[Issue], todo_file: str = "TODO.md") -> int:
    """Add issues to TODO.md without duplicates.
    
    Args:
        project_dir: Project directory path
        issues: List of issues to add
        todo_file: Name of TODO file (default: TODO.md)
        
    Returns:
        Number of new issues added
    """
    import click
    
    if not issues:
        return 0
    
    todo_path = project_dir / todo_file
    existing_tickets = _read_existing_tickets(todo_path)
    
    # Filter only unfixed issues and generate new entries
    new_entries = []
    added_count = 0
    
    for issue in issues:
        if issue.fixed:
            continue  # Skip fixed issues
            
        ticket_id = _generate_ticket_id(issue)
        if ticket_id not in existing_tickets:
            new_entries.append(_format_todo_entry(issue))
            existing_tickets.add(ticket_id)  # Mark as added to avoid duplicates in this run
            added_count += 1
    
    if not new_entries:
        return 0
    
    # Prepare content
    timestamp = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=short'], 
                              capture_output=True, text=True, cwd=project_dir).stdout.strip()
    if not timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d')
    
    header = f"\n## Issues Found - {timestamp}\n\n"
    content = header + "\n\n".join(new_entries) + "\n"
    
    # Write to TODO.md
    if todo_path.exists():
        existing_content = todo_path.read_text(encoding='utf-8')
        # Insert before the last section or at the end
        if existing_content.strip():
            todo_path.write_text(existing_content.rstrip() + content, encoding='utf-8')
        else:
            todo_path.write_text(f"# TODO\n\n{content}", encoding='utf-8')
    else:
        todo_path.write_text(f"# TODO\n\n{content}", encoding='utf-8')
    
    click.echo(click.style(f"  📝 Added {added_count} new issue(s) to {todo_file}", fg='cyan'))
    return added_count


def diagnose_and_report_with_todo(project_dir: Path, project_type: str,
                                 auto_fix: bool = True, todo_file: str = "TODO.md") -> 'DoctorReport':
    """Diagnose, fix, report, and optionally add issues to TODO.md."""
    from .core import diagnose_and_report
    
    report = diagnose_and_report(project_dir, project_type, auto_fix)
    
    # Add unfixed issues to TODO.md
    if report.issues and todo_file is not None:
        unfixed_issues = [i for i in report.issues if not i.fixed]
        if unfixed_issues:
            add_issues_to_todo(project_dir, unfixed_issues, todo_file)
    
    return report
