"""Smart commit message generation with code abstraction."""

import fnmatch
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CodeAbstraction:
    """Extracts meaningful abstractions from code changes."""
    
    EXTENSION_TO_LANGUAGE = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.rs': 'rust',
        '.go': 'go',
        '.md': 'markdown',
        '.rst': 'markdown',
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with goal.yaml configuration."""
        self.config = config
        self.domain_mapping = config.get('git', {}).get('commit', {}).get('domain_mapping', {})
        self.code_parsers = config.get('code_parsers', {})
        self.benefit_keywords = config.get('git', {}).get('commit', {}).get('benefit_keywords', {})
        self.templates = config.get('git', {}).get('commit', {}).get('templates', {})
        self.abstraction_level = config.get('git', {}).get('commit', {}).get('abstraction_level', 'auto')
    
    def get_domain(self, filepath: str) -> str:
        """Map filepath to domain using goal.yaml domain_mapping."""
        for pattern, domain in self.domain_mapping.items():
            if fnmatch.fnmatch(filepath, pattern):
                return domain
            # Also check if the pattern matches as a prefix
            if pattern.endswith('/*') and filepath.startswith(pattern[:-2]):
                return domain
            if pattern.endswith('/*.py') and filepath.startswith(pattern[:-4]) and filepath.endswith('.py'):
                return domain
        
        # Fallback based on file extension
        ext = Path(filepath).suffix
        if ext in ['.md', '.rst', '.txt']:
            return 'docs'
        if ext in ['.py', '.js', '.ts', '.rs', '.go']:
            return 'core'
        if filepath.startswith('test') or filepath.startswith('spec'):
            return 'test'
        
        return 'other'
    
    def get_language(self, filepath: str) -> str:
        """Get programming language from file extension."""
        ext = Path(filepath).suffix.lower()
        return self.EXTENSION_TO_LANGUAGE.get(ext, 'unknown')
    
    def extract_entities(self, filepath: str, diff_content: str) -> List[str]:
        """Extract code entities (functions, classes, etc.) from diff."""
        language = self.get_language(filepath)
        parser = self.code_parsers.get(language, {})
        
        entities = []
        extract_patterns = parser.get('extract', [])
        ignore_patterns = parser.get('ignore', [])
        entity_pattern = parser.get('entity_pattern', '')
        
        # Only look at added lines (starting with +)
        added_lines = [
            line[1:].strip() 
            for line in diff_content.split('\n') 
            if line.startswith('+') and not line.startswith('+++')
        ]
        
        for line in added_lines:
            # Skip ignored patterns
            if any(ignore in line for ignore in ignore_patterns):
                continue
            
            # Check extract patterns
            for pattern in extract_patterns:
                if pattern in line:
                    # Try to extract entity name using regex
                    if entity_pattern:
                        match = re.search(entity_pattern, line)
                        if match:
                            entity_name = match.group(1)
                            if entity_name and len(entity_name) > 1:
                                entities.append(entity_name)
                    else:
                        # Fallback: extract word after pattern
                        parts = line.split(pattern)
                        if len(parts) > 1:
                            word = parts[1].split('(')[0].split(':')[0].split()[0] if parts[1] else ''
                            if word and len(word) > 1 and word.isidentifier():
                                entities.append(word)
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for e in entities:
            if e not in seen:
                seen.add(e)
                unique_entities.append(e)
        
        return unique_entities[:10]  # Limit to 10 entities
    
    def extract_markdown_topics(self, diff_content: str) -> List[str]:
        """Extract topics from markdown changes."""
        topics = []
        
        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                line = line[1:].strip()
                # Extract headers
                if line.startswith('#'):
                    topic = re.sub(r'^#+\s*', '', line)
                    if topic and len(topic) > 2:
                        topics.append(topic)
        
        return topics[:5]
    
    def infer_benefit(self, entities: List[str], domain: str, commit_type: str) -> str:
        """Infer business benefit from entities and context."""
        # Check for specific patterns in entities
        entity_str = ' '.join(entities).lower()
        
        # Pattern matching for common functionality
        benefit_patterns = [
            (r'config|settings|yaml|json', 'better configuration management'),
            (r'cli|command|option|arg', 'improved CLI experience'),
            (r'api|endpoint|route|handler', 'enhanced API functionality'),
            (r'test|spec|assert', 'improved test coverage'),
            (r'doc|readme|guide|tutorial', 'better documentation'),
            (r'auth|login|token|session', 'enhanced security'),
            (r'cache|perf|optim|speed', 'improved performance'),
            (r'refactor|clean|extract|split', 'cleaner code architecture'),
            (r'fix|bug|issue|error', 'resolved issues'),
            (r'feat|add|new|create', 'new functionality'),
        ]
        
        for pattern, benefit in benefit_patterns:
            if re.search(pattern, entity_str):
                return benefit
        
        # Fallback to domain-based benefit
        domain_benefits = self.benefit_keywords
        if domain in domain_benefits:
            return domain_benefits[domain]
        
        # Fallback to commit type benefit
        if commit_type in domain_benefits:
            return domain_benefits[commit_type]
        
        return 'improved functionality'
    
    def determine_abstraction_level(self, analysis: Dict[str, Any]) -> str:
        """Determine the best abstraction level based on analysis."""
        if self.abstraction_level != 'auto':
            return self.abstraction_level
        
        file_count = analysis.get('file_count', 0)
        entity_count = len(analysis.get('entities', []))
        
        # High abstraction for small, focused changes
        if file_count <= 3 and entity_count <= 5:
            return 'high'
        
        # Medium abstraction when we have meaningful entities
        if entity_count >= 2:
            return 'medium'
        
        # Low abstraction for large changes or no entities
        if file_count > 10:
            return 'low'
        
        return 'medium'
    
    def get_action_verb(self, commit_type: str) -> str:
        """Get action verb for commit type."""
        verbs = {
            'feat': 'add',
            'fix': 'fix',
            'docs': 'document',
            'refactor': 'refactor',
            'test': 'test',
            'build': 'configure',
            'chore': 'update',
            'style': 'format',
            'perf': 'optimize',
        }
        return verbs.get(commit_type, 'update')


class SmartCommitGenerator:
    """Generates smart commit messages using code abstraction."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with goal.yaml configuration."""
        self.config = config
        self.abstraction = CodeAbstraction(config)
    
    def analyze_changes(self, staged_files: List[str] = None) -> Dict[str, Any]:
        """Analyze staged changes and extract abstractions."""
        if staged_files is None:
            staged_files = self._get_staged_files()
        
        analysis = {
            'files': staged_files,
            'file_count': len(staged_files),
            'domains': defaultdict(list),
            'entities': [],
            'added': 0,
            'deleted': 0,
            'primary_domain': 'core',
            'commit_type': 'feat',
            'benefit': '',
        }
        
        if not staged_files:
            return analysis
        
        # Analyze each file
        domain_counter = Counter()
        all_entities = []
        
        for filepath in staged_files:
            domain = self.abstraction.get_domain(filepath)
            domain_counter[domain] += 1
            analysis['domains'][domain].append(filepath)
            
            # Get diff for this file
            diff = self._get_file_diff(filepath)
            if diff:
                # Count additions/deletions
                for line in diff.split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        analysis['added'] += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        analysis['deleted'] += 1
                
                # Extract entities
                if filepath.endswith('.md'):
                    entities = self.abstraction.extract_markdown_topics(diff)
                else:
                    entities = self.abstraction.extract_entities(filepath, diff)
                all_entities.extend(entities)
        
        # Determine primary domain
        if domain_counter:
            analysis['primary_domain'] = domain_counter.most_common(1)[0][0]
        
        # Deduplicate entities
        seen = set()
        unique_entities = []
        for e in all_entities:
            if e not in seen:
                seen.add(e)
                unique_entities.append(e)
        analysis['entities'] = unique_entities[:10]
        
        # Determine commit type
        analysis['commit_type'] = self._infer_commit_type(analysis)
        
        # Infer benefit
        analysis['benefit'] = self.abstraction.infer_benefit(
            analysis['entities'],
            analysis['primary_domain'],
            analysis['commit_type']
        )
        
        return analysis
    
    def _get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, check=True
            )
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            return []
    
    def _get_file_diff(self, filepath: str) -> str:
        """Get diff content for a specific file."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--', filepath],
                capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ''
    
    def _infer_commit_type(self, analysis: Dict[str, Any]) -> str:
        """Infer commit type from analysis."""
        domain = analysis.get('primary_domain', 'core')
        entities = analysis.get('entities', [])
        added = analysis.get('added', 0)
        deleted = analysis.get('deleted', 0)
        
        # Map domain to commit type
        domain_type_map = {
            'docs': 'docs',
            'test': 'test',
            'ci': 'build',
            'build': 'build',
            'config': 'chore',
        }
        
        if domain in domain_type_map:
            return domain_type_map[domain]
        
        # Analyze entities for type hints
        entity_str = ' '.join(entities).lower()
        if 'fix' in entity_str or 'bug' in entity_str:
            return 'fix'
        if 'refactor' in entity_str or 'extract' in entity_str:
            return 'refactor'
        if 'test' in entity_str:
            return 'test'
        
        # Analyze add/delete ratio
        if deleted > added * 2:
            return 'refactor'
        if added > 0 and deleted == 0:
            return 'feat'
        if deleted > added:
            return 'fix'
        
        return 'feat'
    
    def generate_message(self, analysis: Dict[str, Any] = None, level: str = None) -> str:
        """Generate commit message based on analysis."""
        if analysis is None:
            analysis = self.analyze_changes()
        
        if level is None:
            level = self.abstraction.determine_abstraction_level(analysis)
        
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        entities = analysis.get('entities', [])
        benefit = analysis.get('benefit', 'improved functionality')
        file_count = analysis.get('file_count', 0)
        added = analysis.get('added', 0)
        deleted = analysis.get('deleted', 0)
        
        # Get template for commit type and level
        templates = self.abstraction.templates.get(commit_type, {})
        
        if isinstance(templates, dict) and level in templates:
            template = templates[level]
        elif isinstance(templates, str):
            template = templates
        else:
            # Fallback to abstraction_levels
            levels = self.config.get('git', {}).get('commit', {}).get('abstraction_levels', {})
            template = levels.get(level, '{type}({domain}): {benefit}')
        
        # Format entities for message
        if entities:
            if len(entities) <= 3:
                entities_str = ', '.join(entities)
            else:
                entities_str = ', '.join(entities[:3]) + f' and {len(entities) - 3} more'
        else:
            entities_str = 'changes'
        
        # Build message
        action = self.abstraction.get_action_verb(commit_type)
        
        message = template.format(
            type=commit_type,
            domain=domain,
            benefit=benefit,
            entities=entities_str,
            action=action,
            file_count=file_count,
            added=added,
            deleted=deleted,
            scope=domain,
            description=benefit,
        )
        
        return message
    
    def generate_changelog_entry(self, analysis: Dict[str, Any] = None, 
                                  commit_hash: str = None) -> Dict[str, Any]:
        """Generate structured changelog entry."""
        if analysis is None:
            analysis = self.analyze_changes()
        
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        entities = analysis.get('entities', [])
        benefit = analysis.get('benefit', 'improved functionality')
        
        # Map commit type to changelog section
        type_to_section = {
            'feat': 'Added',
            'fix': 'Fixed',
            'docs': 'Changed',
            'refactor': 'Changed',
            'perf': 'Changed',
            'test': 'Changed',
            'build': 'Changed',
            'chore': 'Changed',
            'style': 'Changed',
        }
        
        section = type_to_section.get(commit_type, 'Changed')
        
        # Build entry
        entry = {
            'section': section,
            'domain': domain,
            'type': commit_type,
            'message': f"{commit_type}({domain}): {benefit}",
            'entities': entities[:5],
            'commit_hash': commit_hash,
        }
        
        # Add entity details if configured
        changelog_config = self.config.get('git', {}).get('changelog', {})
        if changelog_config.get('include_entities', True) and entities:
            max_entities = changelog_config.get('max_entities_per_entry', 5)
            entry['entity_details'] = entities[:max_entities]
        
        return entry
    
    def format_changelog_entry(self, entry: Dict[str, Any]) -> str:
        """Format changelog entry as markdown."""
        message = entry.get('message', '')
        entities = entry.get('entity_details', [])
        commit_hash = entry.get('commit_hash', '')
        
        # Base entry
        if commit_hash:
            line = f"- {message} ([{commit_hash[:7]}](commit/{commit_hash}))"
        else:
            line = f"- {message}"
        
        # Add entity details
        if entities:
            entity_list = ', '.join(f'`{e}`' for e in entities)
            line += f"\n  - Added: {entity_list}"
        
        return line


def create_smart_generator(config: Dict[str, Any]) -> SmartCommitGenerator:
    """Factory function to create SmartCommitGenerator."""
    return SmartCommitGenerator(config)
