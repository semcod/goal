"""Version management - detection and update utilities."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

try:
    import tomlkit
except ImportError:
    tomlkit = None

if TYPE_CHECKING:
    from tomlkit import TOMLDocument
else:
    TOMLDocument = Any

from .version_types import PROJECT_TYPES


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
    """Bump version according to semantic versioning.

    Handles pre-release suffixes such as:
      - PEP 440 pre-release:  1.2.3a1, 1.2.3b2, 1.2.3rc1
      - PEP 440 dev/post:     1.2.3.dev1, 1.2.3.post1
      - Hyphen pre-release:   1.2.3-rc1, 1.2.3-alpha, 1.2.3-beta.2
      - CalVer with suffix:   2024.1.0-rc1
    The pre-release suffix is always stripped; the bumped result is a clean semver.
    """
    # Strip any pre-release / build suffix before numeric parsing.
    # Matches an optional hyphen or dot followed by non-numeric tail, e.g.
    # "0.2.0-rc1", "1.0.0rc1", "2024.1.0.dev3", "1.2.3.post1"
    base = re.split(r'[-+]|(?<=\d)(?=[a-zA-Z])', version)[0]
    # Remove any trailing dot-separated non-numeric segment (e.g. ".dev1", ".post1")
    base = re.sub(r'\.(dev|post|a|b|rc|alpha|beta)\d*$', '', base, flags=re.IGNORECASE)

    parts = base.split('.')
    if len(parts) < 3:
        parts.extend(['0'] * (3 - len(parts)))

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        # Last-resort fallback: treat as 0.0.0
        major, minor, patch = 0, 0, 0

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
            filepath.write_text(f"{json.dumps(content, indent=2)}\n")
            return True
    except Exception:
        pass
    return False


def _build_author_block(existing_authors: str, author_name: str, author_email: str) -> str:
    author_entries = []
    for line in existing_authors.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            author_entries.append(line.rstrip(','))

    author_entries.append(f'{{name = "{author_name}", email = "{author_email}"}}')

    authors_block = 'authors = [\n'
    for entry in author_entries:
        authors_block += f'    {entry},\n'
    authors_block += ']'
    return authors_block


def _update_tomlkit_license(doc: TOMLDocument, license_id: str) -> None:
    """Update license in tomlkit document.

    PEP 639 / setuptools>=77 requires ``license`` to be a plain SPDX
    identifier string, **not** a table like ``{text = "..."}``.
    """
    if 'project' in doc:
        doc['project']['license'] = license_id


def _update_tomlkit_authors(doc: TOMLDocument, author_name: str, author_email: str) -> None:
    """Update authors in tomlkit document."""
    if 'project' in doc and 'authors' in doc['project']:
        authors = doc['project']['authors']
        author_exists = any(
            isinstance(a, dict) and a.get('email') == author_email
            for a in authors
        )
        if not author_exists:
            authors.append({'name': author_name, 'email': author_email})


def _update_tomlkit_classifier(doc: TOMLDocument, license_classifier: str) -> None:
    """Update license classifier in tomlkit document."""
    if 'project' in doc and 'classifiers' in doc['project']:
        classifiers = doc['project']['classifiers']
        for i, classifier in enumerate(classifiers):
            if 'License :: OSI Approved ::' in classifier:
                classifiers[i] = license_classifier
                break


def _update_pyproject_with_tomlkit(content: str, author_name: str, author_email: str,
                                   license_id: str, license_classifier: Optional[str]) -> Optional[str]:
    """Update pyproject.toml using tomlkit. Returns updated content or None if failed."""
    if tomlkit is None:
        return None
    try:
        doc = tomlkit.parse(content)
        _update_tomlkit_license(doc, license_id)
        _update_tomlkit_authors(doc, author_name, author_email)
        if license_classifier:
            _update_tomlkit_classifier(doc, license_classifier)
        return tomlkit.dumps(doc)
    except Exception:
        return None


def _update_regex_license(content: str, license_id: str) -> str:
    """Update license field using regex."""
    content = re.sub(
        r'^license\s*=\s*[{{\[].*?[}}\]]',
        f'license = "{license_id}"',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^license\s*=\s*["\'].*?["\']',
        f'license = "{license_id}"',
        content,
        flags=re.MULTILINE
    )
    return content


def _update_regex_authors(content: str, author_name: str, author_email: str) -> str:
    """Update authors field using regex."""
    authors_match = re.search(r'authors\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if authors_match and author_email not in authors_match.group(1):
        authors_block = _build_author_block(authors_match.group(1), author_name, author_email)
        content = re.sub(
            r'authors\s*=\s*\[.*?\]',
            authors_block,
            content,
            flags=re.DOTALL
        )
    return content


def _update_regex_classifier(content: str, license_classifier: Optional[str]) -> str:
    """Update license classifier using regex."""
    if license_classifier:
        content = re.sub(
            r'"License :: OSI Approved :: .*?"',
            f'"{license_classifier}"',
            content,
            flags=re.MULTILINE
        )
    return content


def _update_pyproject_with_regex(content: str, author_name: str, author_email: str,
                                 license_id: str, license_classifier: Optional[str]) -> str:
    """Update pyproject.toml using regex fallback."""
    content = _update_regex_license(content, license_id)
    content = _update_regex_authors(content, author_name, author_email)
    content = _update_regex_classifier(content, license_classifier)
    return content


def _update_pyproject_metadata(content: str, author_name: str, author_email: str,
                               license_id: str, license_classifier: Optional[str]) -> str:
    """Update pyproject.toml metadata with author and license information."""
    # Try tomlkit first
    result = _update_pyproject_with_tomlkit(content, author_name, author_email,
                                            license_id, license_classifier)
    if result is not None:
        return result

    # Fallback to regex-based approach
    return _update_pyproject_with_regex(content, author_name, author_email,
                                        license_id, license_classifier)


def _update_package_json_metadata(content: str, author_name: str, author_email: str,
                                  license_id: str) -> str:
    data = json.loads(content)
    if 'author' in data:
        if isinstance(data['author'], dict):
            data['author']['name'] = author_name
            data['author']['email'] = author_email
        else:
            data['author'] = {
                'name': author_name,
                'email': author_email
            }
    else:
        data['author'] = {
            'name': author_name,
            'email': author_email
        }

    if 'license' in data:
        data['license'] = license_id

    return json.dumps(data, indent=2) + '\n'


def _update_setup_py_metadata(content: str, author_name: str, author_email: str,
                              license_id: str) -> str:
    content = re.sub(
        r"author\s*=\s*['\"].*?['\"]",
        f'author="{author_name}"',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"author_email\s*=\s*['\"].*?['\"]",
        f'author_email="{author_email}"',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r"license\s*=\s*['\"].*?['\"]",
        f'license="{license_id}"',
        content,
        flags=re.MULTILINE
    )
    return content


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
        
        if filepath.name == 'pyproject.toml':
            content = _update_pyproject_metadata(content, author_name, author_email, license_id, license_classifier)
        elif filepath.name == 'package.json':
            content = _update_package_json_metadata(content, author_name, author_email, license_id)
        elif filepath.name == 'setup.py':
            content = _update_setup_py_metadata(content, author_name, author_email, license_id)
        
        if content != original_content:
            filepath.write_text(content)
            return True
    except Exception:
        pass
    
    return False


def update_readme_metadata(user_config) -> bool:
    """Update README.md with author and license information."""
    if not user_config:
        return False
    
    try:
        author_name = user_config.get('author_name')
        license_id = user_config.get('license')
        
        if not all([author_name, license_id]):
            return False
        
        readme_path = Path('README.md')
        if not readme_path.exists():
            return False
        
        content = readme_path.read_text()
        original_content = content
        
        # Update or add license section - only match H2 headers at line start
        # Find the LAST occurrence (the real section, not code blocks)
        license_matches = list(re.finditer(r'^## License[ \t]*$', content, re.MULTILINE))
        if license_matches:
            # Use the last match (real License section is typically at the end)
            last_match = license_matches[-1]
            start_pos = last_match.start()
            # Find where this section ends (next ## header or end of file)
            rest = content[last_match.end():]
            next_header = re.search(r'^##[ \t]', rest, re.MULTILINE)
            if next_header:
                end_pos = last_match.end() + next_header.start()
            else:
                end_pos = len(content)
            # Replace only this section
            new_section = f'## License\n\nLicensed under {license_id}.\n'
            content = content[:start_pos] + new_section + content[end_pos:]
        else:
            # Add license section at the end, but only if license info is not already present
            license_line = f'Licensed under {license_id}.'
            if license_line not in content and license_id not in content:
                content += f'\n\n## License\n\n{license_line}\n'
        
        # Update author information if present - only match H2 headers at line start
        # Find the LAST occurrence (the real section, not code blocks)
        author_matches = list(re.finditer(r'^## Author[ \t]*$', content, re.MULTILINE))
        if author_matches:
            # Use the last match (real Author section is typically at the end)
            last_match = author_matches[-1]
            start_pos = last_match.start()
            # Find where this section ends (next ## header or end of file)
            rest = content[last_match.end():]
            next_header = re.search(r'^##[ \t]', rest, re.MULTILINE)
            if next_header:
                end_pos = last_match.end() + next_header.start()
            else:
                end_pos = len(content)
            # Replace only this section
            new_section = f'## Author\n\n{author_name}\n'
            content = content[:start_pos] + new_section + content[end_pos:]
        
        if content != original_content:
            readme_path.write_text(content)
            return True
    except Exception:
        pass
    
    return False
