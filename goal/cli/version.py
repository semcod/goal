"""Version management functions - extracted from cli.py."""

import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple

try:
    from ..git_ops import run_git
    from ..version_validation import update_badge_versions
except ImportError:
    from goal.git_ops import run_git
    from goal.version_validation import update_badge_versions


# Project type definitions with version patterns
PROJECT_TYPES = {
    'python': {
        'files': ['pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt', 'Pipfile', 'environment.yml', 'poetry.lock', 'uv.lock', 'Pipfile.lock'],
        'version_patterns': {
            'pyproject.toml': r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'setup.py': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'setup.cfg': r'^version\s*=\s*(\d+\.\d+\.\d+)',
        },
        'test_command': 'python -m pytest',
        'publish_command': 'python -m build && python -m twine upload --skip-existing dist/*',
    },
    'nodejs': {
        'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb'],
        'version_patterns': {
            'package.json': r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'npm test',
        'publish_command': 'npm publish',
    },
    'rust': {
        'files': ['Cargo.toml', 'Cargo.lock'],
        'version_patterns': {
            'Cargo.toml': r'^version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'cargo test',
        'publish_command': 'cargo publish',
    },
    'go': {
        'files': ['go.mod', 'go.sum'],
        'version_patterns': {},  # Go uses git tags
        'test_command': 'go test ./...',
        'publish_command': 'git push origin --tags',
    },
    'ruby': {
        'files': ['Gemfile', '*.gemspec', 'Gemfile.lock'],
        'version_patterns': {
            '*.gemspec': r'\.version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
        },
        'test_command': 'bundle exec rspec',
        'publish_command': 'gem build *.gemspec && gem push *.gem',
    },
    'php': {
        'files': ['composer.json', 'composer.lock'],
        'version_patterns': {
            'composer.json': r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'composer test',
        'publish_command': 'composer publish',
    },
    'dotnet': {
        'files': ['*.csproj', '*.fsproj', 'packages.lock.json'],
        'version_patterns': {
            '*.csproj': r'<Version>(\d+\.\d+\.\d+)</Version>',
            '*.fsproj': r'<Version>(\d+\.\d+\.\d+)</Version>',
        },
        'test_command': 'dotnet test',
        'publish_command': 'dotnet pack && dotnet nuget push *.nupkg',
    },
    'java': {
        'files': ['pom.xml', 'build.gradle', 'build.gradle.kts', 'gradle.lockfile'],
        'version_patterns': {
            'pom.xml': r'<version>(\d+\.\d+\.\d+)</version>',
            'build.gradle': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'build.gradle.kts': r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'mvn test',
        'publish_command': 'mvn deploy',
    },
    'elixir': {
        'files': ['mix.exs', 'mix.lock'],
        'version_patterns': {
            'mix.exs': r'version:\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'mix test',
        'publish_command': 'mix hex.publish',
    },
    'haskell': {
        'files': ['*.cabal', 'cabal.project', 'cabal.project.freeze', 'stack.yaml', 'stack.yaml.lock'],
        'version_patterns': {
            '*.cabal': r'version:\s*(\d+\.\d+\.\d+)',
            'cabal.project': r'version:\s*(\d+\.\d+\.\d+)',
        },
        'test_command': 'cabal test',
        'publish_command': 'cabal sdist',
    },
    'swift': {
        'files': ['Package.swift', 'Package.resolved'],
        'version_patterns': {
            'Package.swift': r'let version = "(\d+\.\d+\.\d+)"',
        },
        'test_command': 'swift test',
        'publish_command': 'swift package publish',
    },
    'dart': {
        'files': ['pubspec.yaml', 'pubspec.lock'],
        'version_patterns': {
            'pubspec.yaml': r'^version:\s*(\d+\.\d+\.\d+)',
        },
        'test_command': 'dart test',
        'publish_command': 'pub publish',
    },
    'kotlin': {
        'files': ['build.gradle.kts'],
        'version_patterns': {
            'build.gradle.kts': r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        'test_command': 'gradle test',
        'publish_command': 'gradle publish',
    },
}


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


def get_current_version() -> str:
    """Get current version from VERSION file or project files."""
    version_file = Path('VERSION')
    if version_file.exists():
        content = version_file.read_text().strip()
        if content:
            return content
    
    # Try to get from project files
    version_files = find_version_files()
    for filepath, (path, pattern) in version_files.items():
        version = get_version_from_file(path, pattern)
        if version:
            return version
    
    return '0.0.0'


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to semantic versioning."""
    parts = version.split('.')
    if len(parts) < 3:
        parts.extend(['0'] * (3 - len(parts)))
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


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
    """Update author and license in project files based on user config."""
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
            r'^(version\s*=\s*")\d+\.\d+\.\d+("})',
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


__all__ = [
    'PROJECT_TYPES',
    'detect_project_types',
    'find_version_files',
    'get_version_from_file',
    'get_current_version',
    'bump_version',
    'update_version_in_file',
    'update_json_version',
    'update_project_metadata',
    'update_readme_metadata',
    'sync_all_versions',
]
