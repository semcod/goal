#!/usr/bin/env python3
"""Goal CLI - Automated git push with smart commit messages and version management."""

import subprocess
import os
import sys
import re
import json
import shutil
import shlex
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import click
try:
    from .formatter import format_push_result, format_status_output, format_enhanced_summary
    from .commit_generator import CommitMessageGenerator
    from .config import GoalConfig, ensure_config, init_config, load_config
except ImportError:
    from formatter import format_push_result, format_status_output, format_enhanced_summary
    from commit_generator import CommitMessageGenerator
    from config import GoalConfig, ensure_config, init_config, load_config


ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


def strip_ansi(text: str) -> str:
    try:
        return ANSI_ESCAPE_RE.sub('', text)
    except Exception:
        return text


def read_tickert(path: Path = Path('TICKET')) -> Dict[str, str]:
    """Read TICKET configuration file (key=value)."""
    cfg: Dict[str, str] = {'prefix': '', 'format': '[{ticket}] {title}'}
    if not path.exists():
        return cfg
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            cfg[k.strip()] = v.strip()
    except Exception:
        return cfg
    return cfg


def apply_ticket_prefix(title: str, ticket: Optional[str]) -> str:
    """Apply ticket prefix (from CLI or TICKERT) to commit title."""
    cfg = read_tickert()
    ticket_value = (ticket or cfg.get('prefix') or '').strip()
    if not ticket_value:
        return title
    fmt = cfg.get('format') or '[{ticket}] {title}'
    try:
        return fmt.format(ticket=ticket_value, title=title)
    except Exception:
        return f"[{ticket_value}] {title}"


def split_paths_by_type(paths: List[str]) -> Dict[str, List[str]]:
    """Split file paths into groups (code/docs/ci/examples/other)."""
    groups: Dict[str, List[str]] = {'code': [], 'docs': [], 'ci': [], 'examples': [], 'other': []}
    for p in paths:
        pl = p.lower()
        if pl.startswith('examples/'):
            groups['examples'].append(p)
        elif pl.startswith('docs/') or pl.endswith(('.md', '.rst')) or os.path.basename(pl) in ('readme.md',):
            groups['docs'].append(p)
        elif pl.startswith('.github/') or pl.startswith('.gitlab/') or pl.endswith(('.yml', '.yaml')):
            groups['ci'].append(p)
        elif pl.startswith('goal/') or pl.startswith('src/') or pl.startswith('lib/') or pl.endswith('.py'):
            groups['code'].append(p)
        else:
            groups['other'].append(p)

    return {k: v for k, v in groups.items() if v}


def stage_paths(paths: List[str]):
    if not paths:
        return
    # stage in chunks to avoid arg length issues
    chunk: List[str] = []
    for p in paths:
        chunk.append(p)
        if len(chunk) >= 100:
            run_git('add', '--', *chunk)
            chunk = []
    if chunk:
        run_git('add', '--', *chunk)


# =============================================================================
# Project Type Detection & Version File Management
# =============================================================================

