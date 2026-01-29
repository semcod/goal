"""Enhanced summary generator for functional commit messages.

Transforms technical code changes into business value descriptions.
Provides role mapping, relation detection, and quality metrics.
"""

import re
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from pathlib import Path

try:
    from .deep_analyzer import CodeChangeAnalyzer
except ImportError:
    from deep_analyzer import CodeChangeAnalyzer


class SummaryQualityFilter:
    """Filter noise and improve summary quality."""
    
    NOISE_PATTERNS = [
        r'^_',                    # private methods
        r'_helper$',              # helper suffix
        r'_internal$',            # internal suffix  
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


class QualityValidator:
    """Validate commit summary against quality gates."""
    
    # Quality gate thresholds
    GATES = {
        'max_complexity_percent': 200,
        'max_duplicate_relations': 0,
        'min_unique_files_ratio': 0.8,
        'min_capabilities': 1,
        'max_banned_words': 0,
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.filter = SummaryQualityFilter()
        
        quality = self.config.get('quality', {})
        commit_summary = quality.get('commit_summary', {})
        enhanced_summary = quality.get('enhanced_summary', {})
        
        self.min_value_words = commit_summary.get('min_value_words', 3)
        self.max_generic_terms = commit_summary.get('max_generic_terms', 0)
        self.required_metrics = commit_summary.get('required_metrics', 2)
        self.relation_threshold = commit_summary.get('relation_threshold', 0.7)
        
        generic_terms = commit_summary.get('generic_terms')
        if isinstance(generic_terms, list) and generic_terms:
            self.filter.BANNED_TITLE_WORDS = set(self.filter.BANNED_TITLE_WORDS) | {t.lower() for t in generic_terms}
        
        self.enhanced_enabled = bool(enhanced_summary.get('enabled', True))
        
        gates = quality.get('gates', {})
        for key, default in self.GATES.items():
            setattr(self, key, gates.get(key, default))
    
    def validate(self, summary: Dict[str, Any], files: List[str]) -> Dict[str, Any]:
        """Validate summary against all quality gates.
        
        Returns: {valid: bool, errors: [], warnings: [], score: int, fixes: []}
        """
        errors = []
        warnings = []
        fixes = []
        
        title = summary.get('title', '')
        metrics = summary.get('metrics', {})
        relations = summary.get('relations', {}).get('relations', [])
        capabilities = summary.get('capabilities', [])
        
        intent = summary.get('intent')
        if not intent and title:
            m = re.match(r'^(\w+)\([^)]*\):', title)
            if m:
                intent = m.group(1)
        
        added = metrics.get('lines_added', 0)
        deleted = metrics.get('lines_deleted', 0)
        
        # 1. Check banned words
        banned = self.filter.has_banned_words(title)
        if banned:
            errors.append(f"Banned words in title: {banned}")
            fixes.append(('remove_banned_words', banned))

        # 1a. Check generic term count in the title description
        generic_terms = self.config.get('quality', {}).get('commit_summary', {}).get('generic_terms')
        if isinstance(generic_terms, list) and generic_terms:
            desc = title.split(':', 1)[1] if ':' in title else title
            desc_words = set(re.findall(r"[a-zA-Z]+", desc.lower()))
            generic_count = sum(1 for t in generic_terms if t.lower() in desc_words)
            if generic_count > self.max_generic_terms:
                errors.append(f"Title contains {generic_count} generic terms (max {self.max_generic_terms})")
                fixes.append(('reduce_generic_terms', generic_count))

        # 1c. Minimum value words
        desc = title.split(':', 1)[1] if ':' in title else title
        desc_word_count = len(re.findall(r"[a-zA-Z]+", desc.lower()))
        if desc_word_count < self.min_value_words:
            errors.append(f"Title too short ({desc_word_count} words, need {self.min_value_words})")
            fixes.append(('expand_title', desc_word_count))
        
        # 1b. Wrong intent vs refactor signals
        try:
            entities = []
            agg = summary.get('analysis', {}).get('aggregated', {}) if isinstance(summary.get('analysis'), dict) else {}
            entities = agg.get('added_entities', []) if isinstance(agg, dict) else []
            smart_intent = self.filter.classify_intent_smart(files, entities, added, deleted)
            if intent == 'feat' and smart_intent == 'refactor':
                errors.append("Wrong intent: feat → refactor (refactor patterns or code reduction detected)")
                fixes.append(('reclassify_intent', 'refactor'))
            if intent in ('feat', 'fix') and (deleted >= 250 and smart_intent == 'refactor'):
                errors.append("Hidden refactor: large deletions with non-refactor intent")
                fixes.append(('fix_hidden_refactor', deleted))
        except Exception:
            pass
        
        # 2. Check complexity (already capped in format_complexity_delta)
        old_cc = metrics.get('old_complexity', 1)
        new_cc = metrics.get('new_complexity', old_cc)
        if old_cc > 0:
            delta_pct = abs((new_cc - old_cc) / old_cc * 100)
            if delta_pct > self.max_complexity_percent:
                warnings.append(f"Complexity {delta_pct:.0f}% > {self.max_complexity_percent}% (will be normalized)")
                fixes.append(('normalize_complexity', delta_pct))
        
        # 3. Check duplicate relations
        unique_relations = self.filter.dedupe_relations(relations)
        duplicates = len(relations) - len(unique_relations)
        if duplicates > self.max_duplicate_relations:
            errors.append(f"Duplicate relations: {duplicates}")
            fixes.append(('dedupe_relations', duplicates))
        
        # 3b. Check generic nodes in relations
        clean_relations = self.filter.filter_generic_nodes(relations)
        generic_count = len(relations) - len(clean_relations)
        
        if generic_count > 1:  # Allow max 1 generic node
            errors.append(f"Generic nodes in graph: {generic_count} (base, utils, etc.)")
            fixes.append(('filter_generic_nodes', generic_count))
        
        # 4. Check duplicate files
        unique_files = self.filter.dedupe_files(files)
        if len(files) > 0:
            unique_ratio = len(unique_files) / len(files)
            if unique_ratio < self.min_unique_files_ratio:
                dup_count = len(files) - len(unique_files)
                errors.append(f"Duplicate files: {dup_count}")
                fixes.append(('dedupe_files', dup_count))
        
        # 5. Check capabilities
        if len(capabilities) < self.min_capabilities:
            errors.append(f"Only {len(capabilities)} capabilities (need {self.min_capabilities})")
            fixes.append(('add_capabilities', len(capabilities)))

        # 6. Check that the body exposes metrics (enterprise-grade preview)
        body = summary.get('body', '')
        if body:
            metric_keywords = ['NET', 'Relations:', 'Test coverage', 'score', '%', 'deletions']
            metric_count = sum(1 for kw in metric_keywords if kw.lower() in body.lower())
            if metric_count < self.required_metrics:
                errors.append(f"Only {metric_count} metrics found in body (need {self.required_metrics})")
                fixes.append(('expose_metrics', metric_count))

        # 7. Enhanced summary minimum value score
        min_value_score = self.config.get('quality', {}).get('enhanced_summary', {}).get('min_value_score')
        if isinstance(min_value_score, int):
            value_score = metrics.get('value_score')
            if isinstance(value_score, int) and value_score < min_value_score:
                errors.append(f"Value score {value_score}/100 < {min_value_score}/100")
                fixes.append(('raise_value_score', value_score))
        
        # Calculate score
        score = 100
        score -= len(errors) * 20
        score -= len(warnings) * 5
        score = max(0, min(100, score))
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'fixes': fixes,
            'score': score
        }
    
    def auto_fix(self, summary: Dict[str, Any], files: List[str], 
                 added: int = 0, deleted: int = 0) -> Dict[str, Any]:
        """Auto-fix summary issues and return corrected summary."""
        fixed = summary.copy()
        applied_fixes = []
        
        # Get file categories for architecture title
        categories = self.filter.categorize_files(files)
        
        # 1. Remove banned words and generate architecture title
        title = fixed.get('title', '')
        banned = self.filter.has_banned_words(title)
        if banned:
            # Generate architecture-aware title instead of just removing words
            arch_title = self.filter.generate_architecture_title(files, categories)
            
            # Extract scope from original title if present
            scope_match = re.search(r'\(([^)]+)\)', title)
            scope = scope_match.group(1) if scope_match else 'core'
            
            # Reclassify intent based on net lines
            entities = summary.get('analysis', {}).get('aggregated', {}).get('added_entities', [])
            intent = self.filter.classify_intent_smart(files, entities, added, deleted)
            
            fixed['title'] = f"{intent}({scope}): {arch_title}"
            fixed['intent'] = intent
            applied_fixes.append(f"Fixed title: banned words {banned} → '{arch_title}'")

        # 1b. Fix wrong intent even if there are no banned words
        title = fixed.get('title', '')
        m = re.match(r'^(\w+)\(([^)]*)\):\s*(.*)$', title)
        if m:
            current_intent = m.group(1)
            scope = m.group(2)
            desc = m.group(3)
            entities = summary.get('analysis', {}).get('aggregated', {}).get('added_entities', [])
            smart_intent = self.filter.classify_intent_smart(files, entities, added, deleted)
            if current_intent != smart_intent and smart_intent == 'refactor':
                fixed['title'] = f"{smart_intent}({scope}): {desc}"
                fixed['intent'] = smart_intent
                applied_fixes.append(f"Fixed intent: {current_intent} → {smart_intent}")
        
        # 2. Dedupe and clean relations (remove generic nodes)
        if 'relations' in fixed and 'relations' in fixed['relations']:
            original_count = len(fixed['relations']['relations'])
            relations = fixed['relations']['relations']
            
            # First filter generic nodes
            relations = self.filter.filter_generic_nodes(relations)
            generic_removed = original_count - len(relations)
            
            # Then dedupe
            relations = self.filter.dedupe_relations(relations)
            fixed['relations']['relations'] = relations
            
            new_count = len(relations)
            if original_count != new_count:
                applied_fixes.append(f"Cleaned relations: {original_count} → {new_count} "
                                    f"({generic_removed} generic nodes removed)")
        
        # 3. Dedupe files
        original_files = len(files)
        unique_files = self.filter.dedupe_files(files)
        if original_files != len(unique_files):
            applied_fixes.append(f"Deduped files: {original_files} → {len(unique_files)}")
        
        # 4. Prioritize capabilities
        if 'capabilities' in fixed:
            fixed['capabilities'] = self.filter.prioritize_capabilities(fixed['capabilities'])
            applied_fixes.append("Reordered capabilities by priority")
        
        # 5. Store NET lines info
        if added or deleted:
            net = added - deleted
            emoji, desc = self.filter.format_net_lines(added, deleted)
            fixed['net_lines'] = {'added': added, 'deleted': deleted, 'net': net, 
                                  'emoji': emoji, 'description': desc}
            applied_fixes.append(f"Added NET lines: {desc}")
        
        # 6. Smart file categorization
        fixed['categories'] = categories
        cat_summary = ', '.join(f"{len(v)} {k}" for k, v in categories.items())
        applied_fixes.append(f"Categorized: {cat_summary}")
        
        fixed['applied_fixes'] = applied_fixes
        return fixed


class EnhancedSummaryGenerator:
    """Generate business-value focused commit summaries."""
    
    # Entity name patterns -> functional roles
    ROLE_PATTERNS = {
        # Analysis patterns
        r'_analyze_(python|js|generic)_diff': 'language-specific code analyzer',
        r'CodeChangeAnalyzer': 'AST-based change detector',
        r'analyze_file_diff': 'diff analysis engine',
        r'aggregate_changes': 'change aggregator',
        r'detect_relations': 'dependency graph builder',
        
        # Summary patterns
        r'generate_functional_summary': 'business value summarizer',
        r'generate.*message': 'commit message generator',
        r'generate.*summary': 'summary generator',
        r'infer_functional_value': 'value inference engine',
        r'EnhancedSummaryGenerator': 'enterprise changelog generator',
        
        # Config patterns
        r'GoalConfig': 'configuration manager',
        r'load_config': 'config loader',
        r'save_config': 'config persistence',
        r'validate': 'validation engine',
        
        # CLI patterns
        r'@click\.command': 'CLI command',
        r'@click\.option': 'CLI option',
        r'main': 'entry point',
        r'push': 'push workflow',
        r'commit': 'commit workflow',
        
        # Formatter patterns
        r'format_.*result': 'output formatter',
        r'MarkdownFormatter': 'markdown renderer',
        
        # Quality patterns
        r'_calculate_complexity': 'complexity analyzer',
        r'complexity': 'code quality metrics',
        r'coverage': 'test coverage analyzer',
    }
    
    # Value patterns: signature -> (capability name, business impact)
    VALUE_PATTERNS = {
        'ast_analysis': {
            'signatures': ['ast.parse', 'ast.walk', 'libcst', 'tree-sitter', 'AST'],
            'capability': 'deep code analysis engine',
            'impact': 'intelligent change detection'
        },
        'dependency_graph': {
            'signatures': ['networkx', 'relations', 'dependencies', 'graph', 'detect_relations'],
            'capability': 'code relationship mapping',
            'impact': 'architecture understanding'
        },
        'quality_metrics': {
            'signatures': ['radon', 'cyclomatic', 'complexity', 'coverage', 'metrics'],
            'capability': 'code quality metrics',
            'impact': 'maintainability tracking'
        },
        'multi_language': {
            'signatures': ['_analyze_python', '_analyze_js', 'language', 'parser'],
            'capability': 'multi-language support',
            'impact': 'universal code analysis'
        },
        'config_system': {
            'signatures': ['yaml', 'config', 'GoalConfig', 'settings'],
            'capability': 'configuration management',
            'impact': 'customizable workflows'
        },
        'cli_interface': {
            'signatures': ['click', 'command', 'option', 'argument'],
            'capability': 'CLI interface',
            'impact': 'improved user experience'
        },
        'output_formatting': {
            'signatures': ['markdown', 'format', 'render', 'template'],
            'capability': 'output formatting',
            'impact': 'readable reports'
        },
        'changelog': {
            'signatures': ['changelog', 'CHANGELOG', 'version', 'release'],
            'capability': 'changelog generation',
            'impact': 'release documentation'
        },
    }
    
    # Generic terms to avoid in summaries
    GENERIC_TERMS = {
        'update', 'improve', 'enhance', 'fix', 'change', 'modify',
        'cleaner', 'better', 'refactor', 'cleanup', 'misc'
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.analyzer = CodeChangeAnalyzer()
        self.quality_filter = SummaryQualityFilter()
        self._cache = {}
    
    def map_entity_to_role(self, entity_name: str) -> str:
        """Map a code entity name to its functional role."""
        for pattern, role in self.ROLE_PATTERNS.items():
            if re.search(pattern, entity_name, re.IGNORECASE):
                return role
        
        # Infer role from naming conventions
        if entity_name.startswith('test_'):
            return 'test case'
        if entity_name.startswith('_'):
            return 'internal helper'
        if entity_name.endswith('Handler'):
            return 'request handler'
        if entity_name.endswith('Manager'):
            return 'resource manager'
        if entity_name.endswith('Factory'):
            return 'object factory'
        if entity_name.endswith('Builder'):
            return 'builder pattern'
        if entity_name.endswith('Validator'):
            return 'input validator'
        if entity_name.endswith('Parser'):
            return 'parser'
        if entity_name.endswith('Generator'):
            return 'generator'
        if entity_name.endswith('Analyzer'):
            return 'analyzer'
        
        return entity_name  # Return as-is if no pattern matches
    
    def detect_capabilities(self, files: List[str], diff_content: str) -> List[Dict[str, str]]:
        """Detect capabilities from files and diff content."""
        capabilities = []
        seen = set()
        
        combined_text = diff_content + ' ' + ' '.join(files)
        
        for cap_id, cap_info in self.VALUE_PATTERNS.items():
            for sig in cap_info['signatures']:
                if sig.lower() in combined_text.lower() and cap_id not in seen:
                    capabilities.append({
                        'id': cap_id,
                        'capability': cap_info['capability'],
                        'impact': cap_info['impact']
                    })
                    seen.add(cap_id)
                    break
        
        return capabilities
    
    def detect_file_relations(self, files: List[str], diff_content: str = '') -> Dict[str, Any]:
        """Detect import/dependency relations between changed files."""
        relations = []
        file_domains = {}
        
        # Map files to domains
        for f in files:
            domain = self._infer_domain(f)
            file_domains[f] = domain
        
        # Detect imports between files
        import_pattern = r'from\s+\.?(\w+)\s+import|import\s+\.?(\w+)'
        
        for f in files:
            if not f.endswith('.py'):
                continue
            
            try:
                with open(f, 'r') as fp:
                    content = fp.read()
            except:
                continue
            
            imports = re.findall(import_pattern, content)
            for imp in imports:
                imp_name = imp[0] or imp[1]
                # Check if imported module is in changed files
                for other_f in files:
                    other_name = Path(other_f).stem
                    if imp_name == other_name and f != other_f:
                        relations.append({
                            'from': Path(f).stem,
                            'to': other_name,
                            'type': 'imports'
                        })
        
        # Build relation chain
        chain = self._build_relation_chain(relations)
        
        return {
            'relations': relations,
            'chain': chain,
            'domains': file_domains,
            'ascii': self._render_relations_ascii(relations, files)
        }
    
    def _infer_domain(self, filepath: str) -> str:
        """Infer domain/area from filepath."""
        path_lower = filepath.lower()
        
        if 'test' in path_lower:
            return 'test'
        if 'doc' in path_lower or path_lower.endswith('.md'):
            return 'docs'
        if 'config' in path_lower or path_lower.endswith(('.yaml', '.toml', '.json')):
            return 'config'
        if 'cli' in path_lower:
            return 'cli'
        if 'api' in path_lower:
            return 'api'
        if 'db' in path_lower or 'model' in path_lower:
            return 'data'
        if 'format' in path_lower or 'render' in path_lower:
            return 'output'
        if 'analyzer' in path_lower or 'parse' in path_lower:
            return 'analysis'
        
        return 'core'
    
    def _build_relation_chain(self, relations: List[Dict]) -> str:
        """Build a chain representation of relations."""
        if not relations:
            return ''
        
        # Build adjacency
        adj = defaultdict(set)
        for r in relations:
            adj[r['from']].add(r['to'])
        
        # Find roots (not imported by anyone)
        all_targets = {r['to'] for r in relations}
        all_sources = {r['from'] for r in relations}
        roots = all_sources - all_targets
        
        if not roots:
            roots = all_sources
        
        # Build chain string
        chains = []
        for root in roots:
            chain = [root]
            current = root
            visited = {root}
            while adj[current] - visited:
                next_node = sorted(adj[current] - visited)[0]
                chain.append(next_node)
                visited.add(next_node)
                current = next_node
            chains.append('→'.join(chain))
        
        return ', '.join(chains)
    
    def _render_relations_ascii(self, relations: List[Dict], files: List[str]) -> str:
        """Render file relations as ASCII art (deduplicated)."""
        if not relations:
            return ''
        
        lines = []
        
        # Group by source with deduplicated targets
        by_source = defaultdict(set)  # Use set to auto-dedupe
        for r in relations:
            by_source[r['from']].add(r['to'])
        
        for source, targets in sorted(by_source.items()):
            targets_list = sorted(targets)  # Sort for consistent output
            if len(targets_list) == 1:
                lines.append(f"{source}.py → {targets_list[0]}.py")
            else:
                lines.append(f"{source}.py ──┬──> {targets_list[0]}.py")
                for t in targets_list[1:-1]:
                    lines.append(f"{'':>{len(source)+4}}├──> {t}.py")
                lines.append(f"{'':>{len(source)+4}}└──> {targets_list[-1]}.py")
        
        return '\n'.join(lines)
    
    def calculate_quality_metrics(self, analysis: Dict[str, Any], 
                                   files: List[str]) -> Dict[str, Any]:
        """Calculate quality metrics for the changes."""
        metrics = {
            'functional_coverage': 0,
            'relation_density': 0.0,
            'complexity_delta': 0,
            'test_impact': 0,
            'value_score': 0
        }
        
        aggregated = analysis.get('aggregated', {})
        
        # Functional coverage: detected areas vs total entities
        areas = len(aggregated.get('functional_areas', []))
        total_entities = (len(aggregated.get('added_entities', [])) + 
                         len(aggregated.get('modified_entities', [])))
        if total_entities > 0:
            metrics['functional_coverage'] = min(100, int((areas / max(total_entities, 1)) * 100 + 50))
        
        # Relation density
        relations = analysis.get('relations', [])
        if files:
            metrics['relation_density'] = round(len(relations) / len(files), 1)
        
        # Complexity delta
        metrics['complexity_delta'] = aggregated.get('complexity_change', 0)
        
        # Test impact
        test_entities = [e for e in aggregated.get('added_entities', []) 
                        if e.get('name', '').startswith('test_')]
        metrics['test_impact'] = len(test_entities) * 5  # 5% per test
        
        # Value score (composite)
        value_score = 50  # Base
        value_score += min(30, areas * 10)  # Areas
        value_score += min(10, len(relations) * 5)  # Relations
        value_score += min(10, metrics['test_impact'])  # Tests
        if metrics['complexity_delta'] < 0:
            value_score += min(10, abs(metrics['complexity_delta']))  # Simplification bonus
        metrics['value_score'] = min(100, value_score)
        
        return metrics
    
    def generate_value_title(self, capabilities: List[Dict], 
                             analysis: Dict[str, Any],
                             files: List[str] = None) -> str:
        """Generate a business-value focused title.
        
        Priority:
        1. Specific pipeline/system name if detectable
        2. Primary capability with version/qualifier
        3. Inferred functional value
        """
        files = files or []
        aggregated = analysis.get('aggregated', {})
        areas = aggregated.get('functional_areas', [])
        
        # Check for specific system patterns
        file_stems = [Path(f).stem.lower() for f in files]
        
        # Detect analysis pipeline
        if any('analyzer' in s or 'analysis' in s for s in file_stems):
            if any('deep' in s or 'smart' in s for s in file_stems):
                return "intelligent code analysis pipeline"
            return "code analysis engine"
        
        # Detect commit system
        if any('commit' in s for s in file_stems):
            if any('smart' in s for s in file_stems):
                return "smart commit generation system"
            return "commit message generator"
        
        # Detect CLI system
        if 'cli' in areas and any('cli' in s for s in file_stems):
            return "CLI interface improvements"
        
        # Detect config system
        if 'configuration' in areas:
            return "configuration management system"
        
        # Use capabilities if meaningful
        if capabilities:
            primary = capabilities[0]
            cap_name = primary['capability']
            
            # Make capability name more specific
            if len(capabilities) >= 3:
                return f"{cap_name} with {len(capabilities)-1} supporting modules"
            return cap_name
        
        # Fallback to inferred value
        return analysis.get('functional_value', 'code improvements')
    
    def generate_enhanced_summary(self, files: List[str], 
                                   diff_content: str = '',
                                   lines_added: int = 0, lines_deleted: int = 0) -> Dict[str, Any]:
        """Generate complete enhanced summary with business value focus."""
        # Dedupe files first
        files = self.quality_filter.dedupe_files(files)
        
        # Extract line stats from diff if not provided
        if not lines_added and not lines_deleted and diff_content:
            lines_added = diff_content.count('\n+') - diff_content.count('\n+++')
            lines_deleted = diff_content.count('\n-') - diff_content.count('\n---')
        
        # Run deep analysis
        analysis = self.analyzer.generate_functional_summary(files)
        
        # Detect capabilities and prioritize them
        capabilities = self.detect_capabilities(files, diff_content)
        capabilities = self.quality_filter.prioritize_capabilities(capabilities)
        
        # Detect relations and dedupe them
        relations = self.detect_file_relations(files, diff_content)
        relations['relations'] = self.quality_filter.dedupe_relations(relations.get('relations', []))
        # Remove generic nodes, then rebuild chain and ASCII after cleaning
        relations['relations'] = self.quality_filter.filter_generic_nodes(relations['relations'])
        relations['chain'] = self._build_relation_chain(relations['relations'])
        relations['ascii'] = self._render_relations_ascii(relations['relations'], files)
        
        # Calculate metrics
        metrics = self.calculate_quality_metrics(analysis, files)
        
        # Map entities to roles (filter noise)
        aggregated = analysis.get('aggregated', {})
        roles = []
        for entity in aggregated.get('added_entities', [])[:10]:
            name = entity.get('name', '')
            role = self.map_entity_to_role(name)
            
            # Skip noise entities
            if self.quality_filter.is_noise(name, role):
                continue
                
            if role != name:  # Only if mapped to meaningful role
                roles.append({
                    'name': name,
                    'role': role,
                    'type': entity.get('type', 'function')
                })
        
        # Limit to top 5 after filtering
        roles = roles[:5]
        
        # Calculate old/new complexity for interpretable metrics
        file_analyses = analysis.get('file_analyses', [])
        old_complexity = sum(
            sum(e.get('complexity', 1) for e in fa.get('removed_entities', [])) +
            sum(e.get('complexity', 1) for e in fa.get('modified_entities', []))
            for fa in file_analyses
        ) or 1
        new_complexity = old_complexity + aggregated.get('complexity_change', 0)
        metrics['old_complexity'] = old_complexity
        metrics['new_complexity'] = new_complexity
        metrics['lines_added'] = lines_added
        metrics['lines_deleted'] = lines_deleted
        
        # Generate title
        title = self.generate_value_title(capabilities, analysis, files)
        
        # Build formatted output
        body = self._format_enhanced_body(
            capabilities=capabilities,
            roles=roles,
            relations=relations,
            metrics=metrics,
            files=files,
            aggregated=aggregated
        )
        
        # Classify intent (use line stats so refactors can't become "feat")
        intent = self.quality_filter.classify_intent_smart(
            files,
            aggregated.get('added_entities', []),
            added=lines_added,
            deleted=lines_deleted,
        )
        
        return {
            'title': title,
            'body': body,
            'intent': intent,
            'capabilities': capabilities,
            'roles': roles,
            'relations': relations,
            'metrics': metrics,
            'analysis': analysis,
            'files': files  # Include deduped files for validation
        }
    
    def _format_enhanced_body(self, capabilities: List[Dict],
                               roles: List[Dict],
                               relations: Dict,
                               metrics: Dict,
                               files: List[str],
                               aggregated: Dict) -> str:
        """Format the enhanced commit body."""
        sections = []
        
        # NEW CAPABILITIES section
        if capabilities:
            cap_lines = ["NEW CAPABILITIES:"]
            for i, cap in enumerate(capabilities[:5]):
                prefix = "├──" if i < len(capabilities) - 1 else "└──"
                cap_lines.append(f"{prefix} {cap['capability']}: {cap['impact']}")
            sections.append('\n'.join(cap_lines))
        
        # FUNCTIONAL ROLES section (instead of raw entity names)
        if roles:
            role_lines = ["FUNCTIONAL COMPONENTS:"]
            for role in roles[:5]:
                role_lines.append(f"✅ {role['role']} ({role['name']})")
            sections.append('\n'.join(role_lines))

        # ARCHITECTURE section - show concrete file names per category
        categorized = self.quality_filter.categorize_files(files)
        if categorized:
            icon_map = {
                'analyzer': '🔬',
                'cli': '🤖',
                'quality': '📊',
                'test': '🧪',
                'config': '⚙️',
                'docs': '📚',
                'api': '🌐',
                'service': '🧠',
                'model': '📦',
                'util': '🔧',
                'core': '🧩',
            }
            layer_keys = {'analyzer', 'cli', 'quality'}
            header = "3-LAYER ARCHITECTURE:" if (set(categorized.keys()) & layer_keys) else "ARCHITECTURE:"
            arch_lines = [header]
            for category, cat_files in sorted(categorized.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                names = [Path(f).name for f in cat_files]
                shown = names[:4]
                suffix = f", +{len(names) - 4} more" if len(names) > 4 else ""
                icon = icon_map.get(category, '📦')
                arch_lines.append(f"{icon} {category} ({len(names)} files): {', '.join(shown)}{suffix}")
            sections.append('\n'.join(arch_lines))
        
        # IMPACT METRICS section
        if metrics:
            metric_lines = ["IMPACT:"]
            
            # NET lines change (primary metric for refactors)
            added = metrics.get('lines_added', 0)
            deleted = metrics.get('lines_deleted', 0)
            if added or deleted:
                emoji, desc = self.quality_filter.format_net_lines(added, deleted)
                metric_lines.append(f"{emoji} {desc}")
            
            # Show relation count 
            rel_count = len(relations.get('relations', []))
            if rel_count > 0:
                chain = relations.get('chain', '')
                if chain:
                    metric_lines.append(f"🔗 {chain} ({rel_count} clean relations)")
                else:
                    metric_lines.append(f"🔗 Relations: {rel_count} clean relations")
            
            # Test coverage
            test_files = sum(1 for f in files if 'test' in f.lower())
            if test_files > 0:
                coverage_pct = int(test_files / len(files) * 100) if files else 0
                metric_lines.append(f"🧪 Test coverage: {test_files}/{len(files)} files ({coverage_pct}%)")
            
            metric_lines.append(f"⭐ Framework score: {metrics['value_score']}/100")
            sections.append('\n'.join(metric_lines))
        
        # RELATIONS section - show concrete dependency paths
        if relations.get('relations'):
            rel_lines = ["DEPENDENCY FLOW:"]
            chain = relations.get('chain', '')
            if chain:
                rel_lines.append(f"  Chain: {chain}")

            # Show concrete edges (not just counts)
            rel_lines.append("  Relations:")
            for r in relations.get('relations', [])[:8]:
                rel_lines.append(f"  - {r.get('from')}.py → {r.get('to')}.py")

            # Add ASCII visualization if available
            if relations.get('ascii') and len(relations['relations']) > 1:
                rel_lines.append("")
                for line in relations['ascii'].split('\n'):
                    rel_lines.append(f"  {line}")
            sections.append('\n'.join(rel_lines))
        
        # FILES section (summary counts)
        file_parts = []
        for category, cat_files in categorized.items():
            count = len(cat_files)
            if count > 0:
                file_parts.append(f"{category}={count}")
        
        if file_parts:
            sections.append(f"Files: {'; '.join(file_parts)}")
        
        return '\n\n'.join(sections)
    
    def validate_summary_quality(self, title: str, body: str) -> Dict[str, Any]:
        """Validate summary against quality thresholds."""
        config = self.config.get('quality', {}).get('commit_summary', {})
        
        min_value_words = config.get('min_value_words', 3)
        max_generic = config.get('max_generic_terms', 0)
        required_metrics = config.get('required_metrics', 2)
        
        errors = []
        warnings = []
        
        # Check title quality
        title_words = title.lower().split()
        generic_count = sum(1 for w in title_words if w in self.GENERIC_TERMS)
        
        if generic_count > max_generic:
            warnings.append(f"Title contains {generic_count} generic terms")
        
        if len(title_words) < min_value_words:
            warnings.append(f"Title too short ({len(title_words)} words)")
        
        # Check metrics presence
        metric_keywords = ['complexity', 'coverage', 'relations', 'score', '%']
        metric_count = sum(1 for kw in metric_keywords if kw in body.lower())
        
        if metric_count < required_metrics:
            warnings.append(f"Only {metric_count} metrics found (need {required_metrics})")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'score': max(0, 100 - len(errors) * 20 - len(warnings) * 10)
        }


def generate_business_summary(files: List[str], diff_content: str = '', 
                              config: Dict = None) -> Dict[str, Any]:
    """Convenience function to generate enhanced summary."""
    generator = EnhancedSummaryGenerator(config)
    return generator.generate_enhanced_summary(files, diff_content)


def validate_summary(summary: Dict[str, Any], files: List[str] = None,
                     config: Dict = None) -> Dict[str, Any]:
    """Validate summary against quality gates.
    
    Returns: {valid: bool, errors: [], warnings: [], score: int, fixes: []}
    """
    validator = QualityValidator(config)
    files = files or summary.get('files', [])
    return validator.validate(summary, files)


def auto_fix_summary(summary: Dict[str, Any], files: List[str] = None,
                     config: Dict = None) -> Dict[str, Any]:
    """Auto-fix summary issues and return corrected summary.
    
    Returns: Fixed summary with 'applied_fixes' list
    """
    validator = QualityValidator(config)
    files = files or summary.get('files', [])
    return validator.auto_fix(summary, files)
