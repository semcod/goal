"""Ruby project diagnostics."""

from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_ruby(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Ruby-specific diagnostics."""
    issues: List[Issue] = []
    gemfile = project_dir / 'Gemfile'
    if not gemfile.exists():
        return issues

    lock = project_dir / 'Gemfile.lock'
    if not lock.exists():
        issues.append(Issue(
            severity='warning', code='RB001',
            title='Missing Gemfile.lock',
            detail='Run "bundle install" to generate Gemfile.lock for reproducible builds.',
            file='Gemfile.lock',
        ))

    return issues
