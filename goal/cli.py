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
    import nfo
    from nfo.terminal import TerminalSink
    _HAS_NFO = True
except ImportError:
    _HAS_NFO = False

try:
    from .formatter import format_push_result, format_status_output, format_enhanced_summary
    from .commit_generator import CommitMessageGenerator
    from .config import GoalConfig, ensure_config, init_config, load_config
    from .user_config import get_user_config, initialize_user_config, show_user_config
    from .version_validation import validate_project_versions, check_readme_badges, update_badge_versions, format_validation_results
    from .project_bootstrap import (
        detect_project_types_deep, bootstrap_all_projects, bootstrap_project,
        ensure_project_environment, find_existing_tests, scaffold_test,
    )
    from .project_doctor import diagnose_and_report, diagnose_project, DoctorReport
    from .git_ops import (
        run_git, run_command, run_command_tee, is_git_repository, validate_repo_url,
        clone_repository, ensure_git_repository, ensure_remote, get_remote_url,
        get_remote_branch, get_staged_files, get_unstaged_files, get_working_tree_files,
        get_diff_stats, get_diff_content, _run_git_verbose, _echo_cmd, list_remotes
    )
    from .git_ops import (
        run_git, run_command, run_command_tee, is_git_repository, validate_repo_url,
        clone_repository, ensure_git_repository, ensure_remote, get_remote_url,
        get_remote_branch, get_staged_files, get_unstaged_files, get_working_tree_files,
        get_diff_stats, get_diff_content, _run_git_verbose, _echo_cmd, list_remotes
    )
except ImportError:
    from formatter import format_push_result, format_status_output, format_enhanced_summary
    from commit_generator import CommitMessageGenerator
    from config import GoalConfig, ensure_config, init_config, load_config
    from user_config import get_user_config, initialize_user_config, show_user_config
    from version_validation import validate_project_versions, check_readme_badges, update_badge_versions, format_validation_results
    from project_bootstrap import (
        detect_project_types_deep, bootstrap_all_projects, bootstrap_project,
        ensure_project_environment, find_existing_tests, scaffold_test,
    )
    from project_doctor import diagnose_and_report, diagnose_project, DoctorReport
    from git_ops import (
        run_git, run_command, run_command_tee, is_git_repository, validate_repo_url,
        clone_repository, ensure_git_repository, ensure_remote, get_remote_url,
        get_remote_branch, get_staged_files, get_unstaged_files, get_working_tree_files,
        get_diff_stats, get_diff_content, _run_git_verbose, _echo_cmd, list_remotes
    )


def _setup_nfo_logging(nfo_format: str = "markdown", nfo_sink: str = ""):
    """Configure nfo logging for the goal CLI session."""
    if not _HAS_NFO:
        return
    sinks = [f"terminal:{nfo_format}"]
    if nfo_sink:
        sinks.append(nfo_sink)
    nfo.configure(
        name="goal",
        level=os.environ.get("NFO_LEVEL", "INFO"),
        sinks=sinks,
        propagate_stdlib=False,
        force=True,
    )


def _nfo_log_call(**kwargs):
    """Conditional @nfo.log_call — no-op decorator when nfo is not installed."""
    if _HAS_NFO:
        return nfo.log_call(**kwargs)
    def _passthrough(fn):
        return fn
    return _passthrough


# =============================================================================
# Documentation URL for unknown command handling
# =============================================================================

DOCS_URL = "https://github.com/wronai/goal#readme"


class GoalGroup(click.Group):
    """Custom Click Group that shows docs URL for unknown commands (like Poetry)."""
    
    def get_command(self, ctx, cmd_name):
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv
        # Unknown command - show helpful message with docs URL
        click.echo(click.style(f"The requested command {cmd_name} does not exist.\n", fg='red', bold=True))
        click.echo(click.style(f"Documentation: {DOCS_URL}", fg='cyan'))
        click.echo()
        click.echo(click.style("Available commands:", fg='cyan', bold=True))
        self.list_commands(ctx)
        ctx.exit(2)


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


