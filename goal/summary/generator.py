"""Enhanced summary generator - extracted from enhanced_summary.py."""

import re
from typing import Dict, List, Any
from collections import defaultdict
from pathlib import Path

try:
    from ..deep_analyzer import CodeChangeAnalyzer
    from .quality_filter import SummaryQualityFilter
except ImportError:
    from goal.deep_analyzer import CodeChangeAnalyzer
    from goal.summary.quality_filter import SummaryQualityFilter


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
            aggregated=aggregated,
            file_analyses=analysis.get('file_analyses', [])
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
                               aggregated: Dict,
                               file_analyses: List[Dict] = None) -> str:
        """Format the enhanced commit body.
        
        Produces a YAML structure optimised for git log / GitHub readers:
        - changes:      per-file concrete additions/modifications/removals
        - testing:      new test scenarios (only when tests are present)
        - dependencies: import flow between changed files (only when present)
        - stats:        concise line/complexity metrics
        """
        file_analyses = file_analyses or []
        sections = []

        # ── CHANGES section: per-file breakdown of what was touched ──
        categorized = self.quality_filter.categorize_files(files)
        # Build filepath→analysis lookup
        analysis_map = {}
        for fa in file_analyses:
            fp = fa.get('filepath', '')
            analysis_map[fp] = fa
            # Also index by basename for fuzzy matching
            analysis_map[Path(fp).name] = fa

        change_lines = ["changes:"]
        has_changes = False
        test_scenarios = []

        for f in files:
            fname = Path(f).name
            fa = analysis_map.get(f) or analysis_map.get(fname) or {}

            added_ents = fa.get('added_entities', [])
            modified_ents = fa.get('modified_entities', [])
            removed_ents = fa.get('removed_entities', [])

            if not added_ents and not modified_ents and not removed_ents:
                continue

            has_changes = True
            # Determine area from categorization
            area = 'core'
            for cat, cat_files in categorized.items():
                if f in cat_files:
                    area = cat
                    break

            change_lines.append(f"  - file: {fname}")
            change_lines.append(f"    area: {area}")

            if added_ents:
                names = [e['name'] for e in added_ents]
                # Collect test names for the testing section
                tests = [n for n in names if n.startswith('test_')]
                non_tests = [n for n in names if not n.startswith('test_')]
                test_scenarios.extend(tests)

                if non_tests:
                    shown = non_tests[:6]
                    suffix = f", +{len(non_tests) - 6} more" if len(non_tests) > 6 else ""
                    change_lines.append(f"    added: [{', '.join(shown)}{suffix}]")
                if tests:
                    change_lines.append(f"    new_tests: {len(tests)}")

            if modified_ents:
                names = [e['name'] for e in modified_ents[:6]]
                suffix = f", +{len(modified_ents) - 6} more" if len(modified_ents) > 6 else ""
                change_lines.append(f"    modified: [{', '.join(names)}{suffix}]")

            if removed_ents:
                names = [e['name'] for e in removed_ents[:6]]
                suffix = f", +{len(removed_ents) - 6} more" if len(removed_ents) > 6 else ""
                change_lines.append(f"    removed: [{', '.join(names)}{suffix}]")

        if has_changes:
            sections.append('\n'.join(change_lines))

        # ── TESTING section: concrete test scenarios added ──
        if test_scenarios:
            test_lines = ["testing:"]
            test_lines.append(f"  new_tests: {len(test_scenarios)}")
            test_lines.append("  scenarios:")
            for t in test_scenarios[:10]:
                # Strip test_ prefix for readability
                readable = t[5:] if t.startswith('test_') else t
                test_lines.append(f"    - {readable}")
            if len(test_scenarios) > 10:
                test_lines.append(f"    # +{len(test_scenarios) - 10} more")
            sections.append('\n'.join(test_lines))

        # ── DEPENDENCIES section: import flow (only when non-trivial) ──
        if relations.get('relations'):
            dep_lines = ["dependencies:"]
            chain = relations.get('chain', '')
            if chain:
                dep_lines.append(f"  flow: \"{chain}\"")
            for r in relations.get('relations', [])[:8]:
                dep_lines.append(f"  - {r.get('from')}.py -> {r.get('to')}.py")
            sections.append('\n'.join(dep_lines))

        # ── STATS section: concise metrics ──
        if metrics:
            stat_lines = ["stats:"]
            added = metrics.get('lines_added', 0)
            deleted = metrics.get('lines_deleted', 0)
            if added or deleted:
                net = added - deleted
                sign = '+' if net >= 0 else ''
                stat_lines.append(f"  lines: \"+{added}/-{deleted} (net {sign}{net})\"")
            stat_lines.append(f"  files: {len(files)}")

            # Complexity change (human-readable interpretation)
            old_cc = metrics.get('old_complexity', 1)
            new_cc = metrics.get('new_complexity', old_cc)
            if old_cc and old_cc > 0:
                emoji, desc = self.quality_filter.format_complexity_delta(old_cc, new_cc)
                stat_lines.append(f"  complexity: \"{desc}\"")

            sections.append('\n'.join(stat_lines))

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


__all__ = ['EnhancedSummaryGenerator']
