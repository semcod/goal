"""Version management - detection and update utilities."""

import re
import json
from pathlib import Path
from typing import Optional, List, Dict

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
            filepath.write_text(f"{json.dumps(content, indent=2)}\n")
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
                    
                    # Add new author in PEP 621 object format (not Poetry string format)
                    new_author = f'{{name = "{author_name}", email = "{author_email}"}}'
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
                    content,
                    flags=re.MULTILINE
                )
        
        # Update package.json
        elif filepath.name == 'package.json':
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
            
            content = json.dumps(data, indent=2) + '\n'
        
        # Update setup.py
        elif filepath.name == 'setup.py':
            # Update author and email
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
