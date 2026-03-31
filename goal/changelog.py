"""Changelog management functions - extracted from cli.py."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def _classify_file_domain(filepath: str, domain_mapping: Dict[str, str]) -> str:
    """Return the domain label for a file based on domain_mapping patterns."""
    import fnmatch
    for pattern, domain in domain_mapping.items():
        if fnmatch.fnmatch(filepath, pattern):
            return domain
        if pattern.endswith('/*') and filepath.startswith(pattern[:-2]):
            return domain
    return 'other'


def _build_domain_entry(version: str, date_str: str, files: List[str], config: Dict) -> str:
    """Build a changelog entry grouped by domain."""
    domain_mapping = config.get('git', {}).get('commit', {}).get('domain_mapping', {})
    domain_changes: Dict[str, List[str]] = {}
    for f in files:
        if not f:
            continue
        domain = _classify_file_domain(f, domain_mapping)
        domain_changes.setdefault(domain, []).append(f)

    entry_lines = [f"## [{version}] - {date_str}\n"]
    for domain in ['feat', 'fix', 'docs', 'refactor', 'test', 'chore', 'other']:
        if domain not in domain_changes:
            continue
        entry_lines.append(f"\n### {domain.capitalize()}\n")
        for f in domain_changes[domain][:10]:
            entry_lines.append(f"- Update {f}\n")
        overflow = len(domain_changes[domain]) - 10
        if overflow > 0:
            entry_lines.append(f"- ... and {overflow} more files\n")
    return "".join(entry_lines)


def _build_simple_entry(version: str, date_str: str, files: List[str]) -> str:
    """Build a changelog entry without domain grouping."""
    change_list = [f"- Update {f}" for f in files[:10]]
    if len(files) > 10:
        change_list.append(f"- ... and {len(files) - 10} more files")
    return f"## [{version}] - {date_str}\n\n### Changed\n" + "\n".join(change_list) + "\n"


def _insert_entry(existing_content: str, entry: str) -> str:
    """Insert a version entry into existing changelog content."""
    if not existing_content:
        return ("# Changelog\n\n"
                "All notable changes to this project will be documented in this file.\n\n"
                "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
                "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
                f"## [Unreleased]\n\n{entry}\n")

    if '## [Unreleased]' in existing_content:
        parts = existing_content.split('## [Unreleased]', 1)
        if len(parts) == 2:
            match = re.search(r'\n## ', parts[1])
            if match:
                pos = match.start()
                return f"{parts[0]}## [Unreleased]{parts[1][:pos]}\n{entry}{parts[1][pos:]}"
        return f"{existing_content}\n{entry}"

    if existing_content.startswith('# '):
        first_nl = existing_content.find('\n')
        if first_nl > 0:
            return f"{existing_content[:first_nl]}\n\n## [Unreleased]\n\n{entry}{existing_content[first_nl:]}"
        return f"{existing_content}\n{entry}"

    return f"## [Unreleased]\n\n{entry}\n{existing_content}"


def update_changelog(version: str, files: List[str], commit_msg: str, 
                     config: Dict = None, changelog_entry: Dict = None) -> None:
    """Update CHANGELOG.md with new version and changes.
    
    Args:
        version: New version string.
        files: List of changed files.
        commit_msg: Commit message.
        config: Optional goal.yaml config dict for domain grouping.
        changelog_entry: Optional structured changelog entry from smart_commit.
    """
    changelog_path = Path('CHANGELOG.md')
    existing_content = changelog_path.read_text() if changelog_path.exists() else ""
    date_str = datetime.now().strftime('%Y-%m-%d')

    use_domain_grouping = (config or {}).get('git', {}).get('changelog', {}).get('group_by_domain', False)

    if use_domain_grouping and config:
        entry = _build_domain_entry(version, date_str, files, config)
    else:
        entry = _build_simple_entry(version, date_str, files)

    changelog_path.write_text(_insert_entry(existing_content, entry))


__all__ = ['update_changelog']
