"""Quality validator - extracted from enhanced_summary.py."""

import re
from typing import Dict, List, Any

try:
    from .quality_filter import SummaryQualityFilter
except ImportError:
    from goal.summary.quality_filter import SummaryQualityFilter


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
            metric_keywords = ['changes:', 'testing:', 'stats:', 'net', 'complexity', 'dependencies:']
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
        
        # 1c. Expand short title if description has fewer words than min_value_words
        title = fixed.get('title', '')
        desc = title.split(':', 1)[1].strip() if ':' in title else title
        desc_word_count = len(re.findall(r"[a-zA-Z]+", desc.lower()))
        if desc_word_count < self.min_value_words:
            arch_title = self.filter.generate_architecture_title(files, categories)
            if arch_title:
                m2 = re.match(r'^(\w+)\(([^)]*)\):', title)
                if m2:
                    fixed['title'] = f"{m2.group(1)}({m2.group(2)}): {arch_title}"
                else:
                    # No conventional commit prefix — add one
                    entities = summary.get('analysis', {}).get('aggregated', {}).get('added_entities', [])
                    intent = self.filter.classify_intent_smart(files, entities, added, deleted)
                    dominant_cat = max(categories.items(), key=lambda x: len(x[1]))[0] if categories else 'core'
                    fixed['title'] = f"{intent}({dominant_cat}): {arch_title}"
                applied_fixes.append(f"Fixed title: \"{desc}\" → \"{arch_title}\"")

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


__all__ = ['QualityValidator']
