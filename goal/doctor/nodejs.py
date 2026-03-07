"""Node.js project diagnostics."""

import json
from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_nodejs(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Node.js-specific diagnostics."""
    issues: List[Issue] = []
    pkg_json = project_dir / 'package.json'
    if not pkg_json.exists():
        return issues

    try:
        data = json.loads(pkg_json.read_text(errors='ignore'))
    except (json.JSONDecodeError, Exception) as e:
        issues.append(Issue(
            severity='error', code='JS001',
            title='Invalid package.json',
            detail=f'JSON parse error: {e}',
            file='package.json',
        ))
        return issues

    original_data = json.dumps(data, indent=2)

    # --- JS002: missing name ---
    if not data.get('name'):
        issues.append(Issue(
            severity='error', code='JS002',
            title='Missing "name" in package.json',
            detail='Every npm package needs a name field.',
            file='package.json',
        ))

    # --- JS003: missing version ---
    if not data.get('version'):
        detail = 'No "version" field in package.json. Adding "0.1.0".'
        issue = Issue(
            severity='warning', code='JS003',
            title='Missing "version" in package.json',
            detail=detail, file='package.json',
        )
        if auto_fix:
            data['version'] = '0.1.0'
            issue.fixed = True
            issue.fix_description = 'Added version = "0.1.0"'
        issues.append(issue)

    # --- JS004: missing test script ---
    scripts = data.get('scripts', {})
    if 'test' not in scripts or 'no test specified' in scripts.get('test', ''):
        issues.append(Issue(
            severity='warning', code='JS004',
            title='No test script configured',
            detail='package.json has no usable "test" script. Consider adding jest or mocha.',
            file='package.json',
        ))

    # --- JS005: missing main/module entry ---
    if not data.get('main') and not data.get('module') and not data.get('exports'):
        issues.append(Issue(
            severity='info', code='JS005',
            title='No entry point (main/module/exports)',
            detail='Consider adding a "main" or "exports" field for proper module resolution.',
            file='package.json',
        ))

    # Write fixes
    new_data = json.dumps(data, indent=2)
    if new_data != original_data and auto_fix:
        pkg_json.write_text(new_data + '\n', encoding='utf-8')

    return issues