@_nfo_log_call(level='INFO')
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


def update_project_metadata(filepath: Path, user_config) -> bool:
    """Update author and license in project files based on user config.
    
    Intelligently adds authors if not present, preserving existing authors.
    """
    if not user_config:
        return False
    
    try:
        author_name = user_config.get('author_name')
        author_email = user_config.get('author_email')
        license_id = user_config.get('license')
        license_classifier = user_config.get('license_classifier')
        
        if not all([author_name, author_email, license_id]):
            return False
        
        content = filepath.read_text()
        original_content = content
        
        # Update pyproject.toml
        if filepath.name == 'pyproject.toml':
            # Update license
            content = re.sub(
                r'^license\s*=\s*[{\[].*?[}\]]',
                f'license = {{text = "{license_id}"}}',
                content,
                flags=re.MULTILINE
            )
            content = re.sub(
                r'^license\s*=\s*["\'].*?["\']',
                f'license = "{license_id}"',
                content,
                flags=re.MULTILINE
            )
            
            # Smart author update - add if not present
            authors_match = re.search(r'authors\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if authors_match:
                existing_authors = authors_match.group(1)
                # Check if this author already exists
                if author_email not in existing_authors:
                    # Parse existing authors
                    author_entries = []
                    for line in existing_authors.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#'):
                            author_entries.append(line.rstrip(','))
                    
                    # Add new author in Poetry format (string, not table)
                    new_author = f'"{author_name} <{author_email}>"'
                    author_entries.append(new_author)
                    
                    # Rebuild authors list
                    authors_block = 'authors = [\n'
                    for entry in author_entries:
                        authors_block += f'    {entry},\n'
                    authors_block += ']'
                    
                    content = re.sub(
                        r'authors\s*=\s*\[.*?\]',
                        authors_block,
                        content,
                        flags=re.DOTALL
                    )
            
            # Update license classifier if present
            if license_classifier:
                content = re.sub(
                    r'"License :: OSI Approved :: .*?"',
                    f'"{license_classifier}"',
                    content
                )
        
        # Update package.json
        elif filepath.name == 'package.json':
            data = json.loads(content)
            new_author = f"{author_name} <{author_email}>"
            
            # Check if author field exists and is different
            if 'author' not in data or data['author'] != new_author:
                # If author exists but is different, create contributors array
                if 'author' in data and data['author'] and data['author'] != new_author:
                    if 'contributors' not in data:
                        data['contributors'] = []
                    if new_author not in data['contributors']:
                        data['contributors'].append(new_author)
                else:
                    data['author'] = new_author
            
            data['license'] = license_id
            content = json.dumps(data, indent=2) + '\n'
        
        # Update Cargo.toml
        elif filepath.name == 'Cargo.toml':
            # Update license
            content = re.sub(
                r'^license\s*=\s*".*?"',
                f'license = "{license_id}"',
                content,
                flags=re.MULTILINE
            )
            
            # Smart author update
            authors_match = re.search(r'^authors\s*=\s*\[(.*?)\]', content, re.MULTILINE | re.DOTALL)
            if authors_match:
                existing_authors = authors_match.group(1)
                new_author_entry = f'"{author_name} <{author_email}>"'
                
                if author_email not in existing_authors:
                    # Parse existing
                    author_list = [a.strip().rstrip(',') for a in existing_authors.split('\n') if a.strip()]
                    author_list.append(new_author_entry)
                    
                    authors_block = 'authors = [' + ', '.join(author_list) + ']'
                    content = re.sub(
                        r'^authors\s*=\s*\[.*?\]',
                        authors_block,
                        content,
                        flags=re.MULTILINE | re.DOTALL
                    )
        
        if content != original_content:
            filepath.write_text(content)
            return True
            
    except Exception:
        pass
    
    return False


def update_readme_metadata(user_config) -> bool:
    """Update license badges and author info in README.md based on user config."""
    if not user_config:
        return False
    
    readme_path = Path('README.md')
    if not readme_path.exists():
        return False
    
    try:
        author_name = user_config.get('author_name')
        author_email = user_config.get('author_email')
        license_id = user_config.get('license')
        license_name = user_config.get('license_name')
        
        if not all([author_name, author_email, license_id]):
            return False
        
        content = readme_path.read_text()
        original_content = content
        
        # Badge patterns for different licenses
        license_badges = {
            'Apache-2.0': '[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)',
            'MIT': '[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)',
            'GPL-3.0': '[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)',
            'BSD-3-Clause': '[![License: BSD-3](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)',
            'GPL-2.0': '[![License: GPL v2](https://img.shields.io/badge/License-GPLv2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)',
            'LGPL-3.0': '[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)',
            'AGPL-3.0': '[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)',
            'MPL-2.0': '[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)',
        }
        
        new_badge = license_badges.get(license_id, f'[![License]](https://img.shields.io/badge/License-{license_id}-blue.svg)')
        
        # Update license badges
        content = re.sub(
            r'\[!\[License[^\]]*\]\([^\)]+\)\]\([^\)]+\)',
            new_badge,
            content
        )
        
        # Update ## License section
        license_section_pattern = r'(## License\s*\n\s*\n)([^\n#]+)'
        if re.search(license_section_pattern, content):
            license_text = f'{license_name} - see [LICENSE](LICENSE) for details.'
            content = re.sub(
                license_section_pattern,
                rf'\1{license_text}',
                content
            )
        else:
            # Add License section if missing (before last line or ## Author if exists)
            if '## Author' in content:
                content = re.sub(
                    r'(## Author)',
                    f'## License\n\n{license_name} - see [LICENSE](LICENSE) for details.\n\n\\1',
                    content
                )
            else:
                # Add at the end
                content = content.rstrip() + f'\n\n## License\n\n{license_name} - see [LICENSE](LICENSE) for details.\n'
        
        # Update or add ## Author section
        author_section = f'## Author\n\nCreated by **{author_name}** - [{author_email}](mailto:{author_email})'
        
        if re.search(r'## Author', content):
            # Update existing
            content = re.sub(
                r'## Author\s*\n\s*\n[^\n#]+',
                author_section,
                content
            )
        else:
            # Add after License section or at the end
            if '## License' in content:
                content = re.sub(
                    r'(## License\s*\n\s*\n[^\n#]+)',
                    rf'\1\n\n{author_section}',
                    content
                )
            else:
                content = content.rstrip() + f'\n\n{author_section}\n'
        
        if content != original_content:
            readme_path.write_text(content)
            return True
            
    except Exception:
        pass
    
    return False


@_nfo_log_call(level='INFO')
def sync_all_versions(new_version: str, user_config=None) -> List[str]:
    """Update version, author, and license in all detected project files."""
    updated = []
    
    # Always update VERSION file
    Path('VERSION').write_text(new_version + '\n')
    updated.append('VERSION')
    
    # Update package.json
    if Path('package.json').exists():
        if update_json_version(Path('package.json'), new_version):
            updated.append('package.json')
        # Update metadata
        if user_config and update_project_metadata(Path('package.json'), user_config):
            if 'package.json' not in updated:
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
        # Update metadata
        if user_config and update_project_metadata(Path('pyproject.toml'), user_config):
            if 'pyproject.toml' not in updated:
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
        # Update metadata
        if user_config and update_project_metadata(Path('Cargo.toml'), user_config):
            if 'Cargo.toml' not in updated:
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
    
    # Update README.md with license badges and author info
    if user_config and update_readme_metadata(user_config):
        if Path('README.md').exists():
            updated.append('README.md')
    
    # Update version badges in README.md
    if update_badge_versions(Path('README.md'), new_version):
        if 'README.md' not in updated:
            updated.append('README.md')
    
    # Update __version__ in __init__.py files
    for init_file in Path('.').rglob('__init__.py'):
        # Skip venv / build / egg-info directories
        parts = init_file.parts
        if any(p in parts for p in ('venv', '.venv', 'build', 'dist', 'node_modules'))  \
                or '.egg-info' in str(init_file):
            continue
        try:
            content = init_file.read_text()
            new_content = re.sub(
                r'^(__version__\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
                rf'\g<1>{new_version}\g<2>',
                content,
                count=1,
                flags=re.MULTILINE,
            )
            if new_content != content:
                init_file.write_text(new_content)
                updated.append(str(init_file))
        except Exception:
            pass
    
    return updated


# =============================================================================
# Git Diff Analysis for Smart Commit Messages
# =============================================================================



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


@_nfo_log_call(level='INFO')
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

@_nfo_log_call(level='DEBUG')
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


@_nfo_log_call(level='INFO')
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

@_nfo_log_call(level='INFO')
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




@_nfo_log_call(level='INFO')
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

    def has_npm_test_script() -> bool:
        """Check if package.json has a usable test script (not the npm default placeholder)."""
        pkg = Path('package.json')
        if not pkg.exists():
            return False
        try:
            data = json.loads(pkg.read_text(errors='ignore'))
        except (json.JSONDecodeError, Exception):
            return False
        scripts = data.get('scripts', {})
        test_script = scripts.get('test', '')
        if not test_script:
            return False
        # npm init sets: echo "Error: no test specified" && exit 1
        if 'no test specified' in test_script:
            return False
        return True

    for ptype in project_types:
        if ptype in PROJECT_TYPES and 'test_command' in PROJECT_TYPES[ptype]:
            cmd = wrap_python_test_cmd(PROJECT_TYPES[ptype]['test_command'])

            # Smart skip: nodejs project without a usable test script
            if ptype == 'nodejs' and cmd == 'npm test' and not has_npm_test_script():
                click.echo(click.style("\nNo test script in package.json (or default npm placeholder). Skipping tests.", fg='yellow'))
                return True

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

            # Fallback: detect npm "Missing script" error via a captured re-run
            if ptype == 'nodejs' and result.returncode != 0:
                probe = run_command(cmd, capture=True)
                combined = (probe.stderr or '') + (probe.stdout or '')
                if 'Missing script' in combined or 'missing script' in combined.lower():
                    click.echo(click.style("npm reports missing test script. Skipping tests.", fg='yellow'))
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


@_nfo_log_call(level='INFO')
def publish_project(project_types: List[str], version: str, yes: bool = False) -> bool:
    """Publish project for detected project types."""
    import sys
    
    # Validate versions against registries before publishing
    click.echo(click.style("\n🔍 Checking registry versions...", fg='cyan', bold=True))
    validation_results = validate_project_versions(project_types, version)
    validation_messages = format_validation_results(validation_results)
    
    for msg in validation_messages:
        if "❌" in msg:
            click.echo(click.style(f"  {msg}", fg='red'))
        elif "⚠️" in msg:
            click.echo(click.style(f"  {msg}", fg='yellow'))
        else:
            click.echo(click.style(f"  {msg}", fg='green'))
    
    # Check if any project has version conflicts
    has_conflicts = any(
        not result.get("is_latest", True) and result.get("registry_version")
        for result in validation_results.values()
    )
    
    if has_conflicts:
        click.echo(click.style("\n⚠️  Version conflicts detected!", fg='yellow', bold=True))
        if not yes:
            if not confirm("Continue publishing anyway?", default=False):
                click.echo(click.style("Publishing cancelled due to version conflicts.", fg='yellow'))
                return False
        else:
            click.echo(click.style("  🤖 AUTO: Accepting version conflict and continuing (--all mode)", fg='cyan'))
    
    # Check README badges
    click.echo(click.style("\n🔍 Checking README badges...", fg='cyan', bold=True))
    badge_check = check_readme_badges(version)
    
    if badge_check["exists"]:
        if badge_check["needs_update"]:
            click.echo(click.style(f"  ⚠️  {badge_check['message']}", fg='yellow'))
            if confirm("Update README badges now?", default=True):
                click.echo(click.style("  🤖 AUTO: Updating README badges (user chose Y)", fg='cyan'))
                if update_badge_versions(Path('README.md'), version):
                    click.echo(click.style("  ✅ README badges updated", fg='green'))
                    run_git('add', 'README.md')
                else:
                    click.echo(click.style("  ❌ Failed to update README badges", fg='red'))
            else:
                click.echo(click.style("  🤖 AUTO: Skipping README badges update (user chose N)", fg='cyan'))
        else:
            click.echo(click.style(f"  ✅ {badge_check['message']}", fg='green'))
    else:
        click.echo(click.style("  ℹ️  README.md not found", fg='yellow'))
    
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


@click.group(invoke_without_command=True, cls=GoalGroup)
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
@click.option('--nfo-format', default='markdown',
              type=click.Choice(['ascii', 'color', 'markdown', 'toon', 'table']),
              envvar='NFO_FORMAT', help='nfo log format (default: markdown)')
@click.option('--nfo-sink', default='', envvar='NFO_SINK',
              help='nfo sink spec for log persistence (e.g. sqlite:goal.db, md:goal-log.md)')
@click.pass_context
def main(ctx, bump, yes, all, markdown, dry_run, config_path, abstraction, nfo_format, nfo_sink):
    """Goal - Automated git push with smart commit messages."""
    # Initialize nfo structured logging
    _setup_nfo_logging(nfo_format=nfo_format, nfo_sink=nfo_sink)

    # Store output preference in context
    ctx.ensure_object(dict)
    ctx.obj['markdown'] = markdown
    ctx.obj['config_path'] = config_path
    ctx.obj['abstraction'] = abstraction
    
    # Initialize user configuration (first-time setup if needed)
    # Skip for 'config' command to avoid recursion
    if ctx.invoked_subcommand != 'config':
        try:
            user_config = get_user_config()
            ctx.obj['user_config'] = user_config
        except Exception as e:
            click.echo(click.style(f"Warning: Could not load user config: {e}", fg='yellow'))
            ctx.obj['user_config'] = None
    
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
    
    # Check if we're in a git repository (interactive clone/init if missing)
    if not ensure_git_repository(auto=yes):
        if yes:
            click.echo(click.style("No git repository. Skipping.", fg='yellow'))
            return
        sys.exit(1)
    
    # Detect project types
    project_types = detect_project_types()
    if project_types and not dry_run:
        click.echo(f"Detected project types: {click.style(', '.join(project_types), fg='cyan')}")

    # Bootstrap project environments (venv, deps, scaffold tests if missing)
    if not dry_run and project_types:
        deep_detected = detect_project_types_deep()
        for ptype, dirs in deep_detected.items():
            for pdir in dirs:
                bootstrap_project(pdir, ptype, yes=yes)

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
                            if confirm(f"Apply suggested title?\n\nCurrent: {commit_msg}\nSuggested: {suggested_title}"):
                                click.echo(click.style("  🤖 AUTO: Applying suggested title (user chose Y)", fg='cyan'))
                                apply_fix = True
                            else:
                                click.echo(click.style("  🤖 AUTO: Keeping original title (user chose N)", fg='cyan'))
                                apply_fix = False

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
                    click.echo(click.style("  🤖 AUTO: Aborting due to test failures (user chose N)", fg='cyan'))
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
            click.echo(click.style("  🤖 AUTO: Skipping tests (user chose N)", fg='cyan'))
    else:
        # When --yes or --all is used, run tests automatically
        click.echo(click.style("\n🤖 AUTO: Running tests (--all mode)", fg='cyan'))
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
            click.echo(click.style("  🤖 AUTO: Aborting commit (user chose N)", fg='cyan'))
            click.echo(click.style("Aborted.", fg='red'))
            sys.exit(1)
    else:
        click.echo(click.style("🤖 AUTO: Committing changes (--all mode)", fg='cyan'))

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
                user_config = ctx.obj.get('user_config')
                updated_files = sync_all_versions(new_version, user_config)
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
        user_config = ctx.obj.get('user_config')
        updated_files = sync_all_versions(new_version, user_config)
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
    
    # Push stage — ensure a remote is configured first
    has_remote = ensure_remote(auto=yes)

    if has_remote:
        if not yes:
            if confirm("Push to remote?"):
                branch = get_remote_branch()
                try:
                    _echo_cmd(['git', 'push', 'origin', branch])
                    result = run_git('push', 'origin', branch, capture=False)
                    if result.returncode != 0:
                        click.echo(click.style(f"✗ Push failed (exit {result.returncode}). Check remote access.", fg='red'))
                        sys.exit(1)

                    if (not no_tag) and tag_name:
                        _echo_cmd(['git', 'push', 'origin', tag_name])
                        result = run_git('push', 'origin', tag_name, capture=False)
                        if result.returncode != 0:
                            click.echo(click.style(f"⚠  Could not push tag {tag_name}.", fg='yellow'))

                    click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
                except Exception as e:
                    click.echo(click.style(f"✗ Push error: {e}", fg='red'))
                    sys.exit(1)
            else:
                click.echo(click.style("  Skipping push (user chose N).", fg='yellow'))
        else:
            # Auto-push
            click.echo(click.style("🤖 AUTO: Pushing to remote (--all mode)", fg='cyan'))
            branch = get_remote_branch()
            try:
                _echo_cmd(['git', 'push', 'origin', branch])
                result = run_git('push', 'origin', branch, capture=False)
                if result.returncode != 0:
                    click.echo(click.style(f"✗ Push failed (exit {result.returncode}). Check remote access.", fg='red'))
                    sys.exit(1)

                if (not no_tag) and tag_name:
                    _echo_cmd(['git', 'push', 'origin', tag_name])
                    result = run_git('push', 'origin', tag_name, capture=False)
                    if result.returncode != 0:
                        click.echo(click.style(f"⚠  Could not push tag {tag_name}.", fg='yellow'))

                click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))
            except Exception as e:
                click.echo(click.style(f"✗ Push error: {e}", fg='red'))
                sys.exit(1)
    else:
        click.echo(click.style("  ℹ  No remote configured — commit saved locally.", fg='yellow'))
    
    # Publish stage
    if not yes:
        if confirm(f"Publish version {new_version}?"):
            if not publish_project(project_types, new_version, yes):
                click.echo(click.style("Publish failed. Check the output above.", fg='red'))
                sys.exit(1)
            click.echo(click.style(f"\n✓ Published version {new_version}", fg='green', bold=True))
        else:
            click.echo(click.style("  🤖 AUTO: Skipping publish (user chose N)", fg='yellow'))
    else:
        # Auto-publish when --yes or --all is used
        click.echo(click.style(f"\n🤖 AUTO: Publishing version {new_version} (--all mode)", fg='cyan'))
        if not publish_project(project_types, new_version, yes):
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

    if not publish_project(project_types, version, False):
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


