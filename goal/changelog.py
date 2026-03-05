"""Changelog management functions - extracted from cli.py."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    from ..git_ops import run_git
except ImportError:
    from goal.git_ops import run_git


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
            domain_changes[domain].append(f)
        
        # Build entry with domain grouping
        entry_lines = [f"## [{version}] - {date_str}\n"]
        
        for domain in ['feat', 'fix', 'docs', 'refactor', 'test', 'chore', 'other']:
            if domain in domain_changes:
                domain_label = domain.capitalize()
                entry_lines.append(f"\n### {domain_label}\n")
                for f in domain_changes[domain][:10]:
                    entry_lines.append(f"- Update {f}\n")
                if len(domain_changes[domain]) > 10:
                    entry_lines.append(f"- ... and {len(domain_changes[domain]) - 10} more files\n")
        
        entry = "".join(entry_lines)
    else:
        # Simple entry without domain grouping
        change_list = []
        for f in files[:10]:
            change_list.append(f"- Update {f}")
        if len(files) > 10:
            change_list.append(f"- ... and {len(files) - 10} more files")
        
        entry = f"## [{version}] - {date_str}\n\n### Changed\n" + "\n".join(change_list) + "\n"
    
    # Insert or create changelog
    if existing_content:
        # Check for [Unreleased] section
        if '## [Unreleased]' in existing_content:
            # Insert after [Unreleased] section
            parts = existing_content.split('## [Unreleased]', 1)
            if len(parts) == 2:
                rest = parts[1]
                # Find next ## heading
                match = re.search(r'\n## ', rest)
                if match:
                    pos = match.start()
                    new_content = parts[0] + '## [Unreleased]' + rest[:pos] + '\n' + entry + rest[pos:]
                else:
                    new_content = existing_content + '\n' + entry
            else:
                new_content = existing_content + '\n' + entry
        else:
            # Add at the beginning after title
            if existing_content.startswith('# '):
                # Find first newline after title
                first_nl = existing_content.find('\n')
                if first_nl > 0:
                    new_content = existing_content[:first_nl] + '\n\n## [Unreleased]\n\n' + entry + existing_content[first_nl:]
                else:
                    new_content = existing_content + '\n' + entry
            else:
                new_content = '## [Unreleased]\n\n' + entry + '\n' + existing_content
    else:
        # Create new changelog
        new_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

{entry}
"""
    
    changelog_path.write_text(new_content)


__all__ = ['update_changelog']