PROJECT_TYPES = {
    'python': {
        'files': ['pyproject.toml', 'setup.py', 'setup.cfg'],
        'version_patterns': {
            'pyproject.toml': r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'setup.py': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'setup.cfg': r'^version\s*=\s*(\d+\.\d+\.\d+)',
        },
        'test_command': 'pytest',
        'publish_command': 'python -m build && python -m twine upload dist/goal-{version}*',
    },
    'nodejs': {
        'files': ['package.json'],
        'version_patterns': {
            'package.json': r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'npm test',
        'publish_command': 'npm publish',
    },
    'rust': {
        'files': ['Cargo.toml'],
        'version_patterns': {
            'Cargo.toml': r'^version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'cargo test',
        'publish_command': 'cargo publish',
    },
    'go': {
        'files': ['go.mod'],
        'version_patterns': {},  # Go uses git tags
        'test_command': 'go test ./...',
        'publish_command': 'git push origin --tags',
    },
    'ruby': {
        'files': ['Gemfile', '*.gemspec'],
        'version_patterns': {
            '*.gemspec': r'\.version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
        },
        'test_command': 'bundle exec rspec',
        'publish_command': 'gem build *.gemspec && gem push *.gem',
    },
    'php': {
        'files': ['composer.json'],
        'version_patterns': {
            'composer.json': r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'composer test',
        'publish_command': 'composer publish',
    },
    'dotnet': {
        'files': ['*.csproj', '*.fsproj'],
        'version_patterns': {
            '*.csproj': r'<Version>(\d+\.\d+\.\d+)</Version>',
            '*.fsproj': r'<Version>(\d+\.\d+\.\d+)</Version>',
        },
        'test_command': 'dotnet test',
        'publish_command': 'dotnet pack && dotnet nuget push *.nupkg',
    },
    'java': {
        'files': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
        'version_patterns': {
            'pom.xml': r'<version>(\d+\.\d+\.\d+)</version>',
            'build.gradle': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'build.gradle.kts': r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'mvn test',
        'publish_command': 'mvn deploy',
    },
}

# Conventional commit types based on file patterns
COMMIT_TYPES = {
    'feat': ['add', 'new', 'create', 'implement'],
    'fix': ['fix', 'bug', 'patch', 'repair', 'resolve'],
    'docs': ['readme', 'doc', 'comment', 'license'],
    'style': ['format', 'style', 'lint', 'whitespace'],
    'refactor': ['refactor', 'restructure', 'reorganize', 'rename'],
    'perf': ['perf', 'optimize', 'speed', 'cache'],
    'test': ['test', 'spec', 'coverage'],
    'build': ['build', 'compile', 'makefile', 'docker', 'ci', 'cd'],
    'chore': ['chore', 'deps', 'update', 'bump', 'config'],
}


def run_git(*args, capture=True):
    """Run a git command and return the result."""
    result = subprocess.run(
        ['git'] + list(args),
        capture_output=capture,
        text=True
    )
    return result


def run_command(command: str, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        command,
        shell=True,
        capture_output=capture,
        text=True
    )


def run_command_tee(command: str) -> subprocess.CompletedProcess:
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output: List[str] = []
    if proc.stdout is not None:
        for chunk in proc.stdout:
            output.append(chunk)
            click.echo(chunk, nl=False)
            sys.stdout.flush()

    returncode = proc.wait()
    return subprocess.CompletedProcess(args=command, returncode=returncode, stdout=''.join(output), stderr='')


def confirm(prompt: str, default: bool = True) -> bool:
    """Ask for user confirmation with Y/n prompt (Enter defaults to Yes)."""
    if default:
        suffix = " [Y/n] "
    else:
        suffix = " [y/N] "
    
    while True:
        response = input(click.style(prompt, fg='cyan') + suffix).strip().lower()
        
        if not response:
            return default
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            click.echo(click.style("Please respond with 'y' or 'n'", fg='red'))


def detect_project_types() -> List[str]:
    """Detect what type(s) of project this is."""
    detected = []
    for ptype, config in PROJECT_TYPES.items():
        for file_pattern in config['files']:
            if '*' in file_pattern:
                if list(Path('.').glob(file_pattern)):
                    detected.append(ptype)
                    break
            elif Path(file_pattern).exists():
                detected.append(ptype)
                break
    return detected


def find_version_files() -> Dict[str, Path]:
    """Find all version-containing files in the project."""
    found = {}
    for ptype, config in PROJECT_TYPES.items():
        for file_pattern, pattern in config.get('version_patterns', {}).items():
            if '*' in file_pattern:
                for f in Path('.').glob(file_pattern):
                    found[str(f)] = (f, pattern)
            elif Path(file_pattern).exists():
                found[file_pattern] = (Path(file_pattern), pattern)
    return found


def get_version_from_file(filepath: Path, pattern: str) -> Optional[str]:
    """Extract version from a file using regex pattern."""
    try:
        content = filepath.read_text()
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def update_version_in_file(filepath: Path, pattern: str, old_version: str, new_version: str) -> bool:
    """Update version in a specific file."""
    try:
        content = filepath.read_text()
        # Create replacement pattern
        new_content = re.sub(
            pattern.replace(r'(\d+\.\d+\.\d+)', old_version),
            lambda m: m.group(0).replace(old_version, new_version),
            content,
            count=1,
            flags=re.MULTILINE
        )
        if new_content != content:
            filepath.write_text(new_content)
            return True
    except Exception:
        pass
    return False


def update_json_version(filepath: Path, new_version: str) -> bool:
    """Update version in JSON files (package.json, composer.json)."""
    try:
        content = json.loads(filepath.read_text())
        if 'version' in content:
            content['version'] = new_version
            filepath.write_text(json.dumps(content, indent=2) + '\n')
            return True
    except Exception:
        pass
    return False


def sync_all_versions(new_version: str) -> List[str]:
    """Update version in all detected project files."""
    updated = []
    
    # Always update VERSION file
    Path('VERSION').write_text(new_version + '\n')
    updated.append('VERSION')
    
    # Update package.json
    if Path('package.json').exists():
        if update_json_version(Path('package.json'), new_version):
            updated.append('package.json')
    
    # Update composer.json
    if Path('composer.json').exists():
        if update_json_version(Path('composer.json'), new_version):
            updated.append('composer.json')
    
    # Update pyproject.toml
    if Path('pyproject.toml').exists():
        content = Path('pyproject.toml').read_text()
        new_content = re.sub(
            r'^(version\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
            rf'\g<1>{new_version}\g<2>',
            content,
            count=1,
            flags=re.MULTILINE
        )
        if new_content != content:
            Path('pyproject.toml').write_text(new_content)
            updated.append('pyproject.toml')
    
    # Update Cargo.toml
    if Path('Cargo.toml').exists():
        content = Path('Cargo.toml').read_text()
        new_content = re.sub(
            r'^(version\s*=\s*")\d+\.\d+\.\d+(")',
            rf'\g<1>{new_version}\g<2>',
            content,
            count=1,
            flags=re.MULTILINE
        )
        if new_content != content:
            Path('Cargo.toml').write_text(new_content)
            updated.append('Cargo.toml')
    
    # Update *.csproj
    for csproj in Path('.').glob('*.csproj'):
        content = csproj.read_text()
        new_content = re.sub(
            r'<Version>\d+\.\d+\.\d+</Version>',
            f'<Version>{new_version}</Version>',
            content,
            count=1
        )
        if new_content != content:
            csproj.write_text(new_content)
            updated.append(str(csproj))
    
    # Update pom.xml (first version tag only - project version)
    if Path('pom.xml').exists():
        content = Path('pom.xml').read_text()
        # Only update the first <version> which is typically the project version
        new_content = re.sub(
            r'(<version>)\d+\.\d+\.\d+(</version>)',
            rf'\g<1>{new_version}\g<2>',
            content,
            count=1
        )
        if new_content != content:
            Path('pom.xml').write_text(new_content)
            updated.append('pom.xml')
    
    return updated


# =============================================================================
# Git Diff Analysis for Smart Commit Messages
# =============================================================================

def get_staged_files() -> List[str]:
    """Get list of staged files."""
    result = run_git('diff', '--cached', '--name-only')
    return result.stdout.strip().split('\n') if result.stdout.strip() else []


def get_unstaged_files() -> List[str]:
    """Get list of unstaged/untracked files."""
    result = run_git('status', '--porcelain')
    return [line[3:] for line in result.stdout.strip().split('\n') if line]


def get_working_tree_files() -> List[str]:
    """Get list of files changed in working tree (unstaged + untracked)."""
    changed = run_git('diff', '--name-only').stdout.strip().split('\n')
    untracked = run_git('ls-files', '--others', '--exclude-standard').stdout.strip().split('\n')

    files: List[str] = []
    for f in [*changed, *untracked]:
        f = (f or '').strip()
        if not f:
            continue
        if f not in files:
            files.append(f)
    return files


def get_diff_stats(cached: bool = True) -> Dict[str, Tuple[int, int]]:
    """Get additions/deletions per file."""
    result = run_git('diff', '--cached', '--numstat') if cached else run_git('diff', '--numstat')
    stats = {}
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) == 3:
                adds = int(parts[0]) if parts[0] != '-' else 0
                dels = int(parts[1]) if parts[1] != '-' else 0
                stats[parts[2]] = (adds, dels)
    return stats


def get_diff_content(cached: bool = True) -> str:
    """Get the actual diff content for analysis."""
    result = run_git('diff', '--cached', '-U3') if cached else run_git('diff', '-U3')
    return result.stdout


def analyze_diff_for_type(diff_content: str, files: List[str]) -> str:
    """Analyze diff content to determine commit type."""
    diff_lower = diff_content.lower()
    
    # Check for test files
    if any('test' in f.lower() or 'spec' in f.lower() for f in files):
        return 'test'
    
    # Check for documentation
    if any(f.endswith('.md') or 'doc' in f.lower() for f in files):
        if all(f.endswith('.md') or 'doc' in f.lower() for f in files):
            return 'docs'
    
    # Check for new files (likely feat)
    result = run_git('diff', '--cached', '--name-status')
    if 'A\t' in result.stdout:
        return 'feat'
    
    # Check for fix patterns in diff
    fix_patterns = ['fix', 'bug', 'error', 'issue', 'problem', 'correct', 'repair']
    if any(p in diff_lower for p in fix_patterns):
        return 'fix'
    
    # Check for build/config files
    build_files = ['makefile', 'dockerfile', 'docker-compose', '.yml', '.yaml', 'ci', 'cd']
    if any(any(bf in f.lower() for bf in build_files) for f in files):
        return 'build'
    
    # Check for dependency updates
    dep_files = ['package.json', 'requirements.txt', 'pyproject.toml', 'cargo.toml', 'go.mod']
    if any(f.lower() in dep_files for f in files):
        return 'chore'
    
    # Default to chore for misc changes
    return 'chore'


def extract_function_changes(diff_content: str) -> List[str]:
    """Extract changed function/method names from diff."""
    functions = []
    
    # Python functions
    py_funcs = re.findall(r'^\+\s*def\s+(\w+)\s*\(', diff_content, re.MULTILINE)
    functions.extend(py_funcs)
    
    # JavaScript/TypeScript functions
    js_funcs = re.findall(r'^\+\s*(?:function|const|let|var)\s+(\w+)\s*[=(]', diff_content, re.MULTILINE)
    functions.extend(js_funcs)
    
    # Class definitions
    classes = re.findall(r'^\+\s*class\s+(\w+)', diff_content, re.MULTILINE)
    functions.extend([f'class {c}' for c in classes])
    
    return list(set(functions))[:5]  # Limit to 5


def generate_smart_commit_message(files: List[str], diff_content: str) -> str:
    """Generate intelligent commit message based on diff analysis."""
    if not files:
        return None
    
    # Use the new commit message generator
    generator = CommitMessageGenerator()
    return generator.generate_commit_message(cached=True)


def categorize_file(filename: str) -> Optional[str]:
    """Categorize file and return appropriate description."""
    basename = os.path.basename(filename)
    
    # Skip auto-generated files
    if basename in ('CHANGELOG.md', 'VERSION'):
        return None
    
    # Special files
    if basename == 'Makefile':
        return "build: update Makefile"
    elif basename == 'package.json':
        return "deps: update package.json"
    elif basename in ('Dockerfile', 'docker-compose.yml'):
        return "docker: update " + basename
    elif basename == 'README.md':
        return "docs: update README"
    elif filename.endswith('.md'):
        return f"docs: update {basename}"
    elif filename.endswith('.py'):
        return f"update {filename}"
    elif filename.endswith(('.js', '.ts', '.tsx', '.jsx')):
        return f"update {filename}"
    elif filename.endswith(('.yml', '.yaml')):
        return f"config: update {basename}"
    elif filename.endswith('.sh'):
        return f"scripts: update {basename}"
    else:
        return f"update {filename}"


# =============================================================================
# Version Management
# =============================================================================

def get_current_version() -> str:
    """Get current version from VERSION file or detect from project files."""
    # Try to detect from project files
    if Path('package.json').exists():
        try:
            data = json.loads(Path('package.json').read_text())
            if 'version' in data:
                return data['version']
        except Exception:
            pass
    
    if Path('pyproject.toml').exists():
        content = Path('pyproject.toml').read_text()
        match = re.search(r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)

    version_file = Path('VERSION')
    if version_file.exists():
        return version_file.read_text().strip()
    
    return "1.0.0"


def bump_version(version: str, bump_type: str = 'patch') -> str:
    """Bump version based on type (major, minor, patch)."""
    parts = version.split('.')
    if len(parts) != 3:
        return "1.0.0"
    
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return "1.0.0"
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"


# =============================================================================
# Changelog Management
# =============================================================================

def update_changelog(version: str, files: List[str], commit_msg: str, 
                     config: Dict = None, changelog_entry: Dict = None):
    """Update CHANGELOG.md with new version and changes.
    
    Args:
        version: New version string.
        files: List of changed files.
        commit_msg: Commit message.
        config: Optional goal.yaml config dict for domain grouping.
        changelog_entry: Optional structured changelog entry from smart_commit.
    """
    changelog_path = Path('CHANGELOG.md')
    existing_content = ""
    if changelog_path.exists():
        existing_content = changelog_path.read_text()
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Check if we should use domain grouping
    use_domain_grouping = False
    if config:
        use_domain_grouping = config.get('git', {}).get('changelog', {}).get('group_by_domain', False)
    
    # Build change list with domain grouping
    if use_domain_grouping and config:
        domain_mapping = config.get('git', {}).get('commit', {}).get('domain_mapping', {})
        domain_changes = {}
        
        for f in files:
            if not f:
                continue
            # Determine domain for file
            domain = 'other'
            for pattern, d in domain_mapping.items():
                import fnmatch
                if fnmatch.fnmatch(f, pattern):
                    domain = d
                    break
                if pattern.endswith('/*') and f.startswith(pattern[:-2]):
                    domain = d
                    break
            
            if domain not in domain_changes:
                domain_changes[domain] = []
            
            desc = categorize_file(f)
            if desc:
                domain_changes[domain].append(desc)
        
        # Create entry with domain sections
        new_entry = f"## [{version}] - {date_str}\n\n"
        new_entry += f"### Summary\n\n{commit_msg}\n\n"
        
        # Add entities if available
        if changelog_entry and changelog_entry.get('entity_details'):
            entities = changelog_entry['entity_details']
            new_entry += f"**Key Changes:** {', '.join(f'`{e}`' for e in entities[:5])}\n\n"
        
        # Domain sections
        domain_order = ['core', 'api', 'app', 'docs', 'test', 'build', 'ci', 'config', 'other']
        for domain in domain_order:
            if domain in domain_changes and domain_changes[domain]:
                domain_title = domain.capitalize()
                new_entry += f"### {domain_title}\n\n"
                for change in domain_changes[domain][:10]:
                    new_entry += f"- {change}\n"
                if len(domain_changes[domain]) > 10:
                    new_entry += f"- ... and {len(domain_changes[domain]) - 10} more\n"
                new_entry += "\n"
        
        new_entry += "\n"
    else:
        # Legacy format without domain grouping
        changes = []
        for f in files:
            if f:
                desc = categorize_file(f)
                if desc:
                    changes.append(desc)
        
        # Create entry
        new_entry = f"## [{version}] - {date_str}\n\n"
        new_entry += f"### Summary\n\n{commit_msg}\n\n"
        if changes:
            new_entry += "### Changes\n\n"
            for change in changes[:20]:  # Limit to 20 changes
                new_entry += f"- {change}\n"
            if len(changes) > 20:
                new_entry += f"- ... and {len(changes) - 20} more changes\n"
        new_entry += "\n"
    
    changelog_path.write_text(new_entry + existing_content)


def get_remote_branch() -> str:
    """Get the current branch name."""
    result = run_git('rev-parse', '--abbrev-ref', 'HEAD')
    return result.stdout.strip() if result.returncode == 0 else 'main'


def run_tests(project_types: List[str]) -> bool:
    """Run tests for detected project types."""
    def is_poetry_project() -> bool:
        if Path('poetry.lock').exists():
            return True
        pyproject = Path('pyproject.toml')
        if not pyproject.exists():
            return False
        try:
            content = pyproject.read_text(errors='ignore')
        except Exception:
            return False
        return ('[tool.poetry]' in content) or ('[tool.poetry.dependencies]' in content)

    def wrap_python_test_cmd(cmd: str) -> str:
        """Run pytest in the repo's intended environment (Poetry / .venv) instead of the active shell venv."""
        if 'pytest' not in cmd:
            return cmd

        if is_poetry_project() and shutil.which('poetry'):
            return f"poetry run {cmd}"

        # Prefer the currently active environment over a hardcoded .venv path.
        # This prevents running tests with a stale/unrelated .venv.
        python_bin: Optional[Path] = None
        venv_env = os.environ.get('VIRTUAL_ENV')
        if venv_env:
            candidate = Path(venv_env) / 'bin' / 'python'
            if candidate.exists() and candidate.is_file():
                python_bin = candidate

        if python_bin is None:
            try:
                candidate = Path(sys.executable)
                if candidate.exists() and candidate.is_file():
                    python_bin = candidate
            except Exception:
                python_bin = None

        if python_bin is not None:
            if cmd.strip() == 'pytest':
                return f"{python_bin} -m pytest"
            return f"{python_bin} -m {cmd}"

        return cmd

    def wrap_install_cmd(cmd: str) -> str:
        if is_poetry_project() and shutil.which('poetry'):
            return f"poetry run {cmd}"
        return cmd

    def ensure_pytest_available(test_cmd: str) -> bool:
        test_cmd = (test_cmd or '').strip()
        if not test_cmd:
            return True
        if 'pytest' not in test_cmd:
            return True

        check_cmd = None
        install_cmd = None

        if test_cmd.startswith('poetry run '):
            check_cmd = 'poetry run python -c "import pytest"'
            install_cmd = 'poetry run python -m pip install --upgrade pytest'
        else:
            try:
                parts = shlex.split(test_cmd)
            except Exception:
                parts = test_cmd.split()

            python_bin = None
            if len(parts) >= 3 and parts[1:3] == ['-m', 'pytest']:
                python_bin = parts[0]

            if python_bin:
                check_cmd = f'{python_bin} -c "import pytest"'
                install_cmd = f'{python_bin} -m pip install --upgrade pytest'
            else:
                check_cmd = 'python -c "import pytest"'
                install_cmd = 'python -m pip install --upgrade pytest'

        probe = run_command(check_cmd, capture=True)
        if probe.returncode == 0:
            return True

        click.echo(click.style("pytest is missing in the selected test environment.", fg='yellow'))
        if confirm("Install pytest now?", default=True):
            click.echo(f"{click.style('Preparing tests:', fg='cyan', bold=True)} {install_cmd}")
            result = run_command(install_cmd, capture=False)
            if result.returncode != 0:
                return False
        return True

    def has_pytest_cov() -> bool:
        if is_poetry_project() and shutil.which('poetry'):
            result = run_command('poetry run python -c "import pytest_cov"', capture=True)
            return result.returncode == 0

        venv_python = Path('.venv/bin/python')
        if venv_python.exists() and venv_python.is_file():
            result = run_command(f'{venv_python} -c "import pytest_cov"', capture=True)
            return result.returncode == 0

        return importlib.util.find_spec('pytest_cov') is not None

    def project_uses_cov_options() -> bool:
        for p in ('pyproject.toml', 'pytest.ini', 'setup.cfg', 'tox.ini'):
            path = Path(p)
            if not path.exists() or not path.is_file():
                continue
            try:
                content = path.read_text(errors='ignore')
            except Exception:
                continue
            if '--cov' in content:
                return True
        return False

    for ptype in project_types:
        if ptype in PROJECT_TYPES and 'test_command' in PROJECT_TYPES[ptype]:
            cmd = wrap_python_test_cmd(PROJECT_TYPES[ptype]['test_command'])

            if 'pytest' in cmd:
                if not ensure_pytest_available(cmd):
                    return False

            if 'pytest' in cmd and project_uses_cov_options():
                if not has_pytest_cov():
                    click.echo(click.style("pytest-cov is missing but this project appears to use --cov options.", fg='yellow'))
                    if confirm("Install pytest-cov now?", default=True):
                        install_cmd = wrap_install_cmd('python -m pip install --upgrade pytest-cov')
                        click.echo(f"{click.style('Preparing tests:', fg='cyan', bold=True)} {install_cmd}")
                        result = run_command(install_cmd, capture=False)
                        if result.returncode != 0:
                            return False
            click.echo(f"\n{click.style('Running tests:', fg='cyan', bold=True)} {cmd}")
            result = run_command(cmd, capture=False)
            if result.returncode == 0:
                return True

            if 'pytest' in cmd and result.returncode == 5:
                click.echo(click.style("No tests collected (pytest exit code 5). Continuing.", fg='yellow'))
                return True

            return False
    
    click.echo(click.style("\nNo test command configured for this project type", fg='yellow'))
    return True


def get_registry_help(project_type: str) -> str:
    """Get help message for configuring registry authentication."""
    help_messages = {
        'nodejs': """
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📦 npm Registry Configuration                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ To publish to npm, you need to authenticate:                                │
│                                                                             │
│ Option 1: Interactive login                                                 │
│   $ npm login                                                               │
│                                                                             │
│ Option 2: Use automation token (recommended for CI/CD)                      │
│   1. Create token at: https://www.npmjs.com/settings/tokens                 │
│   2. Set environment variable:                                              │
│      $ export NPM_TOKEN="npm_xxxxxxxx"                                      │
│   3. Create .npmrc in project root:                                         │
│      //registry.npmjs.org/:_authToken=${NPM_TOKEN}                          │
│                                                                             │
│ Configure in goal.yaml:                                                     │
│   registries:                                                               │
│     npm:                                                                    │
│       url: "https://registry.npmjs.org/"                                    │
│       token_env: "NPM_TOKEN"                                                │
│                                                                             │
│ For scoped packages (@org/package):                                         │
│   $ npm publish --access public                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""",
        'python': """
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🐍 PyPI Registry Configuration                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ To publish to PyPI, you need to authenticate:                               │
│                                                                             │
│ Option 1: Use API token (recommended)                                       │
│   1. Create token at: https://pypi.org/manage/account/token/               │
│   2. Create ~/.pypirc:                                                      │
│      [pypi]                                                                 │
│      username = __token__                                                   │
│      password = pypi-xxxxxxxx                                               │
│                                                                             │
│ Option 2: Environment variable                                              │
│   $ export TWINE_USERNAME=__token__                                         │
│   $ export TWINE_PASSWORD=pypi-xxxxxxxx                                     │
│                                                                             │
│ Configure in goal.yaml:                                                     │
│   registries:                                                               │
│     pypi:                                                                   │
│       url: "https://pypi.org/simple/"                                       │
│       token_env: "PYPI_TOKEN"                                               │
│                                                                             │
│ For Test PyPI (testing):                                                    │
│   $ twine upload --repository testpypi dist/*                               │
└─────────────────────────────────────────────────────────────────────────────┘
""",
        'rust': """
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🦀 crates.io Registry Configuration                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ To publish to crates.io, you need to authenticate:                          │
│                                                                             │
│ 1. Get API token at: https://crates.io/settings/tokens                     │
│ 2. Login with cargo:                                                        │
│    $ cargo login <your-token>                                               │
│                                                                             │
│ Or use environment variable:                                                │
│    $ export CARGO_REGISTRY_TOKEN=<your-token>                               │
│                                                                             │
│ Configure in goal.yaml:                                                     │
│   registries:                                                               │
│     cargo:                                                                  │
│       url: "https://crates.io/"                                             │
│       token_env: "CARGO_REGISTRY_TOKEN"                                     │
└─────────────────────────────────────────────────────────────────────────────┘
""",
        'ruby': """
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💎 RubyGems Registry Configuration                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ To publish to RubyGems, you need to authenticate:                           │
│                                                                             │
│ 1. Get API key at: https://rubygems.org/profile/api_keys                   │
│ 2. Create ~/.gem/credentials:                                               │
│    ---                                                                      │
│    :rubygems_api_key: rubygems_xxxxxxxx                                     │
│                                                                             │
│ Or use environment variable:                                                │
│    $ export GEM_HOST_API_KEY=rubygems_xxxxxxxx                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""
    }
    return help_messages.get(project_type, f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📦 Registry Configuration                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Publishing failed. Please configure your registry authentication.           │
│                                                                             │
│ Check goal.yaml registries section for configuration options:              │
│   $ goal config show -k registries                                          │
│                                                                             │
│ Common environment variables:                                               │
│   - NPM_TOKEN: npm registry token                                           │
│   - PYPI_TOKEN: PyPI API token                                              │
│   - CARGO_REGISTRY_TOKEN: crates.io token                                   │
└─────────────────────────────────────────────────────────────────────────────┘
""")


def publish_project(project_types: List[str], version: str) -> bool:
    """Publish project for detected project types."""
    import sys
    for ptype in project_types:
        if ptype in PROJECT_TYPES and 'publish_command' in PROJECT_TYPES[ptype]:
            if ptype == 'python':
                package_name = None
                pyproject_path = Path('pyproject.toml')
                if pyproject_path.exists():
                    try:
                        try:
                            import tomllib
                        except ModuleNotFoundError:
                            tomllib = None
                        if tomllib is not None:
                            data = tomllib.loads(pyproject_path.read_text())
                            package_name = (
                                (data.get('project') or {}).get('name')
                                or ((data.get('tool') or {}).get('poetry') or {}).get('name')
                            )
                    except Exception:
                        package_name = None

                name_variants = set()
                if package_name:
                    base = package_name.strip()
                    if base:
                        name_variants.update(
                            {
                                base,
                                base.lower(),
                                base.replace('-', '_'),
                                base.replace('-', '_').lower(),
                                base.replace('_', '-'),
                                base.replace('_', '-').lower(),
                            }
                        )

                build_dir = Path('build')
                if build_dir.exists():
                    shutil.rmtree(build_dir)

                dist = Path('dist')
                if dist.exists():
                    for f in dist.iterdir():
                        if not f.is_file():
                            continue
                        if not (f.name.endswith('.whl') or f.name.endswith('.tar.gz')):
                            continue
                        if name_variants:
                            if not any(
                                f.name.startswith(f"{n}-")
                                for n in name_variants
                            ):
                                continue
                        try:
                            f.unlink()
                        except OSError:
                            pass

                missing = [
                    m for m in ('build', 'twine')
                    if importlib.util.find_spec(m) is None
                ]
                if missing:
                    cmd = 'python -m pip install --upgrade build twine'
                    click.echo(f"\n{click.style('Preparing publish:', fg='cyan', bold=True)} {cmd}")
                    sys.stdout.flush()
                    result = run_command(cmd, capture=False)
                    sys.stdout.flush()
                    if result.returncode != 0:
                        click.echo("")
                        click.echo(click.style("Failed to install build dependencies.", fg='red'))
                        return False

                cmd = 'python -m build'
                click.echo(f"\n{click.style('Publishing:', fg='cyan', bold=True)} {cmd}")
                sys.stdout.flush()
                result = run_command(cmd, capture=False)

                if result.returncode != 0:
                    sys.stdout.flush()
                    click.echo("")
                    click.echo(click.style("Build failed. Check the output above.", fg='red'))
                    return False

                artifacts = []
                if dist.exists():
                    for f in dist.iterdir():
                        if not f.is_file():
                            continue
                        if not (f.name.endswith('.whl') or f.name.endswith('.tar.gz')):
                            continue

                        dist_name = None
                        dist_version = None
                        if f.name.endswith('.whl'):
                            stem = f.name[:-len('.whl')]
                            parts = stem.split('-')
                            if len(parts) >= 2:
                                dist_name = parts[0]
                                dist_version = parts[1]
                        else:
                            stem = f.name[:-len('.tar.gz')]
                            if '-' in stem:
                                dist_name, dist_version = stem.rsplit('-', 1)

                        if not dist_name or not dist_version:
                            continue
                        if dist_version != version:
                            continue

                        if name_variants:
                            norm = dist_name.replace('_', '-').lower()
                            allowed = {n.replace('_', '-').lower() for n in name_variants}
                            if norm not in allowed:
                                continue

                        artifacts.append(f)

                artifacts = sorted({str(a) for a in artifacts})
                if not artifacts:
                    click.echo(click.style(f"No dist artifacts found for version {version}", fg='red'))
                    if dist.exists():
                        dist_listing = sorted(p.name for p in dist.iterdir() if p.is_file())
                        if dist_listing:
                            click.echo(click.style("Dist directory contains:", fg='yellow'))
                            for name in dist_listing[:20]:
                                click.echo(f"  - {name}")
                    return False

                cmd = 'python -m twine upload ' + ' '.join(artifacts)
                click.echo(f"\n{click.style('Publishing:', fg='cyan', bold=True)} {cmd}")
                sys.stdout.flush()
                result = run_command_tee(cmd)
            else:
                cmd = PROJECT_TYPES[ptype]['publish_command']
                try:
                    cmd = cmd.format(version=version)
                except Exception:
                    pass
                click.echo(f"\n{click.style('Publishing:', fg='cyan', bold=True)} {cmd}")
                sys.stdout.flush()
                result = run_command_tee(cmd)
            sys.stdout.flush()
            
            if result.returncode != 0:
                out = ((result.stdout or '') + "\n" + (result.stderr or '')).strip()
                out_l = strip_ansi(out).lower()

                click.echo("")
                click.echo(click.style("=" * 77, fg='yellow'))
                if re.search(r'file[^a-z0-9]+already[^a-z0-9]+exists', out_l) is not None:
                    click.echo(click.style("⚠️  PUBLISH FAILED - File already exists", fg='yellow', bold=True))
                    click.echo(click.style("=" * 77, fg='yellow'))
                    click.echo(click.style("This version (or filename) already exists in the registry.", fg='yellow'))
                    click.echo(click.style("Bump the version and try again.", fg='yellow'))
                else:
                    auth_indicators = (
                        'unauthorized',
                        'forbidden',
                        'invalid or non-existent authentication',
                        'missing or invalid authentication',
                        '403',
                        '401',
                        'invalid token',
                    )
                    if any(x in out_l for x in auth_indicators):
                        click.echo(click.style("⚠️  PUBLISH FAILED - Authentication Required", fg='yellow', bold=True))
                        click.echo(click.style("=" * 77, fg='yellow'))
                        click.echo(get_registry_help(ptype))
                    else:
                        click.echo(click.style("⚠️  PUBLISH FAILED", fg='yellow', bold=True))
                        click.echo(click.style("=" * 77, fg='yellow'))
                click.echo(click.style("=" * 77, fg='yellow'))
                return False
            
            return True
    
    click.echo(click.style("\nNo publish command configured for this project type", fg='yellow'))
    return True


@click.group(invoke_without_command=True)
@click.version_option()
@click.option('--bump', '-b', type=click.Choice(['patch', 'minor', 'major']), default='patch',
              help='Version bump type (default: patch)')
@click.option('--yes', '-y', is_flag=True, help='Skip all prompts (run automatically)')
@click.option('--all', '-a', is_flag=True, help='Automate all stages including tests, commit, push, and publish')
@click.option('--markdown/--ascii', default=True, help='Output format (default: markdown)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
@click.option('--config', '-c', 'config_path', type=click.Path(), default=None,
              help='Path to goal.yaml config file')
@click.option('--abstraction', type=click.Choice(['auto', 'high', 'medium', 'low', 'legacy']), 
              default='auto', help='Commit message abstraction level (default: auto)')
@click.pass_context
def main(ctx, bump, yes, all, markdown, dry_run, config_path, abstraction):
    """Goal - Automated git push with smart commit messages."""
    # Store output preference in context
    ctx.ensure_object(dict)
    ctx.obj['markdown'] = markdown
    ctx.obj['config_path'] = config_path
    ctx.obj['abstraction'] = abstraction
    
    # Load configuration (creates goal.yaml if it doesn't exist)
    try:
        if config_path:
            ctx.obj['config'] = load_config(config_path)
        else:
            ctx.obj['config'] = ensure_config()
    except Exception:
        ctx.obj['config'] = None
    
    if ctx.invoked_subcommand is None:
        # Run interactive push by default
        if all:
            ctx.invoke(push, bump=bump, yes=True, markdown=markdown, dry_run=dry_run, abstraction=abstraction)
        else:
            ctx.invoke(push, bump=bump, yes=yes, markdown=markdown, dry_run=dry_run, abstraction=abstraction)


@main.command()
@click.option('--bump', '-b', type=click.Choice(['patch', 'minor', 'major']), default='patch',
              help='Version bump type (default: patch)')
@click.option('--no-tag', is_flag=True, help='Skip creating git tag')
@click.option('--no-changelog', is_flag=True, help='Skip updating changelog')
@click.option('--no-version-sync', is_flag=True, help='Skip syncing version to project files')
@click.option('--message', '-m', help='Custom commit message (overrides auto-generation)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
@click.option('--yes', '-y', is_flag=True, help='Skip all prompts (run automatically)')
@click.option('--markdown/--ascii', default=True, help='Output format (default: markdown)')
@click.option('--split', is_flag=True, help='Create separate commits per change type (docs/code/ci/examples)')
@click.option('--ticket', help='Ticket prefix to include in commit titles (overrides TICKET)')
@click.option('--abstraction', type=click.Choice(['auto', 'high', 'medium', 'low', 'legacy']), 
              default='auto', help='Commit message abstraction level')
@click.pass_context
def push(ctx, bump, no_tag, no_changelog, no_version_sync, message, dry_run, yes, markdown, split, ticket, abstraction):
    """Add, commit, tag, and push changes to remote.
    
    Automatically:
    - Generates smart commit messages based on diff analysis
    - Updates VERSION file and syncs to package.json, pyproject.toml, etc.
    - Updates CHANGELOG.md with changes
    - Creates git tag
    - Pushes to remote
    """
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        result = run_git('rev-parse', '--git-dir')
        if result.returncode != 0:
            click.echo(click.style("Error: Not a git repository", fg='red'))
            sys.exit(1)
    
    # Detect project types
    project_types = detect_project_types()
    if project_types and not dry_run:
        click.echo(f"Detected project types: {click.style(', '.join(project_types), fg='cyan')}")
    
    # Stage all changes
    if not dry_run:
        run_git('add', '-A')
    
    # Get staged files
    files = get_staged_files()
    if not files or files == ['']:
        if markdown or ctx.obj.get('markdown'):
            current_version = get_current_version()
            md_output = format_push_result(
                project_types=project_types or [],
                files=[],
                stats={},
                current_version=current_version,
                new_version=current_version,
                commit_msg="(none)",
                commit_body="No staged changes detected.",
                test_result="Not executed",
                test_exit_code=0,
                actions=["Detected project types"],
                error="No changes to commit"
            )
            click.echo(md_output)
        else:
            click.echo(click.style("No changes to commit.", fg='yellow'))
        return
    
    # Get diff content for smart analysis
    diff_content = get_diff_content()
    
    # Generate or use provided commit message
    commit_title = None
    commit_body = None
    detailed_result = None
    if message:
        commit_title = apply_ticket_prefix(message, ticket)
    else:
        # Get config from context for smart abstraction
        config_obj = ctx.obj.get('config')
        config_dict = config_obj.to_dict() if config_obj else None
        generator = CommitMessageGenerator(config=config_dict)

        use_enhanced = bool((config_dict or {}).get('quality', {}).get('enhanced_summary', {}).get('enabled', False))
        if use_enhanced:
            detailed = generator.generate_detailed_message(cached=True)
            if detailed and detailed.get('enhanced'):
                detailed_result = detailed
                commit_title = apply_ticket_prefix(detailed.get('title'), ticket)
                commit_body = detailed.get('body')
        
        # Use abstraction-based generation if available
        if not commit_title and abstraction != 'legacy' and config_dict:
            abstraction_result = generator.generate_abstraction_message(level=abstraction, cached=True)
            if abstraction_result:
                commit_title = apply_ticket_prefix(abstraction_result.get('title'), ticket)
                commit_body = abstraction_result.get('body')
            else:
                detailed = generator.generate_detailed_message(cached=True)
                if detailed:
                    detailed_result = detailed
                    commit_title = apply_ticket_prefix(detailed.get('title'), ticket)
                    commit_body = detailed.get('body')
        elif not commit_title:
            detailed = generator.generate_detailed_message(cached=True)
            if detailed:
                detailed_result = detailed
                commit_title = apply_ticket_prefix(detailed.get('title'), ticket)
                commit_body = detailed.get('body')
            else:
                commit_title = apply_ticket_prefix(generate_smart_commit_message(files, diff_content), ticket)
        if not commit_title:
            click.echo(click.style("No changes to commit.", fg='yellow'))
            return

    commit_msg = commit_title
    
    # Get version info
    current_version = get_current_version()
    new_version = bump_version(current_version, bump)
    
    # Get diff stats for display
    stats = get_diff_stats()
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())

    quality_enforced = False

    # Enforce commit quality gates for auto-generated messages
    if not message and detailed_result and detailed_result.get('enhanced'):
        config_obj = ctx.obj.get('config')
        config_dict = config_obj.to_dict() if config_obj else {}
        quality_cfg = (config_dict or {}).get('quality', {}).get('enhanced_summary', {})
        enforce_quality = bool(quality_cfg.get('enabled', True))

        if enforce_quality:
            try:
                from .enhanced_summary import QualityValidator
            except ImportError:
                from enhanced_summary import QualityValidator

            try:
                validator = QualityValidator(config_dict or {})

                # Validate the actual commit message we are about to use
                summary_for_validation = dict(detailed_result)
                summary_for_validation['title'] = commit_msg
                summary_for_validation['intent'] = detailed_result.get('intent')
                summary_for_validation.setdefault('metrics', {})
                summary_for_validation['metrics'].setdefault('lines_added', total_adds)
                summary_for_validation['metrics'].setdefault('lines_deleted', total_dels)

                validation = validator.validate(summary_for_validation, detailed_result.get('files') or files)
                if not validation.get('valid', True):
                    suggested = validator.auto_fix(summary_for_validation, files, total_adds, total_dels)

                    suggested_title = (suggested or {}).get('title')
                    if suggested_title and suggested_title.strip() and suggested_title != commit_msg:
                        apply_fix = True
                        if not yes:
                            apply_fix = confirm(f"Apply suggested title?\n\nCurrent: {commit_msg}\nSuggested: {suggested_title}")

                        if apply_fix:
                            commit_msg = suggested_title
                            summary_for_validation['title'] = commit_msg
                            validation = validator.validate(
                                summary_for_validation,
                                detailed_result.get('files') or files,
                            )
                            if validation.get('valid', True):
                                if markdown or ctx.obj.get('markdown'):
                                    click.echo(f"\n- **Applied title fix:** `{commit_msg}`")
                                else:
                                    click.echo(click.style(f"\n✓ Applied title fix: {commit_msg}", fg='green'))
                            else:
                                if markdown or ctx.obj.get('markdown'):
                                    click.echo("\n## ❌ FAILED QUALITY GATES\n")
                                    click.echo(f"- **Score:** {validation.get('score', 0)}/100")
                                    click.echo("\n### Errors")
                                    for e in validation.get('errors', []):
                                        click.echo(f"- {e}")
                                    if validation.get('warnings'):
                                        click.echo("\n### Warnings")
                                        for w in validation.get('warnings', []):
                                            click.echo(f"- {w}")
                                else:
                                    click.echo(click.style("\n❌ FAILED QUALITY GATES", fg='red', bold=True))
                                    click.echo(f"Score: {validation.get('score', 0)}/100\n")
                                    for e in validation.get('errors', []):
                                        click.echo(f"  ✗ {e}")
                                    if validation.get('warnings'):
                                        click.echo("")
                                        for w in validation.get('warnings', []):
                                            click.echo(f"  ⚠ {w}")
                                sys.exit(1)
                        else:
                            if markdown or ctx.obj.get('markdown'):
                                click.echo("\n### Suggested Fix")
                                click.echo(f"- **Title:** `{suggested_title}`")
                                click.echo("\n💡 Run: `goal validate --fix` or `goal fix-summary --auto`")
                            else:
                                click.echo(click.style(f"Suggested title: {suggested_title}", fg='cyan'))
                                click.echo(click.style("Run: goal validate --fix OR goal fix-summary --auto", fg='cyan'))
                            sys.exit(1)

                    if validation.get('valid', True):
                        commit_title = commit_msg
                    else:
                        if markdown or ctx.obj.get('markdown'):
                            click.echo("\n## ❌ FAILED QUALITY GATES\n")
                            click.echo(f"- **Score:** {validation.get('score', 0)}/100")
                            click.echo("\n### Errors")
                            for e in validation.get('errors', []):
                                click.echo(f"- {e}")
                            if validation.get('warnings'):
                                click.echo("\n### Warnings")
                                for w in validation.get('warnings', []):
                                    click.echo(f"- {w}")
                            click.echo("\n### Suggested Fix")
                            click.echo(f"- **Title:** `{suggested.get('title', '')}`")
                            click.echo("\n💡 Run: `goal validate --fix` or `goal fix-summary --auto`")
                        else:
                            click.echo(click.style("\n❌ FAILED QUALITY GATES", fg='red', bold=True))
                            click.echo(f"Score: {validation.get('score', 0)}/100\n")
                            for e in validation.get('errors', []):
                                click.echo(f"  ✗ {e}")
                            if validation.get('warnings'):
                                click.echo("")
                                for w in validation.get('warnings', []):
                                    click.echo(f"  ⚠ {w}")
                            click.echo("")
                            click.echo(click.style(f"Suggested title: {suggested.get('title', '')}", fg='cyan'))
                            click.echo(click.style("Run: goal validate --fix OR goal fix-summary --auto", fg='cyan'))

                        sys.exit(1)

                quality_enforced = True
            except Exception:
                # If validation fails unexpectedly, do not block push
                pass
    
    if dry_run:
        # Split mode: show planned commits per group
        if split and not message:
            config_obj = ctx.obj.get('config')
            config_dict = config_obj.to_dict() if config_obj else None
            generator = CommitMessageGenerator(config=config_dict)
            groups = split_paths_by_type(files)
            plan_lines = []
            for gname in ['code', 'docs', 'ci', 'examples', 'other']:
                if gname not in groups:
                    continue
                d = generator.generate_detailed_message(cached=True, paths=groups[gname])
                if not d:
                    continue
                title = apply_ticket_prefix(d.get('title'), ticket)
                plan_lines.append(f"- {gname}: {title} ({len(groups[gname])} files)")
            if not no_version_sync or not no_changelog:
                plan_lines.append(f"- release: chore(release): bump to {bump_version(get_current_version(), bump)}")
            commit_body = (commit_body or '')
            commit_body = ("Planned split commits:\n" + "\n".join(plan_lines)).strip()

        if markdown or ctx.obj.get('markdown'):
            # Generate markdown output for dry run
            if detailed_result and detailed_result.get('enhanced'):
                md_output = format_enhanced_summary(
                    commit_title=commit_msg,
                    commit_body=commit_body or '',
                    capabilities=detailed_result.get('capabilities'),
                    roles=detailed_result.get('roles'),
                    relations=detailed_result.get('relations'),
                    metrics=detailed_result.get('metrics'),
                    files=files,
                    stats=stats,
                    current_version=current_version,
                    new_version=new_version
                )
            else:
                md_output = format_push_result(
                    project_types=project_types,
                    files=files,
                    stats=stats,
                    current_version=current_version,
                    new_version=new_version,
                    commit_msg=commit_msg,
                    commit_body=commit_body,
                    test_result="Dry run - tests not executed",
                    test_exit_code=0,
                    actions=[
                        "Detected project types",
                        "Staged changes",
                        "Generated commit message",
                        "Planned version bump",
                        "Planned changelog update",
                        "Planned tag creation",
                        "Planned push to remote"
                    ]
                )
            click.echo(md_output)
        else:
            click.echo(click.style("=== DRY RUN ===", fg='cyan', bold=True))
            if project_types:
                click.echo(f"Project types: {', '.join(project_types)}")
            click.echo(f"Files to commit: {len(files)} (+{total_adds}/-{total_dels} lines)")
            for f in files[:10]:
                stat = stats.get(f, (0, 0))
                click.echo(f"  - {f} (+{stat[0]}/-{stat[1]})")
            if len(files) > 10:
                click.echo(f"  ... and {len(files) - 10} more")
            click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
            click.echo(f"Version: {current_version} -> {new_version}")
            if not no_version_sync:
                click.echo("Version sync: VERSION, package.json, pyproject.toml, etc.")
            if not no_tag:
                click.echo(f"Tag: v{new_version}")
        return
    
    # Interactive workflow
    if not yes:
        if markdown or ctx.obj.get('markdown'):
            # Markdown preview for interactive mode
            click.echo(f"\n## GOAL Workflow Preview\n")
            denom = (total_adds + total_dels) or 1
            deletion_pct = int((total_dels / denom) * 100)
            net = total_adds - total_dels
            click.echo(
                f"- **Files:** {len(files)} (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)"
            )
            click.echo(f"- **Version:** {current_version} → {new_version}")
            click.echo(f"- **Commit:** `{commit_msg}`")
            if commit_body and not message:
                click.echo(f"\n### Commit Body\n```\n{commit_body}\n```")
        else:
            click.echo(click.style("\n=== GOAL Workflow ===", fg='cyan', bold=True))
            denom = (total_adds + total_dels) or 1
            deletion_pct = int((total_dels / denom) * 100)
            net = total_adds - total_dels
            click.echo(
                f"Will commit {len(files)} files (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)"
            )
            click.echo(f"Version bump: {current_version} -> {new_version}")
            click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
            if commit_body and not message:
                click.echo(click.style("\nCommit body (preview):", fg='cyan'))
                click.echo(commit_body)
    
    # Test stage
    test_result = None
    test_exit_code = 0
    
    if not yes:
        if confirm("Run tests?"):
            click.echo(click.style("\nRunning tests...", fg='cyan'))
            test_success = run_tests(project_types)
            if not test_success:
                test_exit_code = 1
                if not confirm("Tests failed. Continue anyway?", default=False):
                    # Output markdown if requested
                    if markdown or ctx.obj.get('markdown'):
                        md_output = format_push_result(
                            project_types=project_types,
                            files=files,
                            stats=stats,
                            current_version=current_version,
                            new_version=new_version,
                            commit_msg=commit_msg,
                            commit_body=commit_body,
                            test_result="Tests failed - aborted by user",
                            test_exit_code=1,
                            actions=["Detected project types", "Staged changes", "Attempted to run tests"],
                            error="User aborted due to test failures"
                        )
                        click.echo(md_output)
                    click.echo(click.style("Aborted.", fg='red'))
                    sys.exit(1)
        else:
            click.echo(click.style("Skipping tests.", fg='yellow'))
    else:
        # When --yes or --all is used, run tests automatically
        click.echo(click.style("\nRunning tests...", fg='cyan'))
        test_success = run_tests(project_types)
        if not test_success:
            test_exit_code = 1
            test_result = "Tests failed - aborting"
            if markdown or ctx.obj.get('markdown'):
                md_output = format_push_result(
                    project_types=project_types,
                    files=files,
                    stats=stats,
                    current_version=current_version,
                    new_version=new_version,
                    commit_msg=commit_msg,
                    commit_body=commit_body,
                    test_result=test_result,
                    test_exit_code=test_exit_code,
                    actions=["Detected project types", "Staged changes", "Ran tests automatically"],
                    error="Tests failed - automatic abort"
                )
                click.echo(md_output)
            click.echo(click.style("Tests failed!", fg='red'))
            sys.exit(1)
    
    # Commit stage
    if not yes:
        if not confirm("Commit changes?"):
            click.echo(click.style("Aborted.", fg='red'))
            sys.exit(1)

    # Split commits per group if requested (single push at end)
    if split and not message:
        config_obj = ctx.obj.get('config')
        config_dict = config_obj.to_dict() if config_obj else None
        generator = CommitMessageGenerator(config=config_dict)
        # Unstage everything first, then stage/commit per group
        run_git('reset')
        groups = split_paths_by_type(files)

        if not yes:
            click.echo(click.style("\nSplit commits plan:", fg='cyan', bold=True))
            for gname in ['code', 'docs', 'ci', 'examples', 'other']:
                if gname in groups:
                    d = generator.generate_detailed_message(cached=False, paths=groups[gname])
                    title = apply_ticket_prefix(d.get('title'), ticket) if d else gname
                    click.echo(f"- {gname}: {title} ({len(groups[gname])} files)")

        # Commit each group
        for gname in ['code', 'docs', 'ci', 'examples', 'other']:
            if gname not in groups:
                continue

            stage_paths(groups[gname])
            d = generator.generate_detailed_message(cached=True, paths=groups[gname])
            if not d:
                continue
            title = apply_ticket_prefix(d.get('title'), ticket)
            body = d.get('body')
            result = run_git('commit', '-m', title, '-m', body)
            if result.returncode != 0:
                click.echo(click.style(f"Error committing split group {gname}: {result.stderr}", fg='red'))
                sys.exit(1)
            click.echo(click.style(f"✓ Committed ({gname}): {title}", fg='green'))

        # Release meta commit: version sync + changelog
        if (not no_version_sync) or (not no_changelog):
            # Sync versions to all project files
            if not no_version_sync:
                updated_files = sync_all_versions(new_version)
                stage_paths(updated_files)
                for f in updated_files:
                    click.echo(click.style(f"✓ Updated {f} to {new_version}", fg='green'))
            else:
                Path('VERSION').write_text(new_version + '\n')
                stage_paths(['VERSION'])
                click.echo(click.style(f"✓ Updated VERSION to {new_version}", fg='green'))

            if not no_changelog:
                config_obj = ctx.obj.get('config')
                config_dict = config_obj.to_dict() if config_obj else None
                update_changelog(new_version, files, commit_msg, config=config_dict)
                stage_paths(['CHANGELOG.md'])
                click.echo(click.style(f"✓ Updated CHANGELOG.md", fg='green'))

            release_title = apply_ticket_prefix(f"chore(release): bump version to {new_version}", ticket)
            release_body = f"Release metadata\n\nVersion: {current_version} -> {new_version}"\
                + ("\nChangelog: updated" if not no_changelog else "")
            result = run_git('commit', '-m', release_title, '-m', release_body)
            if result.returncode != 0:
                click.echo(click.style(f"Error committing release metadata: {result.stderr}", fg='red'))
                sys.exit(1)
            click.echo(click.style(f"✓ Committed (release): {release_title}", fg='green'))

        # Continue with tagging/pushing/publishing below
        # (Skip the single-commit path)
        commit_body = None
        message = "__split__"  # sentinel to skip single commit section
    
    # Sync versions to all project files
    if not no_version_sync:
        updated_files = sync_all_versions(new_version)
        for f in updated_files:
            run_git('add', f)
            click.echo(click.style(f"✓ Updated {f} to {new_version}", fg='green'))
    else:
        # Just update VERSION file
        Path('VERSION').write_text(new_version + '\n')
        run_git('add', 'VERSION')
        click.echo(click.style(f"✓ Updated VERSION to {new_version}", fg='green'))
    
    # Update changelog
    if not no_changelog:
        config_obj = ctx.obj.get('config')
        config_dict = config_obj.to_dict() if config_obj else None
        update_changelog(new_version, files, commit_msg, config=config_dict)
        run_git('add', 'CHANGELOG.md')
        click.echo(click.style(f"✓ Updated CHANGELOG.md", fg='green'))
    
    # Commit
    if message == "__split__":
        result = subprocess.CompletedProcess(args=[], returncode=0)
    elif commit_body and not message:
        result = run_git('commit', '-m', commit_title, '-m', commit_body)
    else:
        result = run_git('commit', '-m', commit_msg)
    if result.returncode != 0:
        click.echo(click.style(f"Error committing: {result.stderr}", fg='red'))
        sys.exit(1)
    if message != "__split__":
        click.echo(click.style(f"✓ Committed: {commit_msg}", fg='green'))
    
    # Create tag
    tag_name = None
    if not no_tag:
        tag_name = f"v{new_version}"
        tag_exists = run_git('rev-parse', '-q', '--verify', f"refs/tags/{tag_name}")
        if tag_exists.returncode == 0:
            click.echo(click.style(f"Warning: Tag already exists: {tag_name}", fg='yellow'))
        else:
            result = run_git('tag', '-a', tag_name, '-m', f"Release {new_version}")
            if result.returncode != 0:
                click.echo(click.style(f"Warning: Could not create tag: {result.stderr}", fg='yellow'))
            else:
                click.echo(click.style(f"✓ Created tag: {tag_name}", fg='green'))
    
    # Push stage
    if not yes:
        if confirm("Push to remote?"):
            branch = get_remote_branch()
            result = run_git('push', 'origin', branch, capture=False)
            
            if result.returncode != 0:
                click.echo(click.style("Error pushing to remote", fg='red'))
                sys.exit(1)

            if (not no_tag) and tag_name:
                result = run_git('push', 'origin', tag_name, capture=False)
                if result.returncode != 0:
                    click.echo(click.style("Error pushing tag to remote", fg='red'))
                    sys.exit(1)
            
            click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
        else:
            click.echo(click.style("Skipping push.", fg='yellow'))
    else:
        # Auto-push
        branch = get_remote_branch()
        result = run_git('push', 'origin', branch, capture=False)
        
        if result.returncode != 0:
            click.echo(click.style("Error pushing to remote", fg='red'))
            sys.exit(1)

        if (not no_tag) and tag_name:
            result = run_git('push', 'origin', tag_name, capture=False)
            if result.returncode != 0:
                click.echo(click.style("Error pushing tag to remote", fg='red'))
                sys.exit(1)
        
        click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
    
    # Publish stage
    if not yes:
        if confirm(f"Publish version {new_version}?"):
            if not publish_project(project_types, new_version):
                click.echo(click.style("Publish failed. Check the output above.", fg='red'))
                sys.exit(1)
            click.echo(click.style(f"\n✓ Published version {new_version}", fg='green', bold=True))
        else:
            click.echo(click.style("Skipping publish.", fg='yellow'))
    else:
        # Auto-publish when --yes or --all is used
        click.echo(click.style(f"\nPublishing version {new_version}...", fg='cyan'))
        if not publish_project(project_types, new_version):
            click.echo(click.style("Publish failed. Check the output above.", fg='red'))
            sys.exit(1)
        click.echo(click.style(f"\n✓ Published version {new_version}", fg='green', bold=True))
    
    # Output markdown if requested
    if markdown or ctx.obj.get('markdown'):
        actions_performed = [
            "Detected project types",
            "Staged changes",
            "Ran tests" if test_exit_code == 0 else "Tests failed but continued",
            "Committed changes",
            f"Updated version to {new_version}",
            "Updated changelog",
            f"Created tag v{new_version}" if not no_tag else "Skipped tag creation",
            "Pushed to remote" if not no_tag else "Pushed to remote without tags",
            f"Published version {new_version}"
        ]
        
        md_output = format_push_result(
            project_types=project_types,
            files=files,
            stats=stats,
            current_version=current_version,
            new_version=new_version,
            commit_msg=commit_msg,
            commit_body=commit_body,
            test_result="Tests passed" if test_exit_code == 0 else "Tests failed but continued",
            test_exit_code=test_exit_code,
            actions=actions_performed
        )
        click.echo("\n" + md_output)


def makefile_has_target(target: str) -> bool:
    makefile = Path('Makefile')
    if not makefile.exists() or not makefile.is_file():
        return False
    try:
        content = makefile.read_text(errors='ignore')
    except Exception:
        return False
    return re.search(rf'^\s*{re.escape(target)}\s*:', content, re.MULTILINE) is not None


@main.command()
@click.option('--make/--no-make', 'use_make', default=True, help='Use Makefile publish target if available')
@click.option('--target', default='publish', help='Make target to run when using --make')
@click.option('--version', default=None, help='Version to publish when not using Makefile')
@click.pass_context
def publish(ctx, use_make, target, version):
    """Publish the current project (optionally using Makefile)."""
    project_types = detect_project_types()

    if use_make and shutil.which('make') and makefile_has_target(target):
        cmd = f"make {target}"
        click.echo(f"\n{click.style('Publishing:', fg='cyan', bold=True)} {cmd}")
        result = run_command_tee(cmd)
        if result.returncode != 0:
            sys.exit(result.returncode)
        return

    if version is None:
        version = get_current_version()

    if not publish_project(project_types, version):
        sys.exit(1)


@main.command()
@click.option('--markdown/--ascii', default=True, help='Output format (default: markdown)')
@click.pass_context
def status(ctx, markdown):
    """Show current git status and version info."""
    # Version
    version = get_current_version()
    
    # Branch
    branch = get_remote_branch()
    
    # Staged files
    staged = get_staged_files()
    
    # Unstaged files
    unstaged = get_unstaged_files()
    
    # Check if markdown is requested
    if markdown or ctx.obj.get('markdown'):
        md_output = format_status_output(
            version=version,
            branch=branch,
            staged_files=staged if staged and staged != [''] else [],
            unstaged_files=unstaged
        )
        click.echo(md_output)
    else:
        # Regular output
        click.echo(f"Version: {click.style(version, fg='cyan')}")
        click.echo(f"Branch: {click.style(branch, fg='cyan')}")
        
        if staged and staged != ['']:
            click.echo(f"\nStaged files ({len(staged)}):")
            for f in staged:
                click.echo(f"  {click.style('+', fg='green')} {f}")
        
        if unstaged:
            click.echo(f"\nUnstaged/untracked ({len(unstaged)}):")
            for f in unstaged[:10]:
                click.echo(f"  {click.style('?', fg='yellow')} {f}")
            if len(unstaged) > 10:
                click.echo(f"  ... and {len(unstaged) - 10} more")


@main.command()
@click.option('--detailed', '-d', is_flag=True, help='Generate detailed commit message with body')
@click.option('--unstaged', '-u', is_flag=True, help='Analyze unstaged changes instead of staged')
@click.option('--markdown/--ascii', default=True, help='Output format (default: markdown)')
@click.option('--ticket', help='Ticket prefix to include in commit title (overrides TICKET)')
@click.option('--abstraction', type=click.Choice(['auto', 'high', 'medium', 'low', 'legacy']), 
              default='auto', help='Commit message abstraction level')
@click.pass_context
def commit(ctx, detailed, unstaged, markdown, ticket, abstraction):
    """Generate a smart commit message for current changes."""
    # Get config from context for smart abstraction
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else None
    generator = CommitMessageGenerator(config=config_dict)
    
    if detailed:
        # Use abstraction-based generation if available
        if abstraction != 'legacy' and config_dict:
            result = generator.generate_abstraction_message(level=abstraction, cached=not unstaged)
        else:
            result = generator.generate_detailed_message(cached=not unstaged)
        if result:
            title = apply_ticket_prefix(result['title'], ticket)
            if markdown or ctx.obj.get('markdown'):
                output = f"```text\n{title}\n\n{result['body']}\n```"
                click.echo(output)
            else:
                click.echo(title)
                click.echo()
                click.echo(result['body'])
        else:
            click.echo(click.style("No changes to analyze.", fg='yellow'))
            sys.exit(1)
    else:
        msg = generator.generate_commit_message(cached=not unstaged, abstraction_level=abstraction)
        if msg:
            msg = apply_ticket_prefix(msg, ticket)
            if markdown or ctx.obj.get('markdown'):
                click.echo(f"```text\n{msg}\n```")
            else:
                click.echo(msg)
        else:
            click.echo(click.style("No changes to analyze.", fg='yellow'))
            sys.exit(1)


@main.command()
@click.option('--type', '-t', 'bump_type', type=click.Choice(['patch', 'minor', 'major']), default='patch',
              help='Version bump type')
def version(bump_type):
    """Show or bump version."""
    current = get_current_version()
    new = bump_version(current, bump_type)
    click.echo(f"Current: {current}")
    click.echo(f"Next ({bump_type}): {new}")


@main.command()
@click.option('--force', '-f', is_flag=True, help='Overwrite existing goal.yaml')
@click.pass_context
def init(ctx, force):
    """Initialize goal in current repository (creates VERSION, CHANGELOG.md, and goal.yaml)."""
    version_file = Path('VERSION')
    changelog_file = Path('CHANGELOG.md')
    config_file = Path('goal.yaml')
    
    # Detect existing version from project files
    detected_version = None
    if Path('package.json').exists():
        try:
            data = json.loads(Path('package.json').read_text())
            detected_version = data.get('version')
        except Exception:
            pass
    
    if not detected_version and Path('pyproject.toml').exists():
        content = Path('pyproject.toml').read_text()
        match = re.search(r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content, re.MULTILINE)
        if match:
            detected_version = match.group(1)
    
    initial_version = detected_version or "1.0.0"
    
    if not version_file.exists():
        version_file.write_text(initial_version + '\n')
        if detected_version:
            click.echo(click.style(f"✓ Created VERSION file ({initial_version}) - detected from project", fg='green'))
        else:
            click.echo(click.style(f"✓ Created VERSION file ({initial_version})", fg='green'))
    else:
        click.echo(f"VERSION exists: {version_file.read_text().strip()}")
    
    if not changelog_file.exists():
        changelog_file.write_text("""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
""")
        click.echo(click.style("✓ Created CHANGELOG.md", fg='green'))
    else:
        click.echo("CHANGELOG.md exists")
    
    # Create goal.yaml configuration
    if not config_file.exists() or force:
        config = init_config(force=force)
        if force and config_file.exists():
            click.echo(click.style("✓ Regenerated goal.yaml", fg='green'))
        else:
            click.echo(click.style("✓ Created goal.yaml with auto-detected settings", fg='green'))
        
        # Show detected settings
        project_name = config.get('project.name')
        project_types = config.get('project.type', [])
        if project_name:
            click.echo(f"  Project: {click.style(project_name, fg='cyan')}")
        if project_types:
            click.echo(f"  Types: {click.style(', '.join(project_types), fg='cyan')}")
    else:
        click.echo("goal.yaml exists (use --force to regenerate)")
    
    # Show detected project types
    project_types = detect_project_types()
    if project_types:
        click.echo(f"Detected project types: {click.style(', '.join(project_types), fg='cyan')}")
    
    click.echo(click.style("\n✓ Goal initialized!", fg='green', bold=True))


@main.command()
def info():
    """Show detailed project information and version status."""
    click.echo(click.style("=== Project Information ===", fg='cyan', bold=True))
    
    # Detect project types
    project_types = detect_project_types()
    if project_types:
        click.echo(f"Project types: {', '.join(project_types)}")
    else:
        click.echo("Project types: Unknown")
    
    # Current version
    version = get_current_version()
    click.echo(f"Current version: {click.style(version, fg='green')}")
    
    # Version files status
    click.echo(f"\n{click.style('Version files:', bold=True)}")
    
    version_files = [
        ('VERSION', Path('VERSION')),
        ('package.json', Path('package.json')),
        ('pyproject.toml', Path('pyproject.toml')),
        ('Cargo.toml', Path('Cargo.toml')),
        ('composer.json', Path('composer.json')),
        ('pom.xml', Path('pom.xml')),
    ]
    
    for name, path in version_files:
        if path.exists():
            if name == 'VERSION':
                ver = path.read_text().strip()
            elif name in ('package.json', 'composer.json'):
                try:
                    data = json.loads(path.read_text())
                    ver = data.get('version', 'not set')
                except Exception:
                    ver = 'error reading'
            elif name == 'pyproject.toml':
                content = path.read_text()
                match = re.search(r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content, re.MULTILINE)
                ver = match.group(1) if match else 'not set'
            elif name == 'Cargo.toml':
                content = path.read_text()
                match = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', content, re.MULTILINE)
                ver = match.group(1) if match else 'not set'
            elif name == 'pom.xml':
                content = path.read_text()
                match = re.search(r'<version>(\d+\.\d+\.\d+)</version>', content)
                ver = match.group(1) if match else 'not set'
            else:
                ver = 'unknown'
            
            status = click.style('✓', fg='green') if ver == version else click.style('⚠', fg='yellow')
            click.echo(f"  {status} {name}: {ver}")
    
    # Git info
    click.echo(f"\n{click.style('Git status:', bold=True)}")
    branch = get_remote_branch()
    click.echo(f"  Branch: {branch}")
    
    # Recent tags
    result = run_git('tag', '--sort=-version:refname')
    tags = result.stdout.strip().split('\n')[:5]
    if tags and tags[0]:
        click.echo(f"  Recent tags: {', '.join(tags)}")
    
    # Pending changes
    unstaged = get_unstaged_files()
    staged = get_staged_files()
    if unstaged or (staged and staged != ['']):
        total = len(unstaged) + (len(staged) if staged != [''] else 0)
        click.echo(f"  Pending changes: {total} files")


@main.group()
@click.pass_context
def config(ctx):
    """Manage goal.yaml configuration."""
    pass


@config.command('show')
@click.option('--key', '-k', default=None, help='Show specific config key (dot notation)')
@click.pass_context
def config_show(ctx, key):
    """Show current configuration."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = GoalConfig()
        cfg.load()
    
    if key:
        value = cfg.get(key)
        if value is not None:
            if isinstance(value, (dict, list)):
                import yaml
                click.echo(yaml.dump(value, default_flow_style=False))
            else:
                click.echo(value)
        else:
            click.echo(click.style(f"Key not found: {key}", fg='red'))
    else:
        import yaml
        click.echo(yaml.dump(cfg.to_dict(), default_flow_style=False, sort_keys=False))


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate goal.yaml configuration."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = GoalConfig()
        if not cfg.exists():
            click.echo(click.style("No goal.yaml found. Run 'goal init' first.", fg='yellow'))
            return
        cfg.load()
    
    errors = cfg.validate()
    if errors:
        click.echo(click.style("Configuration errors:", fg='red', bold=True))
        for error in errors:
            click.echo(click.style(f"  ✗ {error}", fg='red'))
        sys.exit(1)
    else:
        click.echo(click.style("✓ Configuration is valid", fg='green'))


@config.command('update')
@click.pass_context
def config_update(ctx):
    """Update goal.yaml based on project detection."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = GoalConfig()
        if not cfg.exists():
            click.echo(click.style("No goal.yaml found. Run 'goal init' first.", fg='yellow'))
            return
        cfg.load()
    
    if cfg.update_from_detection():
        cfg.save()
        click.echo(click.style("✓ Configuration updated with detected changes", fg='green'))
    else:
        click.echo("Configuration is up-to-date")


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value (dot notation key)."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = GoalConfig()
        if not cfg.exists():
            click.echo(click.style("No goal.yaml found. Run 'goal init' first.", fg='yellow'))
            return
        cfg.load()
    
    # Try to parse value as JSON for complex types
    try:
        import json
        parsed_value = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        parsed_value = value
    
    cfg.set(key, parsed_value)
    cfg.save()
    click.echo(click.style(f"✓ Set {key} = {value}", fg='green'))


@config.command('get')
@click.argument('key')
@click.pass_context
def config_get(ctx, key):
    """Get a configuration value (dot notation key)."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = GoalConfig()
        cfg.load()
    
    value = cfg.get(key)
    if value is not None:
        if isinstance(value, (dict, list)):
            import yaml
            click.echo(yaml.dump(value, default_flow_style=False))
        else:
            click.echo(value)
    else:
        click.echo(click.style(f"Key not found: {key}", fg='red'))
        sys.exit(1)


@main.command()
@click.option('--fix', '-f', is_flag=True, help='Auto-fix detected issues')
@click.option('--cached/--working-tree', 'cached', default=True, show_default=True,
               help='Validate staged (--cached) or unstaged working tree (--working-tree) changes')
@click.pass_context
def validate(ctx, fix, cached):
    """Validate commit summary against quality gates.
    
    Checks for:
    - Banned words in title (add, logging, formatting, etc.)
    - Generic nodes in dependency graph (base, utils)
    - Duplicate files and relations
    - Missing capabilities
    
    Use --fix to automatically correct issues.
    """
    try:
        from .enhanced_summary import QualityValidator, EnhancedSummaryGenerator
    except ImportError:
        from enhanced_summary import QualityValidator, EnhancedSummaryGenerator
    
    files = get_staged_files() if cached else get_working_tree_files()
    if not files or files == ['']:
        click.echo(click.style("No changes to validate.", fg='yellow'))
        return
    
    diff_content = get_diff_content(cached=cached)
    numstats = get_diff_stats(cached=cached)
    stats = {
        'added': sum(v[0] for v in numstats.values()),
        'deleted': sum(v[1] for v in numstats.values())
    }
    
    # Generate summary
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else {}
    
    generator = EnhancedSummaryGenerator(config_dict)
    summary = generator.generate_enhanced_summary(
        files, diff_content, 
        lines_added=stats['added'], 
        lines_deleted=stats['deleted']
    )
    
    # Validate
    validator = QualityValidator(config_dict)
    result = validator.validate(summary, files)
    
    if result['valid']:
        click.echo(click.style("✓ SUMMARY PASSED QUALITY GATES", fg='green', bold=True))
        click.echo(f"Score: {result['score']}/100")
        return
    
    # Show errors
    click.echo(click.style("❌ SUMMARY FAILED QUALITY GATES", fg='red', bold=True))
    click.echo(f"Score: {result['score']}/100\n")
    
    if result['errors']:
        click.echo(click.style("Errors:", fg='red'))
        for e in result['errors']:
            click.echo(f"  ✗ {e}")
    
    if result['warnings']:
        click.echo(click.style("\nWarnings:", fg='yellow'))
        for w in result['warnings']:
            click.echo(f"  ⚠ {w}")
    
    if fix:
        # Auto-fix
        click.echo(click.style("\n🔧 Auto-fixing issues...", fg='cyan'))
        fixed = validator.auto_fix(summary, files, stats['added'], stats['deleted'])
        
        click.echo(click.style("\nApplied fixes:", fg='green'))
        for f in fixed.get('applied_fixes', []):
            click.echo(f"  ✅ {f}")
        
        click.echo(click.style(f"\nFixed title: \"{fixed['title']}\"", fg='green', bold=True))
        click.echo(click.style("✓ SUMMARY APPROVED", fg='green', bold=True))
    else:
        click.echo(click.style("\n💡 Run: goal validate --fix", fg='cyan'))
        sys.exit(1)


@main.command('fix-summary')
@click.option('--auto', 'auto_fix', is_flag=True, help='Automatically fix all issues')
@click.option('--preview', '-p', is_flag=True, help='Preview fixes without applying')
@click.option('--cached/--working-tree', 'cached', default=True, show_default=True,
               help='Fix summary for staged (--cached) or unstaged working tree (--working-tree) changes')
@click.pass_context
def fix_summary(ctx, auto_fix, preview, cached):
    """Auto-fix commit summary quality issues.
    
    Fixes:
    - Removes banned words from title
    - Generates architecture-aware title
    - Filters generic nodes from dependency graph
    - Deduplicates files and relations
    - Reclassifies intent based on NET lines
    """
    try:
        from .enhanced_summary import QualityValidator, EnhancedSummaryGenerator
    except ImportError:
        from enhanced_summary import QualityValidator, EnhancedSummaryGenerator
    
    files = get_staged_files() if cached else get_working_tree_files()
    if not files or files == ['']:
        click.echo(click.style("No changes to fix.", fg='yellow'))
        return
    
    diff_content = get_diff_content(cached=cached)
    numstats = get_diff_stats(cached=cached)
    stats = {
        'added': sum(v[0] for v in numstats.values()),
        'deleted': sum(v[1] for v in numstats.values())
    }
    
    # Generate summary
    config_obj = ctx.obj.get('config')
    config_dict = config_obj.to_dict() if config_obj else {}
    
    generator = EnhancedSummaryGenerator(config_dict)
    summary = generator.generate_enhanced_summary(
        files, diff_content,
        lines_added=stats['added'],
        lines_deleted=stats['deleted']
    )
    
    validator = QualityValidator(config_dict)
    
    # Show original
    click.echo(click.style("=== BEFORE ===", fg='yellow'))
    click.echo(f"Title: {summary['title']}")
    click.echo(f"Intent: {summary.get('intent', 'unknown')}")
    
    # Fix
    fixed = validator.auto_fix(summary, files, stats['added'], stats['deleted'])
    
    # Show fixed
    click.echo(click.style("\n=== AFTER ===", fg='green'))
    click.echo(f"Title: {fixed['title']}")
    click.echo(f"Intent: {fixed.get('intent', 'unknown')}")
    
    if fixed.get('net_lines'):
        nl = fixed['net_lines']
        click.echo(f"NET lines: {nl['emoji']} {nl['description']}")
    
    click.echo(click.style("\nApplied fixes:", fg='cyan'))
    for f in fixed.get('applied_fixes', []):
        click.echo(f"  ✅ {f}")
    
    if preview:
        click.echo(click.style("\n(Preview mode - no changes applied)", fg='yellow'))
    else:
        click.echo(click.style("\n✓ SUMMARY FIXED", fg='green', bold=True))


if __name__ == '__main__':
    main()