@main.command('check-versions')
@click.option('--update-badges', is_flag=True, help='Update README badges if needed')
def check_versions_command(update_badges):
    """Check version consistency across registries and README badges.
    
    Validates that:
    - Local version matches published registry versions
    - README badges show current version
    - All project files have consistent versions
    
    Examples:
        goal check-versions              # Check all versions
        goal check-versions --update-badges  # Update badges if needed
    """
    current_version = get_current_version()
    project_types = detect_project_types()
    
    click.echo(click.style(f"🔍 Version Check for v{current_version}", fg='cyan', bold=True))
    click.echo(f"Detected project types: {', '.join(project_types)}")
    
    # Check registry versions
    click.echo(click.style("\n📦 Registry Versions:", fg='cyan', bold=True))
    validation_results = validate_project_versions(project_types, current_version)
    validation_messages = format_validation_results(validation_results)
    
    for msg in validation_messages:
        if "❌" in msg:
            click.echo(click.style(f"  {msg}", fg='red'))
        elif "⚠️" in msg:
            click.echo(click.style(f"  {msg}", fg='yellow'))
        else:
            click.echo(click.style(f"  {msg}", fg='green'))
    
    # Check README badges
    click.echo(click.style("\n🏷️  README Badges:", fg='cyan', bold=True))
    badge_check = check_readme_badges(current_version)
    
    if badge_check["exists"]:
        if badge_check["needs_update"]:
            click.echo(click.style(f"  ⚠️  {badge_check['message']}", fg='yellow'))
            for badge in badge_check["badges"]:
                if badge["needs_update"]:
                    click.echo(click.style(f"    - {badge['url']} (shows {badge['current_version']})", fg='yellow'))
            
            if update_badges or confirm("Update README badges now?", default=True):
                if update_badge_versions(Path('README.md'), current_version):
                    click.echo(click.style("  ✅ README badges updated", fg='green'))
                    run_git('add', 'README.md')
                    click.echo(click.style("  ✓ README.md staged for commit", fg='green'))
                else:
                    click.echo(click.style("  ❌ Failed to update README badges", fg='red'))
        else:
            click.echo(click.style(f"  ✅ {badge_check['message']}", fg='green'))
    else:
        click.echo(click.style("  ℹ️  README.md not found", fg='yellow'))
    
    # Check local version files
    click.echo(click.style("\n📁 Local Version Files:", fg='cyan', bold=True))
    version_files = find_version_files()
    
    if not version_files:
        click.echo(click.style("  ℹ️  No version files found", fg='yellow'))
    else:
        all_consistent = True
        for file_path, (filepath, pattern) in version_files.items():
            file_version = get_version_from_file(filepath, pattern)
            if file_version:
                if file_version == current_version:
                    click.echo(click.style(f"  ✅ {file_path}: {file_version}", fg='green'))
                else:
                    click.echo(click.style(f"  ⚠️  {file_path}: {file_version} (expected {current_version})", fg='yellow'))
                    all_consistent = False
            else:
                click.echo(click.style(f"  ❌ {file_path}: could not read version", fg='red'))
                all_consistent = False
        
        if all_consistent:
            click.echo(click.style("  ✅ All version files are consistent", fg='green'))
    
    # Summary
    click.echo(click.style("\n📋 Summary:", fg='cyan', bold=True))
    has_issues = (
        any("❌" in msg or "⚠️" in msg for msg in validation_messages) or
        badge_check.get("needs_update", False)
    )
    
    if has_issues:
        click.echo(click.style("  ⚠️  Issues found. Consider fixing before publishing.", fg='yellow'))
        click.echo("  Run 'goal check-versions --update-badges' to fix badge issues.")
    else:
        click.echo(click.style("  ✅ All versions are consistent and ready for publishing!", fg='green'))


