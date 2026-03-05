"""Summary quality filter - extracted from enhanced_summary.py."""

import re
from typing import Dict, List, Tuple
from collections import defaultdict
from pathlib import Path


class SummaryQualityFilter:
    """Filter noise and improve summary quality."""
    
    NOISE_PATTERNS = [
        r'^_',                    # private methods
        r'_helper$',              # helper suffix
        r'_internal$',            # internal suffix  
        r'^_get_.*_name$',        # internal getters
        r'^_get_.*_name$',        # internal getters
        r'^_[a-z]+_[a-z]+$',      # short private methods
    ]
    
    NOISE_ROLES = [
        'internal helper',
        'private method',
    ]
    
    # Banned words for commit titles (too generic)
    BANNED_TITLE_WORDS = {
        'add', 'logging', 'testing', 'performance', 'update', 
        'improve', 'fix', 'misc', 'various', 'some', 'stuff',
        'formatting', 'auth', 'validation', 'changes', 'updates',
        'modifications', 'enhancements', 'tweaks', 'adjustments'
    }
    
    # Generic nodes to filter from dependency graphs
    GENERIC_NODES = {
        'base', '__init__', 'utils', 'common', 'helpers', 'constants',
        'types', 'exceptions', 'models', 'schemas'
    }
    
    # Domain patterns for smart file categorization
    DOMAIN_PATTERNS = {
        'analyzer': [r'analy[sz]', r'parse', r'scan', r'inspect'],
        'cli': [r'cli', r'command', r'arg'],
        'api': [r'api', r'endpoint', r'route', r'handler'],
        'model': [r'model', r'schema', r'entity'],
        'service': [r'service', r'manager', r'provider'],
        'util': [r'util', r'helper', r'tool'],
        'config': [r'config', r'setting', r'option'],
        'test': [r'test_', r'_test', r'spec'],
        'docs': [r'\.md$', r'readme', r'doc'],
        'quality': [r'quality', r'metric', r'coverage', r'dependen'],
    }
    
    # Intent classification patterns
    REFACTOR_PATTERNS = [
        r'analyzer', r'deep_', r'enhanced_', r'AST', r'refactor',
        r'restructure', r'reorganize', r'simplif', r'clean',
        r'framework', r'intelligence', r'git_'
    ]
    FEAT_PATTERNS = [
        r'new_', r'initial', r'support', r'implement', r'create'
    ]
    FIX_PATTERNS = [
        r'fix', r'bug', r'issue', r'error', r'patch', r'hotfix'
    ]
    
    # Capability priority scores (higher = more important)
    CAPABILITY_PRIORITY = {
        'ast_analysis': 10,
        'deep_analyzer': 10,
        'enhanced_summary': 9,
        'quality_metrics': 8,
        'multi_language': 7,
        'dependency_graph': 6,
        'cli_interface': 5,
        'output_formatting': 4,
        'config_system': 3,
        'changelog': 2,
    }
    
    # Max complexity delta percentage (cap absurd values)
    MAX_COMPLEXITY_PERCENT = 200
    
    def __init__(self):
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self.NOISE_PATTERNS]
        self._refactor_re = [re.compile(p, re.IGNORECASE) for p in self.REFACTOR_PATTERNS]
        self._feat_re = [re.compile(p, re.IGNORECASE) for p in self.FEAT_PATTERNS]
        self._fix_re = [re.compile(p, re.IGNORECASE) for p in self.FIX_PATTERNS]
    
    def is_noise(self, entity_name: str, role: str = '') -> bool:
        """Check if entity should be filtered as noise."""
        if role in self.NOISE_ROLES:
            return True
        return any(p.match(entity_name) for p in self._compiled)
    
    def filter_entities(self, entities: List[Dict]) -> List[Dict]:
        """Filter out noise entities."""
        return [e for e in entities if not self.is_noise(
            e.get('name', ''), e.get('role', '')
        )]
    
    def has_banned_words(self, title: str) -> List[str]:
        """Check if title contains banned words. Returns list of found banned words."""
        # Only evaluate the description part (after the conventional prefix).
        # This avoids false positives like banning the commit type token `fix`.
        desc = title.split(':', 1)[1] if ':' in title else title
        desc_words = set(re.findall(r"[a-zA-Z]+", desc.lower()))
        return sorted([w for w in self.BANNED_TITLE_WORDS if w in desc_words])
    
    def classify_intent(self, files: List[str], entities: List[Dict]) -> str:
        """Classify commit intent: feat, fix, refactor, docs, chore."""
        combined = ' '.join(files) + ' ' + ' '.join(e.get('name', '') for e in entities)
        
        # Check patterns
        refactor_score = sum(1 for p in self._refactor_re if p.search(combined))
        feat_score = sum(1 for p in self._feat_re if p.search(combined))
        fix_score = sum(1 for p in self._fix_re if p.search(combined))
        
        # Check for docs
        if all(f.endswith('.md') or 'doc' in f.lower() for f in files):
            return 'docs'
        
        # Check for chore (config only)
        if all(f.endswith(('.yaml', '.toml', '.json', '.ini')) for f in files):
            return 'chore'
        
        # Return highest scoring intent
        scores = {'refactor': refactor_score, 'feat': feat_score, 'fix': fix_score}
        if max(scores.values()) == 0:
            return 'refactor'  # Default to refactor for code changes
        return max(scores, key=scores.get)
    
    def prioritize_capabilities(self, capabilities: List[Dict]) -> List[Dict]:
        """Sort capabilities by priority, highest first."""
        def get_priority(cap: Dict) -> int:
            cap_id = cap.get('id', '')
            return self.CAPABILITY_PRIORITY.get(cap_id, 0)
        
        return sorted(capabilities, key=get_priority, reverse=True)
    
    def format_complexity_delta(self, old_complexity: int, new_complexity: int) -> Tuple[str, str]:
        """Format complexity change as interpretable metric with sane caps.
        
        Returns: (emoji, description)
        """
        if old_complexity == 0:
            return '➡️', "New module (baseline established)"
        
        delta = new_complexity - old_complexity
        delta_pct = (delta / old_complexity) * 100
        
        # Cap absurd values (>200% = structural change, not real complexity)
        if abs(delta_pct) > self.MAX_COMPLEXITY_PERCENT:
            return '➡️', "Large structural change (normalized)"
        
        if delta_pct < -10:
            return '📉', f"-{abs(delta_pct):.0f}% complexity (refactor win)"
        elif delta_pct > 50:
            return '⚠️', f"+{delta_pct:.0f}% complexity (monitor)"
        elif delta_pct > 10:
            return '📊', f"+{delta_pct:.0f}% complexity (new features)"
        else:
            return '➡️', "Stable complexity"
    
    def dedupe_relations(self, relations: List[Dict]) -> List[Dict]:
        """Remove duplicate relations, keep unique edges only."""
        seen = set()
        unique = []
        for r in relations:
            edge = (r.get('from', ''), r.get('to', ''))
            if edge not in seen and edge[0] != edge[1]:  # No self-loops
                seen.add(edge)
                unique.append(r)
        return unique[:10]  # Cap at 10 relations
    
    def dedupe_files(self, files: List[str]) -> List[str]:
        """Remove duplicate files, preserve order."""
        seen = set()
        unique = []
        for f in files:
            fname = Path(f).name
            if fname not in seen:
                seen.add(fname)
                unique.append(f)
        return unique
    
    def categorize_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Smart domain-based file categorization."""
        categories = defaultdict(list)
        
        for f in files:
            fname = f.lower()
            stem = Path(f).stem.lower()
            matched = False
            
            # Try domain patterns first
            for domain, patterns in self.DOMAIN_PATTERNS.items():
                if any(re.search(p, fname) for p in patterns):
                    categories[domain].append(f)
                    matched = True
                    break
            
            if not matched:
                # Fallback categorization
                if fname.endswith('.md'):
                    categories['docs'].append(f)
                elif fname.endswith(('.yaml', '.yml', '.toml', '.json', '.ini')):
                    categories['config'].append(f)
                elif 'test' in fname:
                    categories['test'].append(f)
                else:
                    categories['core'].append(f)
        
        return {k: v for k, v in categories.items() if v}
    
    def filter_generic_nodes(self, relations: List[Dict]) -> List[Dict]:
        """Remove generic nodes from dependency graph."""
        return [
            r for r in relations
            if r.get('from', '').lower() not in self.GENERIC_NODES
            and r.get('to', '').lower() not in self.GENERIC_NODES
        ]
    
    def format_net_lines(self, added: int, deleted: int) -> Tuple[str, str]:
        """Format NET lines change with proper interpretation.
        
        Returns: (emoji, description)
        """
        net = added - deleted
        total = added + deleted
        
        if total == 0:
            return '➡️', "No line changes"
        
        deletion_pct = (deleted / total) * 100 if total else 0
        if deleted > 0 and deletion_pct >= 10:
            if deleted >= 250 and deletion_pct >= 20:
                return '📉', (
                    f"{deletion_pct:.0f}% code reduction (-{deleted} lines refactored, +{added}/-{deleted}, NET {net})"
                )
            if net < 0:
                return '📉', (
                    f"+{added}/-{deleted} lines (NET {net}, {deletion_pct:.0f}% churn deletions)"
                )
            if deleted >= 250:
                return '📉', (
                    f"+{added}/-{deleted} lines (NET +{net}, {deletion_pct:.0f}% churn deletions)"
                )
            return '📊', f"+{added}/-{deleted} lines (NET +{net}, {deletion_pct:.0f}% churn deletions)"
        if net < 0:
            return '📉', f"+{added}/-{deleted} lines (NET {net})"
        if net > 100:
            return '📈', f"+{added}/-{deleted} lines (NET +{net})"
        if net > 0:
            return '📊', f"+{added}/-{deleted} lines (NET +{net})"
        return '➡️', f"+{added}/-{deleted} lines (NET {net})"
    
    def classify_intent_smart(self, files: List[str], entities: List[Dict], 
                               added: int = 0, deleted: int = 0) -> str:
        """Smart intent classification using multiple signals."""
        combined = ' '.join(files) + ' ' + ' '.join(e.get('name', '') for e in entities)
        
        # Signal 1: Deletions/churn signal (refactor often includes large deletions)
        net = added - deleted
        churn_total = added + deleted
        deletion_pct = (deleted / churn_total) * 100 if churn_total else 0

        if deleted >= 1000:
            return 'refactor'
        if deleted >= 250 and deletion_pct >= 20:
            return 'refactor'
        if net < -100:  # Significant net reduction
            return 'refactor'
        
        # Signal 2: File patterns
        refactor_score = sum(1 for p in self._refactor_re if p.search(combined))
        feat_score = sum(1 for p in self._feat_re if p.search(combined))
        fix_score = sum(1 for p in self._fix_re if p.search(combined))
        
        # Signal 3: File count vs net lines ratio
        if len(files) > 10 and net < 0:
            refactor_score += 3  # Many files with net negative = refactor
        
        # Check for docs-only
        if all(f.endswith('.md') or 'doc' in f.lower() for f in files):
            return 'docs'
        
        # Check for config-only
        if all(f.endswith(('.yaml', '.toml', '.json', '.ini')) for f in files):
            return 'chore'
        
        scores = {'refactor': refactor_score, 'feat': feat_score, 'fix': fix_score}
        if max(scores.values()) == 0:
            return 'refactor' if net <= 0 else 'feat'

        # If refactor patterns are present and deletions are meaningful, prefer refactor.
        if deleted >= 100 and refactor_score >= feat_score and refactor_score >= fix_score:
            return 'refactor'
        return max(scores, key=scores.get)
    
    def generate_architecture_title(self, files: List[str], categories: Dict) -> str:
        """Generate architecture-aware title based on file patterns."""
        stems = [Path(f).stem.lower() for f in files]
        
        # Detect framework type
        if any('analyzer' in s or 'analysis' in s for s in stems):
            if len(files) > 10:
                return "complete analysis framework"
            return "analysis engine improvements"
        
        if any('git' in s for s in stems):
            return "git integration framework"
        
        if 'cli' in categories and len(categories.get('cli', [])) > 2:
            return "CLI interface overhaul"
        
        if 'api' in categories:
            return "API layer enhancements"
        
        # Fallback based on dominant category
        if categories:
            dominant = max(categories.items(), key=lambda x: len(x[1]))
            return f"{dominant[0]} module improvements"
        
        return "configuration and maintenance updates"


__all__ = ['SummaryQualityFilter']
