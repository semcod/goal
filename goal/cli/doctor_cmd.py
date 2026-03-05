"""Doctor command - extracted from cli.py."""

import click
from pathlib import Path
from datetime import datetime

try:
    from ..project_bootstrap import detect_project_types_deep, bootstrap_all_projects
    from ..project_doctor import diagnose_and_report_with_todo, DoctorReport
    from . import main
except ImportError:
    from goal.project_bootstrap import detect_project_types_deep, bootstrap_all_projects
    from goal.project_doctor import diagnose_and_report_with_todo, DoctorReport
    from goal.cli import main


@main.command()
@click.option('--fix', is_flag=True, help='Auto-fix detected issues')
@click.option('--path', default='.', help='Project path to diagnose')
@click.option('--todo', is_flag=True, help='Add issues to TODO.md')
@click.pass_context
def doctor(ctx, fix, path, todo):
    """Diagnose and auto-fix common project configuration issues."""
    project_path = Path(path).resolve()
    
    # Ensure TODO.md exists
    todo_file = project_path / 'TODO.md'
    if not todo_file.exists():
        todo_content = """# TODO

## 🎯 Active Tasks

### High Priority
- [ ] Add your high priority tasks here

### Medium Priority
- [ ] Add your medium priority tasks here

### Low Priority
- [ ] Add your low priority tasks here

## 🐛 Issues Found

<!-- Issues will be automatically added here when using goal -t -->

## 📝 Notes

- This TODO list is managed by Goal
- Use `goal -t` to add detected issues automatically
- Use `goal doctor --todo` to diagnose and track issues

Last updated: """ + datetime.now().strftime('%Y-%m-%d')
        todo_file.write_text(todo_content)
        click.echo(click.style("✓ TODO.md file created", fg='green'))
    
    # Ensure CHANGELOG.md exists
    changelog_file = project_path / 'CHANGELOG.md'
    if not changelog_file.exists():
        changelog_content = """# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

### Changed

### Fixed

### Removed

---

Last updated: """ + datetime.now().strftime('%Y-%m-%d')
        changelog_file.write_text(changelog_content)
        click.echo(click.style("✓ CHANGELOG.md file created", fg='green'))
    
    detected = detect_project_types_deep(project_path)
    if detected:
        all_reports = []
        for ptype, dirs in detected.items():
            for project_dir in dirs:
                report = diagnose_and_report_with_todo(project_dir, ptype, auto_fix=fix, todo_file=todo_file if todo else None)
                all_reports.append(report)
        
        total_issues = sum(len(r.issues) for r in all_reports)
        total_fixed = sum(len(r.fixed) for r in all_reports)
        
        if total_issues > 0 or total_fixed > 0:
            click.echo(click.style("\n" + "=" * 60, fg='cyan'))
            if total_issues == 0:
                click.echo(click.style("✓ All projects are healthy!", fg='green', bold=True))
            else:
                click.echo(click.style(f"🩺 Doctor summary: {total_issues} issue(s) found", fg='cyan', bold=True))
    else:
        click.echo(click.style("No known project types detected for diagnostics.", fg='yellow'))


__all__ = ['doctor']
