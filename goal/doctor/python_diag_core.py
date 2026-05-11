"""Python project diagnostics — core checks (PY002–PY009)."""

import re
from pathlib import Path
from typing import List, Optional

from goal.doctor.models import Issue


LICENSE_CLASSIFIERS_RE = re.compile(
    r'^\s*"License\s*::\s*OSI Approved\s*::\s*[^"]*"', re.MULTILINE
)

DEPRECATED_BACKENDS = [
    'setuptools.backends._legacy',
]


class PythonDiagnosticsCore:
    """Container for Python diagnostic checks with shared state."""

    def __init__(self, project_dir: Path, content: str, auto_fix: bool):
        self.project_dir = project_dir
        self.content = content
        self.original_content = content
        self.auto_fix = auto_fix
        self.issues: List[Issue] = []
    
    def check_py001_missing_config(self, pyproject: Path, setup_py: Path, 
                                    setup_cfg: Path, requirements: Path) -> None:
        """PY001: Check for missing pyproject.toml / setup.py / setup.cfg."""
        if not pyproject.exists() and not setup_py.exists() and not setup_cfg.exists():
            if requirements.exists():
                self.issues.append(Issue(
                    severity='warning', code='PY001',
                    title='No pyproject.toml / setup.py / setup.cfg found',
                    detail='Only requirements.txt exists. Consider adding pyproject.toml for proper packaging.',
                ))
    
    def check_py002_build_system(self) -> None:
        """PY002: Check for missing [build-system] section."""
        if '[build-system]' in self.content:
            return
        
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
        if self.auto_fix:
            build_system = (
                '[build-system]\n'
                'requires = ["setuptools>=61.0", "wheel"]\n'
                'build-backend = "setuptools.build_meta"\n\n'
            )
            self.content = build_system + self.content
            issue.fixed = True
            issue.fix_description = 'Added [build-system] section with setuptools backend'
        self.issues.append(issue)
    
    def check_py003_license_classifiers(self) -> None:
        """PY003: Check for deprecated license classifiers."""
        license_classifiers = LICENSE_CLASSIFIERS_RE.findall(self.content)
        if not license_classifiers:
            return
        
        detail = (
            'PEP 639 (adopted in newer setuptools) supersedes license classifiers\n'
            'with the license field. Newer setuptools will REFUSE to build if both\n'
            'a license expression and a License :: classifier are present.\n'
            "Found: " + ', '.join(c.strip().strip('"').strip(',') for c in license_classifiers)
        )
        issue = Issue(
            severity='error', code='PY003',
            title='Deprecated license classifier in pyproject.toml',
            detail=detail, file='pyproject.toml',
        )
        if self.auto_fix:
            lines = self.content.splitlines(keepends=True)
            new_lines = []
            for line in lines:
                stripped = line.strip().strip(',').strip()
                if stripped.startswith('"License :: OSI Approved'):
                    continue
                if stripped.startswith("'License :: OSI Approved"):
                    continue
                new_lines.append(line)
            self.content = ''.join(new_lines)
            issue.fixed = True
            issue.fix_description = 'Removed deprecated License :: classifier(s) from classifiers list'
        self.issues.append(issue)
    
    def check_py004_deprecated_backends(self) -> None:
        """PY004: Check for deprecated/broken build backends."""
        for backend in DEPRECATED_BACKENDS:
            if backend not in self.content:
                continue
            
            detail = (
                f'Build backend "{backend}" is not supported by current pip/setuptools.\n'
                'Replacing with the standard "setuptools.build_meta".'
            )
            issue = Issue(
                severity='error', code='PY004',
                title=f'Broken build backend: {backend}',
                detail=detail, file='pyproject.toml',
            )
            if self.auto_fix:
                self.content = self.content.replace(backend, 'setuptools.build_meta')
                issue.fixed = True
                issue.fix_description = f'Replaced "{backend}" with "setuptools.build_meta"'
            self.issues.append(issue)
    
    def check_py005_license_table(self) -> None:
        """PY005: Check for license field as table instead of string."""
        license_table = re.search(r'^license\s*=\s*\{', self.content, re.MULTILINE)
        license_string = re.search(r'^license\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        
        if not license_table or license_string:
            return
        
        table_match = re.search(
            r'^license\s*=\s*\{[^}]*text\s*=\s*"([^"]+)"[^}]*\}', 
            self.content, re.MULTILINE
        )
        if not table_match:
            return
        
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
        if self.auto_fix:
            self.content = re.sub(
                r'^license\s*=\s*\{[^}]*text\s*=\s*"[^"]*"[^}]*\}',
                f'license = "{license_id}"',
                self.content, flags=re.MULTILINE
            )
            issue.fixed = True
            issue.fix_description = f'Converted license to string expression: license = "{license_id}"'
        self.issues.append(issue)
    
    def check_py006_duplicate_authors(self) -> None:
        """PY006: Check for duplicate authors."""
        authors_match = re.search(r'authors\s*=\s*\[(.*?)\]', self.content, re.DOTALL)
        if not authors_match:
            return
        
        authors_block = authors_match.group(1)
        author_lines = [l.strip().rstrip(',') for l in authors_block.strip().splitlines() 
                       if l.strip() and not l.strip().startswith('#')]
        
        if len(author_lines) == len(set(author_lines)):
            return
        
        detail = 'Duplicate author entries found in pyproject.toml authors list.'
        issue = Issue(
            severity='warning', code='PY006',
            title='Duplicate authors in pyproject.toml',
            detail=detail, file='pyproject.toml',
        )
        if self.auto_fix:
            unique = list(dict.fromkeys(author_lines))
            new_block = 'authors = [\n'
            for a in unique:
                new_block += f'    {a},\n'
            new_block += ']'
            self.content = re.sub(r'authors\s*=\s*\[.*?\]', new_block, self.content, flags=re.DOTALL)
            issue.fixed = True
            issue.fix_description = f'Removed duplicate authors (kept {len(unique)} unique)'
        self.issues.append(issue)
    
    def check_py007_requires_python(self) -> None:
        """PY007: Check for missing requires-python."""
        if 'requires-python' in self.content or '[project]' not in self.content:
            return
        
        detail = (
            'No requires-python specified. This helps pip and build tools\n'
            'know which Python versions your package supports.'
        )
        issue = Issue(
            severity='warning', code='PY007',
            title='Missing requires-python in pyproject.toml',
            detail=detail, file='pyproject.toml',
        )
        if self.auto_fix:
            self.content = re.sub(
                r'(\[project\]\n)',
                r'\1requires-python = ">=3.8"\n',
                self.content, count=1
            )
            issue.fixed = True
            issue.fix_description = 'Added requires-python = ">=3.8"'
        self.issues.append(issue)
    
    def check_py008_empty_classifiers(self) -> None:
        """PY008: Check for empty classifiers list."""
        classifiers_match = re.search(r'classifiers\s*=\s*\[\s*\]', self.content)
        if not classifiers_match:
            return
        
        self.issues.append(Issue(
            severity='info', code='PY008',
            title='Empty classifiers list',
            detail='Consider adding PyPI classifiers for better discoverability.',
            file='pyproject.toml',
        ))
    
    def check_py009_string_authors(self) -> None:
        """PY009: Check for authors in deprecated string format (PEP 621 requires objects).
        
        Note: Skip this check for Poetry projects which require string format.
        """
        if self._should_skip_string_author_check():
            return

        authors_match = re.search(r'authors\s*=\s*\[(.*?)\]', self.content, re.DOTALL)
        if not authors_match:
            return

        authors_block = authors_match.group(1)
        new_block = self._convert_string_author_block(authors_block)
        if new_block is None:
            return

        detail = (
            'authors field uses deprecated string format like "Name <email>".\n'
            'PEP 621 requires object format: {name = "...", email = "..."}.\n'
            'Newer setuptools will REJECT the string format.'
        )
        issue = Issue(
            severity='error', code='PY009',
            title='Authors use deprecated string format',
            detail=detail, file='pyproject.toml',
        )
        if self.auto_fix:
            self.content = re.sub(
                r'authors\s*=\s*\[.*?\]',
                f'authors = [\n{new_block}\n]',
                self.content,
                flags=re.DOTALL
            )
            # Clean up any double newlines that might have been introduced
            self.content = re.sub(r'\n{3,}', '\n\n', self.content)
            issue.fixed = True
            issue.fix_description = 'Converted string-format authors to PEP 621 object format'
        self.issues.append(issue)

    def _should_skip_string_author_check(self) -> bool:
        build_backend_match = re.search(r'build-backend\s*=\s*"([^"]+)"', self.content)
        return bool(build_backend_match and 'poetry' in build_backend_match.group(1).lower())

    @staticmethod
    def _convert_string_author_block(authors_block: str) -> Optional[str]:
        string_author_pattern = re.compile(r'^\s*["\']([^"\']+)<([^>]+)>["\']\s*,?\s*$')
        lines = authors_block.strip().splitlines()
        new_lines = []
        has_string_format = False

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue

            match = string_author_pattern.match(line)
            if match:
                has_string_format = True
                name = match.group(1).strip()
                email = match.group(2).strip()
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f'{indent}{{name = "{name}", email = "{email}"}},')
            else:
                new_lines.append(line)

        if not has_string_format:
            return None

        return '\n'.join(new_lines)
