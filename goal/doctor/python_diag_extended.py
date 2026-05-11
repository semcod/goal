"""Python project diagnostics — extended checks (PY010–PY014)."""

import re
from pathlib import Path
from typing import List, Optional

from goal.doctor.models import Issue
from goal.doctor.python_diag_core import PythonDiagnosticsCore


class PythonDiagnostics(PythonDiagnosticsCore):
    CHECK_METHODS = [
        'check_py002_build_system',
        'check_py003_license_classifiers',
        'check_py004_deprecated_backends',
        'check_py005_license_table',
        'check_py006_duplicate_authors',
        'check_py007_requires_python',
        'check_py008_empty_classifiers',
        'check_py009_string_authors',
        'check_py010_project_name_consistency',
        'check_py011_version_consistency',
        'check_py012_dist_cleanup',
        'check_py013_goal_publish_pattern',
        'check_py014_pypi_token',
    ]

    def _collect_py010_inconsistencies(self, pyproject_name: str, setup_py: Path, goal_yaml: Path) -> List[str]:
        inconsistencies: List[str] = []

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

        return inconsistencies

    def _sync_py010_files(self, pyproject_name: str, setup_py: Path, goal_yaml: Path) -> List[str]:
        fixed_files: List[str] = []

        if setup_py.exists():
            setup_content = setup_py.read_text(errors='ignore')
            new_setup = re.sub(r'(name\s*=\s*)["\'][^"\']+["\']', rf'\1"{pyproject_name}"', setup_content)
            if new_setup != setup_content:
                setup_py.write_text(new_setup, encoding='utf-8')
                fixed_files.append('setup.py')

        if goal_yaml.exists():
            goal_content = goal_yaml.read_text(errors='ignore')
            new_goal = re.sub(r'^(\s*name:\s*)\S+', rf'\1{pyproject_name}', goal_content, flags=re.MULTILINE)
            if new_goal != goal_content:
                goal_yaml.write_text(new_goal, encoding='utf-8')
                fixed_files.append('goal.yaml')

        return fixed_files

    def check_py010_project_name_consistency(self) -> None:
        """PY010: Check for consistent project name across all config files."""
        name_match = re.search(r'^name\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if not name_match:
            return
        pyproject_name = name_match.group(1)

        setup_py = self.project_dir / 'setup.py'
        goal_yaml = self.project_dir / 'goal.yaml'
        inconsistencies = self._collect_py010_inconsistencies(pyproject_name, setup_py, goal_yaml)

        if not inconsistencies:
            return

        detail = f"Project name inconsistency. pyproject.toml: '{pyproject_name}', others: {', '.join(inconsistencies)}"
        issue = Issue(severity='error', code='PY010', title='Inconsistent project name', detail=detail, file='pyproject.toml')

        if self.auto_fix:
            fixed_files = self._sync_py010_files(pyproject_name, setup_py, goal_yaml)
            if fixed_files:
                issue.fixed = True
                issue.fix_description = f"Synchronized name to '{pyproject_name}' in {', '.join(fixed_files)}"
        self.issues.append(issue)

    def _collect_py011_inconsistencies(self, pyproject_version: str, setup_py: Path,
                                       init_py: Optional[Path], version_file: Path) -> List[str]:
        inconsistencies: List[str] = []

        if setup_py.exists():
            setup_content = setup_py.read_text(errors='ignore')
            setup_ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
            if setup_ver_match and setup_ver_match.group(1) != pyproject_version:
                inconsistencies.append(f"setup.py: '{setup_ver_match.group(1)}'")

        if init_py and init_py.exists():
            init_content = init_py.read_text(errors='ignore')
            init_ver_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
            if init_ver_match and init_ver_match.group(1) != pyproject_version:
                inconsistencies.append(f"{init_py.parent.name}/__init__.py: '{init_ver_match.group(1)}'")

        if version_file.exists():
            file_version = version_file.read_text().strip()
            if file_version != pyproject_version:
                inconsistencies.append(f"VERSION: '{file_version}'")

        return inconsistencies

    def _sync_py011_files(self, pyproject_version: str, setup_py: Path,
                          init_py: Optional[Path], version_file: Path) -> None:
        if setup_py.exists():
            setup_content = re.sub(
                r'(version\s*=\s*)["\'][^"\']+["\']',
                rf'\1"{pyproject_version}"',
                setup_py.read_text(errors='ignore')
            )
            setup_py.write_text(setup_content, encoding='utf-8')

        if init_py and init_py.exists():
            init_content = re.sub(
                r'(__version__\s*=\s*)["\'][^"\']+["\']',
                rf'\1"{pyproject_version}"',
                init_py.read_text(errors='ignore')
            )
            init_py.write_text(init_content, encoding='utf-8')

        if version_file.exists():
            version_file.write_text(f"{pyproject_version}\n", encoding='utf-8')

    def check_py011_version_consistency(self) -> None:
        """PY011: Check for consistent version across all config files."""
        version_match = re.search(r'^version\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if not version_match:
            return
        pyproject_version = version_match.group(1)

        setup_py = self.project_dir / 'setup.py'
        version_file = self.project_dir / 'VERSION'
        init_py = None

        name_match = re.search(r'^name\s*=\s*"([^"]+)"', self.content, re.MULTILINE)
        if name_match:
            pkg_name = name_match.group(1).replace('-', '_')
            init_py = self.project_dir / pkg_name / '__init__.py'

        inconsistencies = self._collect_py011_inconsistencies(pyproject_version, setup_py, init_py, version_file)

        if not inconsistencies:
            return

        detail = f"Version inconsistency. pyproject.toml: '{pyproject_version}', others: {', '.join(inconsistencies)}"
        issue = Issue(severity='error', code='PY011', title='Inconsistent version', detail=detail, file='pyproject.toml')

        if self.auto_fix:
            self._sync_py011_files(pyproject_version, setup_py, init_py, version_file)
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

        stale_files = self._collect_stale_dist_files(dist_dir, project_name)
        if not stale_files:
            return

        detail = f"Found {len(stale_files)} stale file(s) in dist/: {', '.join(stale_files)}"
        issue = Issue(severity='error', code='PY012', title='Stale files in dist/', detail=detail, file='dist/')

        if self.auto_fix:
            removed = self._remove_stale_dist_files(dist_dir, stale_files)
            if removed:
                issue.fixed = True
                issue.fix_description = f"Removed {len(removed)} stale file(s)"
        self.issues.append(issue)

    @staticmethod
    def _collect_stale_dist_files(dist_dir: Path, project_name: str) -> List[str]:
        return [
            f.name for f in dist_dir.iterdir()
            if f.is_file() and not f.name.startswith(f'{project_name}-')
        ]

    @staticmethod
    def _remove_stale_dist_files(dist_dir: Path, stale_files: List[str]) -> List[str]:
        removed = []
        for fname in stale_files:
            fpath = dist_dir / fname
            try:
                fpath.unlink()
                removed.append(fname)
            except OSError:
                pass  # File couldn't be removed
        return removed

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
        publish_pattern = self._extract_goal_publish_pattern(goal_content)
        if not publish_pattern:
            return

        expected = f'twine upload dist/{project_name}-{{version}}*'

        if self._goal_publish_pattern_is_acceptable(project_name, publish_pattern, expected):
            return

        detail = f"Incorrect publish pattern: '{publish_pattern}'. Expected: '{expected}'"
        issue = Issue(severity='error', code='PY013', title='Wrong publish pattern', detail=detail, file='goal.yaml')

        if self.auto_fix:
            new_content = self._rewrite_goal_publish_pattern(goal_content, expected)
            if new_content != goal_content:
                goal_yaml.write_text(new_content, encoding='utf-8')
                issue.fixed = True
                issue.fix_description = f"Fixed pattern to '{expected}'"
        self.issues.append(issue)

    @staticmethod
    def _extract_goal_publish_pattern(goal_content: str) -> Optional[str]:
        publish_match = re.search(r'publish:\s*(.+?)(?:\s*$|\s+\w+:|\n\w+)', goal_content, re.MULTILINE)
        if not publish_match:
            return None
        return publish_match.group(1).strip()

    @staticmethod
    def _goal_publish_pattern_is_acceptable(project_name: str, publish_pattern: str, expected: str) -> bool:
        if publish_pattern == expected:
            return True
        return project_name in publish_pattern and 'goal-' not in publish_pattern

    @staticmethod
    def _rewrite_goal_publish_pattern(goal_content: str, expected: str) -> str:
        return re.sub(
            r'(publish:\s*)(.+?)(\s*$|\s+\w+:|\n\w+)',
            rf'\1{expected}\3',
            goal_content,
            flags=re.MULTILINE
        )

    def check_py014_pypi_token(self) -> None:
        """PY014: Check for PyPI token configuration before publishing."""
        import os
        
        # Check if this project uses Python and has publish enabled
        goal_yaml = self.project_dir / 'goal.yaml'
        if not goal_yaml.exists():
            return

        goal_content = goal_yaml.read_text(errors='ignore')
        if not self._is_publish_enabled(goal_content):
            return

        if self._has_pypi_credentials():
            return

        detail = (
            "PyPI token not configured. Publishing will fail with 403 Forbidden.\n"
            "Set PYPI_TOKEN environment variable or configure ~/.pypirc file."
        )
        issue = Issue(
            severity='error', code='PY014',
            title='Missing PyPI token',
            detail=detail, file='goal.yaml'
        )
        self.issues.append(issue)

    @staticmethod
    def _is_publish_enabled(goal_content: str) -> bool:
        return 'publish_enabled: true' in goal_content or 'publish_enabled:true' in goal_content

    def _has_pypi_credentials(self) -> bool:
        import os

        pypi_token = os.environ.get('PYPI_TOKEN') or os.environ.get('TWINE_PASSWORD')
        pypirc_project = self.project_dir / '.pypirc'
        pypirc_home = Path.home() / '.pypirc'
        return bool(pypi_token or pypirc_project.exists() or pypirc_home.exists())

    def run_all_checks(self) -> None:
        """Run all registered check methods in order."""
        for method_name in self.CHECK_METHODS:
            method = getattr(self, method_name)
            method()

    def write_fixes(self, pyproject: Path) -> None:
        """Write fixes back to file if content changed."""
        if self.content != self.original_content and self.auto_fix:
            pyproject.write_text(self.content, encoding='utf-8')

