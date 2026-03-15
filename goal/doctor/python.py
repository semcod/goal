"""Python project diagnostics - refactored."""

import re
from pathlib import Path
from typing import List, Tuple

from goal.doctor.models import Issue


LICENSE_CLASSIFIERS_RE = re.compile(
    r'^\s*"License\s*::\s*OSI Approved\s*::\s*[^"]*"', re.MULTILINE
)

DEPRECATED_BACKENDS = [
    'setuptools.backends._legacy',
]


class PythonDiagnostics:
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
            'Found: ' + ', '.join(c.strip().strip('"').strip(',') for c in license_classifiers)
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
        """PY009: Check for authors in deprecated string format (PEP 621 requires objects)."""
        authors_match = re.search(r'authors\s*=\s*\[(.*?)\]', self.content, re.DOTALL)
        if not authors_match:
            return
        
        authors_block = authors_match.group(1)
        # Pattern to match string format: "Name <email>" or 'Name <email>'
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
                # Replace with object format, preserving indentation
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f'{indent}{{name = "{name}", email = "{email}"}},')
            else:
                new_lines.append(line)
        
        if not has_string_format:
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
            new_block = '\n'.join(new_lines)
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

    def check_py010_project_name_consistency(self) -> None:
        """PY010: Check for consistent project name across all config files."""
        name_match = re.search(r'^name\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if not name_match:
            return
        pyproject_name = name_match.group(1)
        
        inconsistencies = []
        setup_py = self.project_dir / 'setup.py'
        goal_yaml = self.project_dir / 'goal.yaml'
        
        if setup_py.exists():
            setup_content = setup_py.read_text(errors='ignore')
            setup_name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', setup_content)
            if setup_name_match and setup_name_match.group(1) != pyproject_name:
                inconsistencies.append(f"setup.py: '{setup_name_match.group(1)}'")
        
        if goal_yaml.exists():
            goal_content = goal_yaml.read_text(errors='ignore')
            goal_name_match = re.search(r'^\s*name:\s*(\S+)', goal_content, re.MULTILINE)
            if goal_name_match and goal_name_match.group(1) != pyproject_name:
                inconsistencies.append(f"goal.yaml: '{goal_name_match.group(1)}'")
        
        if not inconsistencies:
            return
        
        detail = f"Project name inconsistency. pyproject.toml: '{pyproject_name}', others: {', '.join(inconsistencies)}"
        issue = Issue(severity='error', code='PY010', title='Inconsistent project name', detail=detail, file='pyproject.toml')
        
        if self.auto_fix:
            if setup_py.exists():
                setup_content = re.sub(r'(name\s*=\s*)["\'][^"\']+["\']', rf'\1"{pyproject_name}"', setup_py.read_text(errors='ignore'))
                setup_py.write_text(setup_content, encoding='utf-8')
            if goal_yaml.exists():
                goal_content = re.sub(r'^(\s*name:\s*)\S+', rf'\1{pyproject_name}', goal_yaml.read_text(errors='ignore'), flags=re.MULTILINE)
                goal_yaml.write_text(goal_content, encoding='utf-8')
            issue.fixed = True
            issue.fix_description = f"Synchronized name to '{pyproject_name}'"
        self.issues.append(issue)

    def check_py011_version_consistency(self) -> None:
        """PY011: Check for consistent version across all config files."""
        version_match = re.search(r'^version\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if not version_match:
            return
        pyproject_version = version_match.group(1)
        
        inconsistencies = []
        setup_py = self.project_dir / 'setup.py'
        version_file = self.project_dir / 'VERSION'
        init_py = None
        
        if setup_py.exists():
            setup_content = setup_py.read_text(errors='ignore')
            setup_ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
            if setup_ver_match and setup_ver_match.group(1) != pyproject_version:
                inconsistencies.append(f"setup.py: '{setup_ver_match.group(1)}'")
        
        name_match = re.search(r'^name\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if name_match:
            pkg_name = name_match.group(1).replace('-', '_')
            init_py = self.project_dir / pkg_name / '__init__.py'
            if init_py.exists():
                init_content = init_py.read_text(errors='ignore')
                init_ver_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
                if init_ver_match and init_ver_match.group(1) != pyproject_version:
                    inconsistencies.append(f"{pkg_name}/__init__.py: '{init_ver_match.group(1)}'")
        
        if version_file.exists():
            file_version = version_file.read_text().strip()
            if file_version != pyproject_version:
                inconsistencies.append(f"VERSION: '{file_version}'")
        
        if not inconsistencies:
            return
        
        detail = f"Version inconsistency. pyproject.toml: '{pyproject_version}', others: {', '.join(inconsistencies)}"
        issue = Issue(severity='error', code='PY011', title='Inconsistent version', detail=detail, file='pyproject.toml')
        
        if self.auto_fix:
            if setup_py.exists():
                setup_content = re.sub(r'(version\s*=\s*)["\'][^"\']+["\']', rf'\1"{pyproject_version}"', setup_py.read_text(errors='ignore'))
                setup_py.write_text(setup_content, encoding='utf-8')
            if init_py and init_py.exists():
                init_content = re.sub(r'(__version__\s*=\s*)["\'][^"\']+["\']', rf'\1"{pyproject_version}"', init_py.read_text(errors='ignore'))
                init_py.write_text(init_content, encoding='utf-8')
            if version_file.exists():
                version_file.write_text(pyproject_version + '\n', encoding='utf-8')
            issue.fixed = True
            issue.fix_description = f"Synchronized version to '{pyproject_version}'"
        self.issues.append(issue)

    def check_py012_dist_cleanup(self) -> None:
        """PY012: Check for stale package files in dist/ directory."""
        dist_dir = self.project_dir / 'dist'
        if not dist_dir.exists():
            return
        
        name_match = re.search(r'^name\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if not name_match:
            return
        project_name = name_match.group(1)
        
        stale_files = [f.name for f in dist_dir.iterdir() if f.is_file() and not f.name.startswith(f'{project_name}-')]
        if not stale_files:
            return
        
        detail = f"Found {len(stale_files)} stale file(s) in dist/: {', '.join(stale_files)}"
        issue = Issue(severity='error', code='PY012', title='Stale files in dist/', detail=detail, file='dist/')
        
        if self.auto_fix:
            for fname in stale_files:
                (dist_dir / fname).unlink()
            issue.fixed = True
            issue.fix_description = f"Removed {len(stale_files)} stale file(s)"
        self.issues.append(issue)

    def check_py013_goal_publish_pattern(self) -> None:
        """PY013: Check for correct publish pattern in goal.yaml."""
        goal_yaml = self.project_dir / 'goal.yaml'
        if not goal_yaml.exists():
            return
        
        goal_content = goal_yaml.read_text(errors='ignore')
        name_match = re.search(r'^name\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if not name_match:
            return
        
        project_name = name_match.group(1)
        # Match publish pattern to end of line (YAML value can contain spaces)
        publish_match = re.search(r'publish:\s*(.+?)(?:\s*$|\s+\w+:|\n\w+)', goal_content, re.MULTILINE)
        if not publish_match:
            return
        
        publish_pattern = publish_match.group(1).strip()
        expected = f'twine upload dist/{project_name}-{{version}}*'
        
        if publish_pattern == expected:
            return
        if project_name in publish_pattern and 'goal-' not in publish_pattern:
            return
        
        detail = f"Incorrect publish pattern: '{publish_pattern}'. Expected: '{expected}'"
        issue = Issue(severity='error', code='PY013', title='Wrong publish pattern', detail=detail, file='goal.yaml')
        
        if self.auto_fix:
            # Replace entire publish value, not just first word
            new_content = re.sub(
                r'(publish:\s*)(.+?)(\s*$|\s+\w+:|\n\w+)',
                rf'\1{expected}\3',
                goal_content,
                flags=re.MULTILINE
            )
            goal_yaml.write_text(new_content, encoding='utf-8')
            issue.fixed = True
            issue.fix_description = f"Fixed pattern to '{expected}'"
        self.issues.append(issue)

    def write_fixes(self, pyproject: Path) -> None:
        """Write fixes back to file if content changed."""
        if self.content != self.original_content and self.auto_fix:
            pyproject.write_text(self.content, encoding='utf-8')


def diagnose_python(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Python-specific diagnostics."""
    pyproject = project_dir / 'pyproject.toml'
    setup_py = project_dir / 'setup.py'
    setup_cfg = project_dir / 'setup.cfg'
    requirements = project_dir / 'requirements.txt'
    
    # PY001: Quick return if no config files
    if not pyproject.exists() and not setup_py.exists() and not setup_cfg.exists():
        issues: List[Issue] = []
        if requirements.exists():
            issues.append(Issue(
                severity='warning', code='PY001',
                title='No pyproject.toml / setup.py / setup.cfg found',
                detail='Only requirements.txt exists. Consider adding pyproject.toml for proper packaging.',
            ))
        return issues
    
    if not pyproject.exists():
        return []
    
    # Initialize diagnostics
    content = pyproject.read_text(errors='ignore')
    diag = PythonDiagnostics(project_dir, content, auto_fix)
    
    # Run all checks
    diag.check_py002_build_system()
    diag.check_py003_license_classifiers()
    diag.check_py004_deprecated_backends()
    diag.check_py005_license_table()
    diag.check_py006_duplicate_authors()
    diag.check_py007_requires_python()
    diag.check_py008_empty_classifiers()
    diag.check_py009_string_authors()
    diag.check_py010_project_name_consistency()
    diag.check_py011_version_consistency()
    diag.check_py012_dist_cleanup()
    diag.check_py013_goal_publish_pattern()
    
    # Write fixes
    diag.write_fixes(pyproject)
    
    return diag.issues
