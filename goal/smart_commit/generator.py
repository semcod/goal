"""Smart commit generator - generates commit messages using code abstraction."""

import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .abstraction import CodeAbstraction
except ImportError:
    from goal.smart_commit.abstraction import CodeAbstraction


class SmartCommitGenerator:
    """Generates smart commit messages using code abstraction."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with goal.yaml configuration."""
        self.config = config
        self.abstraction = CodeAbstraction(config)
        self._deep_analyzer = None
    
    @property
    def deep_analyzer(self):
        """Lazy-load deep analyzer to avoid circular imports."""
        if self._deep_analyzer is None:
            try:
                from goal.deep_analyzer import CodeChangeAnalyzer
                self._deep_analyzer = CodeChangeAnalyzer()
            except ImportError:
                self._deep_analyzer = False  # Mark as unavailable
        return self._deep_analyzer if self._deep_analyzer else None
    
    def analyze_changes(self, staged_files: List[str] = None) -> Dict[str, Any]:
        """Analyze staged changes and extract abstractions."""
        if staged_files is None:
            staged_files = self._get_staged_files()
        
        analysis = {
            'files': staged_files,
            'file_count': len(staged_files),
            'domains': defaultdict(list),
            'entities': [],
            'features': [],
            'added': 0,
            'deleted': 0,
            'primary_domain': 'core',
            'commit_type': 'feat',
            'benefit': '',
            'summary': '',
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
        
        # Detect high-level features
        analysis['features'] = self.abstraction.detect_features(staged_files, unique_entities)
        
        # Determine commit type
        analysis['commit_type'] = self._infer_commit_type(analysis)
        
        # Use deep analyzer if available for better functional value
        deep_analysis = None
        if self.deep_analyzer:
            try:
                deep_analysis = self.deep_analyzer.generate_functional_summary(staged_files)
                analysis['deep_analysis'] = deep_analysis
                
                # Extract functional value from deep analysis
                if deep_analysis.get('functional_value'):
                    analysis['benefit'] = deep_analysis['functional_value']
                
                # Merge deep entities with existing
                if deep_analysis.get('aggregated'):
                    agg = deep_analysis['aggregated']
                    added_names = [e['name'] for e in agg.get('added_entities', [])]
                    if added_names:
                        # Prepend deep analysis entities
                        analysis['entities'] = added_names[:5] + analysis['entities'][:5]
                        analysis['entities'] = list(dict.fromkeys(analysis['entities']))[:10]
                    
                    # Use functional areas as features if none detected
                    if not analysis['features'] and agg.get('functional_areas'):
                        analysis['features'] = agg['functional_areas']
                
                # Store relations for commit body
                if deep_analysis.get('relations'):
                    analysis['relations'] = deep_analysis['relations']
            except Exception:
                pass  # Fall back to basic analysis
        
        # Fallback: Infer benefit using features if not set by deep analysis
        if not analysis.get('benefit'):
            analysis['benefit'] = self.abstraction.infer_benefit(
                analysis['entities'],
                analysis['primary_domain'],
                analysis['commit_type'],
                files=staged_files,
                features=analysis['features']
            )
        
        # Generate functional summary
        analysis['summary'] = self._generate_functional_summary(analysis)
        
        return analysis
    
    def _generate_functional_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable functional summary of changes."""
        parts = []
        
        features = analysis.get('features', [])
        entities = analysis.get('entities', [])
        files = analysis.get('files', [])
        added = analysis.get('added', 0)
        deleted = analysis.get('deleted', 0)
        
        # Feature-based summary
        if features:
            if len(features) == 1:
                parts.append(f"Added {features[0]} support")
            elif len(features) == 2:
                parts.append(f"Added {features[0]} and {features[1]} support")
            else:
                parts.append(f"Added {features[0]}, {features[1]}, and {len(features)-2} more features")
        
        # Entity-based summary
        elif entities:
            meaningful = [e for e in entities if len(e) > 2 and not e.startswith('test_')]
            if meaningful:
                if len(meaningful) <= 3:
                    parts.append(f"Implemented {', '.join(meaningful)}")
                else:
                    parts.append(f"Implemented {meaningful[0]}, {meaningful[1]}, and {len(meaningful)-2} more functions")
        
        # Docs detection
        doc_files = [f for f in files if f.endswith(('.md', '.rst', '.txt'))]
        if doc_files and len(doc_files) > len(files) // 2:
            doc_names = [Path(f).stem.upper() for f in doc_files[:3]]
            parts.append(f"Updated documentation ({', '.join(doc_names)})")
        
        # Test detection
        test_files = [f for f in files if 'test' in f.lower()]
        if test_files and not parts:
            parts.append(f"Added/updated {len(test_files)} test files")
        
        # Fallback
        if not parts:
            if added > deleted * 2:
                parts.append(f"Added new functionality ({added} lines)")
            elif deleted > added:
                parts.append(f"Refactored code ({deleted} lines removed)")
            else:
                parts.append(f"Updated {len(files)} files")
        
        return '; '.join(parts)
    
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

        files = analysis.get('files', [])
        is_docs_only = self._is_docs_only_change(files)

        # For docs-only changes, use simpler functional descriptions
        if is_docs_only:
            return self._generate_docs_message(analysis)

        # Route to appropriate abstraction level generator
        if level == 'high':
            return self._generate_high_abstraction_message(analysis)
        if level == 'medium':
            return self._generate_medium_abstraction_message(analysis)

        return self._generate_low_abstraction_message(analysis)

    def _is_docs_only_change(self, files: List[str]) -> bool:
        """Check if this is a documentation-only change."""
        if not files:
            return False
        return all(
            f.lower().endswith(('.md', '.rst', '.txt')) or
            'readme' in f.lower() or
            f.startswith('docs/')
            for f in files
        )

    def _generate_docs_message(self, analysis: Dict[str, Any]) -> str:
        """Generate commit message for documentation-only changes."""
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        files = analysis.get('files', [])
        file_count = analysis.get('file_count', 0)
        added = analysis.get('added', 0)

        if any('readme' in f.lower() for f in files):
            if added > 100:
                return f"docs({domain}): expand README with detailed examples"
            return f"docs({domain}): update README"
        if any('changelog' in f.lower() for f in files):
            return f"docs({domain}): update changelog"
        if file_count == 1:
            fname = Path(files[0]).stem.lower()
            return f"docs({domain}): update {fname} documentation"
        return f"docs({domain}): update documentation"

    def _generate_high_abstraction_message(self, analysis: Dict[str, Any]) -> str:
        """Generate message for high abstraction level."""
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        features = analysis.get('features', [])
        benefit = analysis.get('benefit', 'improved functionality')

        # Prefer features over entities for high abstraction
        if features:
            if len(features) == 1:
                return f"{commit_type}({domain}): add {features[0]} support"
            elif len(features) == 2:
                return f"{commit_type}({domain}): add {features[0]} and {features[1]} support"
            else:
                return f"{commit_type}({domain}): add {features[0]}, {features[1]} and more"

        return f"{commit_type}({domain}): {benefit}"

    def _generate_medium_abstraction_message(self, analysis: Dict[str, Any]) -> str:
        """Generate message for medium abstraction level."""
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        entities = analysis.get('entities', [])
        features = analysis.get('features', [])
        benefit = analysis.get('benefit', 'improved functionality')

        if features:
            feature_str = ', '.join(features[:3])
            return f"{commit_type}({domain}): add {feature_str}"

        if entities:
            meaningful = self._filter_meaningful_entities(entities)[:3]
            if meaningful:
                return f"{commit_type}({domain}): add {', '.join(meaningful)}"

        return f"{commit_type}({domain}): {benefit}"

    def _generate_low_abstraction_message(self, analysis: Dict[str, Any]) -> str:
        """Generate message for low abstraction level (fallback)."""
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        entities = analysis.get('entities', [])
        files = analysis.get('files', [])
        benefit = analysis.get('benefit', 'improved functionality')
        added = analysis.get('added', 0)
        deleted = analysis.get('deleted', 0)

        # Prefer benefit if meaningful
        if benefit and benefit != 'improved functionality':
            return f"{commit_type}({domain}): {benefit}"

        # Try to create functional description from entities
        if entities:
            meaningful = [e for e in entities if len(e) > 2][:2]
            if meaningful:
                verb = self.abstraction.get_action_verb(commit_type)
                return f"{commit_type}({domain}): {verb} {', '.join(meaningful)}"

        # Infer from file patterns
        return self._infer_message_from_files(analysis)

    def _filter_meaningful_entities(self, entities: List[str]) -> List[str]:
        """Filter out noise from entity names."""
        return [
            e for e in entities
            if len(e) > 2
            and not e.startswith('test_')
            and not re.match(r'^\[.*\]$', e)  # Skip [version] patterns
            and not re.match(r'^\d', e)  # Skip entities starting with numbers
        ]

    def _infer_message_from_files(self, analysis: Dict[str, Any]) -> str:
        """Infer commit message from file patterns."""
        commit_type = analysis.get('commit_type', 'feat')
        domain = analysis.get('primary_domain', 'core')
        files = analysis.get('files', [])
        added = analysis.get('added', 0)
        deleted = analysis.get('deleted', 0)

        if not files:
            verb = self.abstraction.get_action_verb(commit_type)
            return f"{commit_type}({domain}): {verb} code structure"

        # Check for common patterns
        if any('cli' in f.lower() for f in files):
            return f"{commit_type}({domain}): improve CLI functionality"
        if any('config' in f.lower() for f in files):
            return f"{commit_type}({domain}): update configuration handling"
        if any('test' in f.lower() for f in files):
            return f"{commit_type}({domain}): improve test coverage"
        if any(f.endswith('.md') for f in files):
            return f"{commit_type}({domain}): update documentation"

        # Fallback based on stats
        verb = self.abstraction.get_action_verb(commit_type)
        if added > deleted * 2:
            return f"{commit_type}({domain}): {verb} new functionality"
        elif deleted > added:
            return f"{commit_type}({domain}): refactor and simplify code"
        else:
            return f"{commit_type}({domain}): {verb} code structure"
    
    def generate_functional_body(self, analysis: Dict[str, Any] = None) -> str:
        """Generate a functional, human-readable commit body."""
        if analysis is None:
            analysis = self.analyze_changes()
        
        parts = []
        features = analysis.get('features', [])
        entities = analysis.get('entities', [])
        files = analysis.get('files', [])
        added = analysis.get('added', 0)
        deleted = analysis.get('deleted', 0)
        summary = analysis.get('summary', '')
        
        # Main summary
        if summary:
            parts.append(f"## Summary\n{summary}\n")
        
        # Features added
        if features:
            parts.append("## Features Added")
            for f in features:
                parts.append(f"- {f}")
            parts.append("")
        
        # Key functions/classes
        if entities:
            meaningful = [e for e in entities if len(e) > 2][:8]
            if meaningful:
                parts.append("## Key Changes")
                for e in meaningful:
                    parts.append(f"- `{e}`")
                parts.append("")
        
        # File changes by domain
        domains = analysis.get('domains', {})
        if domains:
            parts.append("## Changes by Area")
            for domain, domain_files in domains.items():
                if domain_files:
                    parts.append(f"- **{domain.title()}**: {len(domain_files)} files")
            parts.append("")
        
        # Stats
        parts.append(f"## Statistics")
        parts.append(f"- Files: {len(files)}")
        parts.append(f"- Lines: +{added}/-{deleted}")
        
        return '\n'.join(parts)
    
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
