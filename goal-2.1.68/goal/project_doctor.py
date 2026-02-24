"""Project doctor — auto-diagnose and auto-fix common project configuration issues.

Scans a project directory for known problems (broken pyproject.toml, missing
build-system, deprecated classifiers, bad setuptools backend, missing lock files,
etc.) and either fixes them automatically or reports what needs to be done.

Every action is logged with a clear explanation so the user understands *why*
a change was made.
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import click


# =============================================================================
# Diagnostic result model
# =============================================================================

@dataclass
class Issue:
    """A single diagnosed issue."""
    severity: str          # 'error', 'warning', 'info'
    code: str              # e.g. 'PY001'
    title: str             # short one-liner
    detail: str            # longer explanation for the user
    file: Optional[str] = None
    fixed: bool = False
    fix_description: str = ""


@dataclass
class DoctorReport:
    """Aggregated report from a doctor run."""
    project_dir: Path
    project_type: str
    issues: List[Issue] = field(default_factory=list)

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def fixed(self) -> List[Issue]:
        return [i for i in self.issues if i.fixed]

    @property
    def has_problems(self) -> bool:
        return any(i.severity in ('error', 'warning') for i in self.issues)


# =============================================================================
# Logging helpers
# =============================================================================

_SEVERITY_STYLE = {
    'error':   ('✗', 'red'),
    'warning': ('⚠', 'yellow'),
    'info':    ('ℹ', 'cyan'),
}


def _log_issue(issue: Issue):
    icon, color = _SEVERITY_STYLE.get(issue.severity, ('•', 'white'))
    tag = click.style(f"[{issue.code}]", fg='bright_black')
    msg = click.style(f"{icon} {issue.title}", fg=color, bold=issue.severity == 'error')
    click.echo(f"  {tag} {msg}")
    if issue.detail:
        for line in issue.detail.strip().splitlines():
            click.echo(click.style(f"       {line}", fg='bright_black'))


def _log_fix(issue: Issue):
    click.echo(click.style(f"  ✓ FIXED [{issue.code}]: {issue.fix_description}", fg='green'))


# =============================================================================
# Python diagnostics
# =============================================================================

LICENSE_CLASSIFIERS_RE = re.compile(
    r'^\s*"License\s*::\s*OSI Approved\s*::\s*[^"]*"', re.MULTILINE
)

DEPRECATED_BACKENDS = [
    'setuptools.backends._legacy',
]


def _diagnose_python(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# Node.js diagnostics
# =============================================================================

def _diagnose_nodejs(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# Rust diagnostics
# =============================================================================

def _diagnose_rust(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    issues: List[Issue] = []
    cargo = project_dir / 'Cargo.toml'
    if not cargo.exists():
        return issues

    content = cargo.read_text(errors='ignore')

    if not re.search(r'^\[package\]', content, re.MULTILINE):
        issues.append(Issue(
            severity='error', code='RS001',
            title='Missing [package] section in Cargo.toml',
            detail='Cargo.toml needs a [package] section with name and version.',
            file='Cargo.toml',
        ))

    if 'edition' not in content:
        issues.append(Issue(
            severity='warning', code='RS002',
            title='No edition specified in Cargo.toml',
            detail='Consider adding edition = "2021" to [package] for modern Rust features.',
            file='Cargo.toml',
        ))

    return issues


# =============================================================================
# Go diagnostics
# =============================================================================

def _diagnose_go(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# Ruby diagnostics
# =============================================================================

def _diagnose_ruby(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# PHP diagnostics
# =============================================================================

def _diagnose_php(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# .NET diagnostics
# =============================================================================

def _diagnose_dotnet(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# Java diagnostics
# =============================================================================

def _diagnose_java(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
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


# =============================================================================
# Dispatcher
# =============================================================================

_DIAGNOSTICS = {
    'python': _diagnose_python,
    'nodejs': _diagnose_nodejs,
    'rust':   _diagnose_rust,
    'go':     _diagnose_go,
    'ruby':   _diagnose_ruby,
    'php':    _diagnose_php,
    'dotnet': _diagnose_dotnet,
    'java':   _diagnose_java,
}


def diagnose_project(project_dir: Path, project_type: str,
                     auto_fix: bool = True) -> DoctorReport:
    """Run diagnostics for a single project directory.

    Args:
        project_dir: Path to the project root.
        project_type: One of the known project type keys.
        auto_fix: If True, automatically fix issues where possible.

    Returns:
        A DoctorReport with all found (and optionally fixed) issues.
    """
    report = DoctorReport(project_dir=project_dir.resolve(), project_type=project_type)
    diag_fn = _DIAGNOSTICS.get(project_type)
    if diag_fn:
        report.issues = diag_fn(project_dir, auto_fix=auto_fix)
    return report


def diagnose_and_report(project_dir: Path, project_type: str,
                        auto_fix: bool = True) -> DoctorReport:
    """Diagnose, fix, and print a human-readable report."""
    try:
        rel = project_dir.relative_to(Path('.').resolve())
    except ValueError:
        rel = project_dir

    click.echo(click.style(f"\n🩺 Diagnosing {project_type} project in {rel}", fg='cyan', bold=True))
    report = diagnose_project(project_dir, project_type, auto_fix=auto_fix)

    if not report.issues:
        click.echo(click.style("  ✓ No issues found", fg='green'))
        return report

    for issue in report.issues:
        _log_issue(issue)
        if issue.fixed:
            _log_fix(issue)

    # Summary line
    n_err = len(report.errors)
    n_warn = len(report.warnings)
    n_fixed = len(report.fixed)
    parts = []
    if n_err:
        parts.append(click.style(f"{n_err} error(s)", fg='red'))
    if n_warn:
        parts.append(click.style(f"{n_warn} warning(s)", fg='yellow'))
    if n_fixed:
        parts.append(click.style(f"{n_fixed} auto-fixed", fg='green'))
    click.echo("  " + ", ".join(parts))

    return report


# =============================================================================
# TODO Management
# =============================================================================

def _generate_ticket_id(issue: Issue) -> str:
    """Generate unique ticket ID from issue code and title."""
    # Use code + first 50 chars of title (normalized) as unique identifier
    title_normalized = re.sub(r'[^a-zA-Z0-9]', '', issue.title.lower())[:50]
    return f"{issue.code}-{title_normalized}"


def _read_existing_tickets(todo_file: Path) -> Set[str]:
    """Read existing ticket IDs from TODO.md."""
    if not todo_file.exists():
        return set()
    
    content = todo_file.read_text(encoding='utf-8')
    tickets = set()
    
    # Look for ticket IDs in format: - [PY001-...] Issue title
    for line in content.splitlines():
        match = re.match(r'^-\s*\[([A-Z]+\d+-[a-zA-Z0-9]+)\]', line)
        if match:
            tickets.add(match.group(1))
    
    return tickets


def _format_todo_entry(issue: Issue) -> str:
    """Format issue as TODO.md entry."""
    ticket_id = _generate_ticket_id(issue)
    severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.severity, "⚪")
    
    entry = f"- [{ticket_id}] {severity_icon} **{issue.title}**"
    
    if issue.file:
        entry += f" (`{issue.file}`)"
    
    entry += f"\n  - {issue.detail}"
    
    if issue.fixed:
        entry += f"\n  - ✅ **Fixed**: {issue.fix_description}"
    
    return entry


def add_issues_to_todo(project_dir: Path, issues: List[Issue], todo_file: str = "TODO.md") -> int:
    """Add issues to TODO.md without duplicates.
    
    Args:
        project_dir: Project directory path
        issues: List of issues to add
        todo_file: Name of TODO file (default: TODO.md)
        
    Returns:
        Number of new issues added
    """
    if not issues:
        return 0
    
    todo_path = project_dir / todo_file
    existing_tickets = _read_existing_tickets(todo_path)
    
    # Filter only unfixed issues and generate new entries
    new_entries = []
    added_count = 0
    
    for issue in issues:
        if issue.fixed:
            continue  # Skip fixed issues
            
        ticket_id = _generate_ticket_id(issue)
        if ticket_id not in existing_tickets:
            new_entries.append(_format_todo_entry(issue))
            existing_tickets.add(ticket_id)  # Mark as added to avoid duplicates in this run
            added_count += 1
    
    if not new_entries:
        return 0
    
    # Prepare content
    timestamp = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=short'], 
                              capture_output=True, text=True, cwd=project_dir).stdout.strip()
    if not timestamp:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d')
    
    header = f"\n## Issues Found - {timestamp}\n\n"
    content = header + "\n\n".join(new_entries) + "\n"
    
    # Write to TODO.md
    if todo_path.exists():
        existing_content = todo_path.read_text(encoding='utf-8')
        # Insert before the last section or at the end
        if existing_content.strip():
            todo_path.write_text(existing_content.rstrip() + content, encoding='utf-8')
        else:
            todo_path.write_text(f"# TODO\n\n{content}", encoding='utf-8')
    else:
        todo_path.write_text(f"# TODO\n\n{content}", encoding='utf-8')
    
    click.echo(click.style(f"  📝 Added {added_count} new issue(s) to {todo_file}", fg='cyan'))
    return added_count


def diagnose_and_report_with_todo(project_dir: Path, project_type: str,
                                 auto_fix: bool = True, todo_file: str = "TODO.md") -> DoctorReport:
    """Diagnose, fix, report, and optionally add issues to TODO.md."""
    report = diagnose_and_report(project_dir, project_type, auto_fix)
    
    # Add unfixed issues to TODO.md
    if report.issues:
        unfixed_issues = [i for i in report.issues if not i.fixed]
        if unfixed_issues:
            add_issues_to_todo(project_dir, unfixed_issues, todo_file)
    
    return report
