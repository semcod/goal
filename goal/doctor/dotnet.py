""".NET project diagnostics."""

from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_dotnet(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all .NET-specific diagnostics."""
    issues: List[Issue] = []
    csproj_files = list(project_dir.glob('*.csproj')) + list(project_dir.glob('*.fsproj'))
    if not csproj_files:
        return issues

    for csproj in csproj_files:
        content = csproj.read_text(errors='ignore')
        if '<TargetFramework' not in content:
            issues.append(Issue(
                severity='warning', code='NET001',
                title=f'No TargetFramework in {csproj.name}',
                detail='Consider specifying <TargetFramework>net8.0</TargetFramework>.',
                file=csproj.name,
            ))

    return issues
