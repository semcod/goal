"""Python project diagnostics."""

import re
from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


LICENSE_CLASSIFIERS_RE = re.compile(
    r'^\s*"License\s*::\s*OSI Approved\s*::\s*[^"]*"', re.MULTILINE
)

DEPRECATED_BACKENDS = [
    'setuptools.backends._legacy',
]


def diagnose_python(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Python-specific diagnostics."""
    issues: List[Issue] = []
    pyproject = project_dir / 'pyproject.toml'
    setup_py = project_dir / 'setup.py'
    setup_cfg = project_dir / 'setup.cfg'
    requirements = project_dir / 'requirements.txt'

    # --- PY001: missing pyproject.toml ---
    if not pyproject.exists() and not setup_py.exists() and not setup_cfg.exists():
        if requirements.exists():
            issues.append(Issue(
                severity='warning', code='PY001',
                title='No pyproject.toml / setup.py / setup.cfg found',
                detail='Only requirements.txt exists. Consider adding pyproject.toml for proper packaging.',
            ))
        return issues

    if not pyproject.exists():
        return issues

    content = pyproject.read_text(errors='ignore')
    original_content = content

    # --- PY002: missing [build-system] ---
    if '[build-system]' not in content:
        detail = (
            'pyproject.toml has no [build-system] section.\n'
            'pip and build tools need this to know how to build your package.\n'
            'Adding a default setuptools build-system.'
        )
        issue = Issue(
            severity='error', code='PY002',
            title='Missing [build-system] in pyproject.toml',
            detail=detail, file='pyproject.toml',
        )
        if auto_fix:
            build_system = (
                '[build-system]\n'
                'requires = ["setuptools>=61.0", "wheel"]\n'
                'build-backend = "setuptools.build_meta"\n\n'
            )
            content = build_system + content
            issue.fixed = True
            issue.fix_description = 'Added [build-system] section with setuptools backend'
        issues.append(issue)

    # --- PY003: deprecated license classifiers (PEP 639) ---
    license_classifiers = LICENSE_CLASSIFIERS_RE.findall(content)
    if license_classifiers:
        detail = (
            'PEP 639 (adopted in newer setuptools) supersedes license classifiers\n'
            'with the license field. Newer setuptools will REFUSE to build if both\n'
            'a license expression and a License :: classifier are present.\n'
            'Found: ' + ', '.join(c.strip().strip('"').strip(',') for c in license_classifiers)
        )
        issue = Issue(
            severity='error', code='PY003',
            title='Deprecated license classifier in pyproject.toml',
            detail=detail, file='pyproject.toml',
        )
        if auto_fix:
            # Remove the license classifier lines from the classifiers list
            lines = content.splitlines(keepends=True)
            new_lines = []
            for line in lines:
                stripped = line.strip().strip(',').strip()
                if stripped.startswith('"License :: OSI Approved'):
                    continue
                if stripped.startswith("'License :: OSI Approved"):
                    continue
                new_lines.append(line)
            content = ''.join(new_lines)
            issue.fixed = True
            issue.fix_description = 'Removed deprecated License :: classifier(s) from classifiers list'
        issues.append(issue)

    # --- PY004: deprecated/broken build backend ---
    for backend in DEPRECATED_BACKENDS:
        if backend in content:
            detail = (
                f'Build backend "{backend}" is not supported by current pip/setuptools.\n'
                'Replacing with the standard "setuptools.build_meta".'
            )
            issue = Issue(
                severity='error', code='PY004',
                title=f'Broken build backend: {backend}',
                detail=detail, file='pyproject.toml',
            )
            if auto_fix:
                content = content.replace(backend, 'setuptools.build_meta')
                issue.fixed = True
                issue.fix_description = f'Replaced "{backend}" with "setuptools.build_meta"'
            issues.append(issue)

    # --- PY005: license field is a table but should be a string (PEP 639) ---
    license_table = re.search(r'^license\s*=\s*\{', content, re.MULTILINE)
    license_string = re.search(r'^license\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if license_table and not license_string:
        # Extract text from table format
        table_match = re.search(r'^license\s*=\s*\{[^}]*text\s*=\s*"([^"]+)"[^}]*\}', content, re.MULTILINE)
        if table_match:
            license_id = table_match.group(1)
            detail = (
                f'license = {{text = "{license_id}"}} is the old table format.\n'
                f'PEP 639 requires license = "{license_id}" (string expression).\n'
                'Newer setuptools may reject the table format.'
            )
            issue = Issue(
                severity='warning', code='PY005',
                title='License field uses deprecated table format',
                detail=detail, file='pyproject.toml',
            )
            if auto_fix:
                content = re.sub(
                    r'^license\s*=\s*\{[^}]*text\s*=\s*"[^"]*"[^}]*\}',
                    f'license = "{license_id}"',
                    content, flags=re.MULTILINE
                )
                issue.fixed = True
                issue.fix_description = f'Converted license to string expression: license = "{license_id}"'
            issues.append(issue)

    # --- PY006: duplicate authors ---
    authors_match = re.search(r'authors\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if authors_match:
        authors_block = authors_match.group(1)
        author_lines = [l.strip().rstrip(',') for l in authors_block.strip().splitlines() if l.strip() and not l.strip().startswith('#')]
        if len(author_lines) != len(set(author_lines)):
            detail = 'Duplicate author entries found in pyproject.toml authors list.'
            issue = Issue(
                severity='warning', code='PY006',
                title='Duplicate authors in pyproject.toml',
                detail=detail, file='pyproject.toml',
            )
            if auto_fix:
                unique = list(dict.fromkeys(author_lines))  # preserve order
                new_block = 'authors = [\n'
                for a in unique:
                    new_block += f'    {a},\n'
                new_block += ']'
                content = re.sub(r'authors\s*=\s*\[.*?\]', new_block, content, flags=re.DOTALL)
                issue.fixed = True
                issue.fix_description = f'Removed duplicate authors (kept {len(unique)} unique)'
            issues.append(issue)

    # --- PY007: missing requires-python ---
    if 'requires-python' not in content and '[project]' in content:
        detail = (
            'No requires-python specified. This helps pip and build tools\n'
            'know which Python versions your package supports.'
        )
        issue = Issue(
            severity='warning', code='PY007',
            title='Missing requires-python in pyproject.toml',
            detail=detail, file='pyproject.toml',
        )
        if auto_fix:
            # Insert after [project] line
            content = re.sub(
                r'(\[project\]\n)',
                r'\1requires-python = ">=3.8"\n',
                content, count=1
            )
            issue.fixed = True
            issue.fix_description = 'Added requires-python = ">=3.8"'
        issues.append(issue)

    # --- PY008: empty classifiers list ---
    classifiers_match = re.search(r'classifiers\s*=\s*\[\s*\]', content)
    if classifiers_match:
        issues.append(Issue(
            severity='info', code='PY008',
            title='Empty classifiers list',
            detail='Consider adding PyPI classifiers for better discoverability.',
            file='pyproject.toml',
        ))

    # --- Write fixes if content changed ---
    if content != original_content and auto_fix:
        pyproject.write_text(content, encoding='utf-8')

    return issues
