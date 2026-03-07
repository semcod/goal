"""PHP project diagnostics."""

import json
from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_php(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all PHP-specific diagnostics."""
    issues: List[Issue] = []
    composer = project_dir / 'composer.json'
    if not composer.exists():
        return issues

    try:
        data = json.loads(composer.read_text(errors='ignore'))
    except (json.JSONDecodeError, Exception):
        issues.append(Issue(
            severity='error', code='PHP001',
            title='Invalid composer.json',
            detail='JSON parse error in composer.json.',
            file='composer.json',
        ))
        return issues

    if not data.get('autoload') and not data.get('autoload-dev'):
        issues.append(Issue(
            severity='warning', code='PHP002',
            title='No autoload configuration',
            detail='Consider adding PSR-4 autoload config to composer.json.',
            file='composer.json',
        ))

    lock = project_dir / 'composer.lock'
    if not lock.exists() and data.get('require'):
        issues.append(Issue(
            severity='warning', code='PHP003',
            title='Missing composer.lock',
            detail='Run "composer install" to generate composer.lock.',
            file='composer.lock',
        ))

    return issues
