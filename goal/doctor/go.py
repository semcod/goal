"""Go project diagnostics."""

from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_go(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Go-specific diagnostics."""
    issues: List[Issue] = []
    gomod = project_dir / 'go.mod'
    if not gomod.exists():
        return issues

    content = gomod.read_text(errors='ignore')

    if not content.strip().startswith('module '):
        issues.append(Issue(
            severity='error', code='GO001',
            title='Invalid go.mod — missing module declaration',
            detail='go.mod must start with "module <path>".',
            file='go.mod',
        ))

    gosum = project_dir / 'go.sum'
    if not gosum.exists() and 'require' in content:
        issues.append(Issue(
            severity='warning', code='GO002',
            title='Missing go.sum',
            detail='go.sum is missing but go.mod has dependencies. Run "go mod tidy".',
            file='go.sum',
        ))

    return issues