@main.command('clone')
@click.argument('url')
@click.argument('directory', required=False, default=None)
def clone_command(url, directory):
    """Clone an external git repository.

    Accepts HTTP(S) and SSH URLs.

    Examples:
        goal clone https://github.com/user/repo.git
        goal clone git@github.com:user/repo.git
        goal clone https://github.com/user/repo.git my-folder
    """
    if not validate_repo_url(url):
        click.echo(click.style("Error: Invalid repository URL format.", fg='red'))
        click.echo(click.style("  HTTP  example: https://github.com/user/repo.git", fg='bright_black'))
        click.echo(click.style("  SSH   example: git@github.com:user/repo.git", fg='bright_black'))
        sys.exit(1)

    success, msg = clone_repository(url, target_dir=directory)
    if success:
        click.echo(click.style(f"✓ Repository cloned into '{msg}'", fg='green', bold=True))
    else:
        click.echo(click.style(f"Error: {msg}", fg='red'))
        sys.exit(1)


@main.command('bootstrap')
@click.option('--yes', '-y', is_flag=True, help='Skip prompts (auto-accept)')
@click.option('--path', '-p', type=click.Path(exists=True), default='.', help='Root directory to scan')
def bootstrap_command(yes, path):
    """Bootstrap project environments and scaffold tests.

    Scans the current directory (and 1-level-deep subfolders) for known project
    types, then for each detected project:
      - Creates virtual environments / installs dependencies
      - Scaffolds a sample test file when no tests are found

    Supported: Python, Node.js, Rust, Go, Ruby, PHP, .NET, Java.

    Examples:
        goal bootstrap              # Interactive bootstrap
        goal bootstrap -y           # Auto-accept all prompts
        goal bootstrap -p ./myapp   # Bootstrap a specific directory
    """
    root = Path(path).resolve()
    results = bootstrap_all_projects(root, yes=yes)
    if not results:
        click.echo(click.style("No known project types detected.", fg='yellow'))
        return

    click.echo(click.style("\n✓ Bootstrap complete!", fg='green', bold=True))
    for r in results:
        try:
            rel = r['project_dir'].relative_to(root)
        except ValueError:
            rel = r['project_dir']
        status = click.style("✓", fg='green') if r['env_ok'] else click.style("✗", fg='red')
        tests = len(r['tests_found'])
        click.echo(f"  {status} {r['project_type']:>8s}  {rel}  ({tests} test file{'s' if tests != 1 else ''})")


