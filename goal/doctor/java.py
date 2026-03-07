"""Java project diagnostics."""

from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_java(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Java-specific diagnostics."""
    issues: List[Issue] = []
    pom = project_dir / 'pom.xml'
    gradle = project_dir / 'build.gradle'
    gradle_kts = project_dir / 'build.gradle.kts'

    if pom.exists():
        content = pom.read_text(errors='ignore')
        if '<modelVersion>' not in content:
            issues.append(Issue(
                severity='warning', code='JV001',
                title='Missing <modelVersion> in pom.xml',
                detail='pom.xml should have <modelVersion>4.0.0</modelVersion>.',
                file='pom.xml',
            ))

    if not pom.exists() and not gradle.exists() and not gradle_kts.exists():
        issues.append(Issue(
            severity='info', code='JV002',
            title='No build file found',
            detail='No pom.xml or build.gradle found.',
        ))

    return issues