@main.command('doctor')
@click.option('--fix/--no-fix', default=True, help='Auto-fix issues (default: yes)')
@click.option('--path', '-p', type=click.Path(exists=True), default='.', help='Root directory to scan')
def doctor_command(fix, path):
    """Diagnose and auto-fix common project configuration issues.

    Scans the current directory (and 1-level-deep subfolders) for known project
    types and checks for common problems:

    \b
    Python:  PEP 639 classifiers, missing build-system, broken backend,
             duplicate authors, deprecated license format
    Node.js: invalid package.json, missing version/test script
    Rust:    missing [package], no edition
    Go:      invalid go.mod, missing go.sum
    Ruby:    missing Gemfile.lock
    PHP:     invalid composer.json, missing autoload
    .NET:    missing TargetFramework
    Java:    missing modelVersion in pom.xml

    Examples:
        goal doctor              # Diagnose and auto-fix
        goal doctor --no-fix     # Diagnose only (report without changes)
        goal doctor -p ./myapp   # Scan a specific directory
    """
    from goal.project_bootstrap import detect_project_types_deep

    root = Path(path).resolve()
    detected = detect_project_types_deep(root)
    if not detected:
        click.echo(click.style("No known project types detected.", fg='yellow'))
        return

    all_reports = []
    for ptype, dirs in detected.items():
        for project_dir in dirs:
            report = diagnose_and_report(project_dir, ptype, auto_fix=fix)
            all_reports.append(report)

    # Final summary
    total_issues = sum(len(r.issues) for r in all_reports)
    total_fixed = sum(len(r.fixed) for r in all_reports)
    total_errors = sum(len(r.errors) for r in all_reports)

    click.echo(click.style("\n" + "=" * 60, fg='cyan'))
    if total_issues == 0:
        click.echo(click.style("✓ All projects are healthy!", fg='green', bold=True))
    else:
        click.echo(click.style(f"🩺 Doctor summary: {total_issues} issue(s) found", fg='cyan', bold=True))
        if total_fixed:
            click.echo(click.style(f"   ✓ {total_fixed} auto-fixed", fg='green'))
        remaining = total_errors - sum(1 for r in all_reports for i in r.errors if i.fixed)
        if remaining > 0:
            click.echo(click.style(f"   ✗ {remaining} error(s) need manual attention", fg='red'))


@main.command('config')
@click.option('--reset', is_flag=True, help='Reset user configuration and re-run setup')
@click.option('--show', is_flag=True, help='Show current configuration')
def config_command(reset, show):
    """Manage goal user configuration.
    
    View or modify your user preferences stored in ~/.goal:
    - Author name and email (from git config)
    - Default license preference
    
    Examples:
        goal config              # Show current configuration
        goal config --reset      # Re-run interactive setup
    """
    if reset:
        initialize_user_config(force=True)
    else:
        show_user_config()


if __name__ == '__main__':
    main()
