"""Deep code analysis for functional commit messages.

Uses AST analysis to understand code changes and infer business value.
No external dependencies required - uses Python's built-in ast module.
"""

import ast
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict


class CodeChangeAnalyzer:
    """Analyzes code changes to extract functional meaning."""
    
    # Patterns that indicate specific functionality
    VALUE_PATTERNS = {
        'configuration': {
            'signatures': ['config', 'yaml', 'toml', 'settings', 'options', 'parse_config'],
            'keywords': ['load_config', 'get_config', 'save_config', 'merge'],
            'impact': 'improved configuration management'
        },
        'cli': {
            'signatures': ['click.', '@click', 'argparse', 'command', 'option'],
            'keywords': ['add_command', 'cli', 'parse_args'],
            'impact': 'enhanced CLI interface'
        },
        'api': {
            'signatures': ['endpoint', 'route', 'request', 'response', 'api'],
            'keywords': ['get', 'post', 'put', 'delete', 'handler'],
            'impact': 'new API capabilities'
        },
        'database': {
            'signatures': ['db', 'sql', 'query', 'model', 'migrate'],
            'keywords': ['insert', 'update', 'delete', 'select', 'connection'],
            'impact': 'database improvements'
        },
        'auth': {
            'signatures': ['auth', 'login', 'token', 'permission', 'session'],
            'keywords': ['authenticate', 'authorize', 'verify', 'jwt'],
            'impact': 'security enhancements'
        },
        'testing': {
            'signatures': ['test_', 'assert', 'mock', 'fixture', 'pytest'],
            'keywords': ['test', 'spec', 'coverage'],
            'impact': 'improved test coverage'
        },
        'logging': {
            'signatures': ['log', 'logger', 'logging', 'debug', 'info'],
            'keywords': ['error', 'warning', 'trace'],
            'impact': 'better observability'
        },
        'performance': {
            'signatures': ['cache', 'async', 'parallel', 'optimize'],
            'keywords': ['speed', 'fast', 'efficient', 'memory'],
            'impact': 'performance improvements'
        },
        'formatting': {
            'signatures': ['format', 'render', 'template', 'markdown', 'html'],
            'keywords': ['output', 'display', 'style'],
            'impact': 'improved output formatting'
        },
        'validation': {
            'signatures': ['valid', 'check', 'verify', 'ensure', 'sanitize'],
            'keywords': ['schema', 'constraint', 'rule'],
            'impact': 'better input validation'
        }
    }
    
    # Relation patterns between modules
    RELATION_PATTERNS = {
        ('config', 'cli'): 'configuration-driven CLI',
        ('config', 'core'): 'configurable core logic',
        ('test', 'core'): 'better test coverage',
        ('docs', 'core'): 'improved documentation',
        ('api', 'db'): 'data-driven API',
        ('auth', 'api'): 'secure API endpoints',
    }
    
    def __init__(self):
        self.cache = {}
    
    def analyze_file_diff(self, filepath: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze changes between two versions of a file."""
        result = {
            'filepath': filepath,
            'language': self._detect_language(filepath),
            'added_entities': [],
            'modified_entities': [],
            'removed_entities': [],
            'functional_areas': [],
            'complexity_change': 0,
            'value_indicators': []
        }
        
        if result['language'] == 'python':
            result.update(self._analyze_python_diff(old_content, new_content))
        elif result['language'] in ('javascript', 'typescript'):
            result.update(self._analyze_js_diff(old_content, new_content))
        else:
            result.update(self._analyze_generic_diff(old_content, new_content))
        
        # Detect functional areas from entities and content
        result['functional_areas'] = self._detect_functional_areas(
            result['added_entities'] + result['modified_entities'],
            new_content
        )
        
        return result
    
    def _detect_language(self, filepath: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(filepath).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.java': 'java',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.toml': 'toml',
        }
        return lang_map.get(ext, 'unknown')
    
    def _analyze_python_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze Python code changes using AST."""
        result = {
            'added_entities': [],
            'modified_entities': [],
            'removed_entities': [],
            'complexity_change': 0,
            'value_indicators': []
        }
        
        try:
            old_tree = ast.parse(old_content) if old_content.strip() else ast.Module(body=[])
            new_tree = ast.parse(new_content) if new_content.strip() else ast.Module(body=[])
        except SyntaxError:
            return result
        
        old_entities = self._extract_python_entities(old_tree)
        new_entities = self._extract_python_entities(new_tree)
        
        old_names = set(old_entities.keys())
        new_names = set(new_entities.keys())
        
        # Find added, removed, modified
        for name in new_names - old_names:
            entity = new_entities[name]
            result['added_entities'].append({
                'name': name,
                'type': entity['type'],
                'decorators': entity.get('decorators', []),
                'docstring': entity.get('docstring', ''),
                'complexity': entity.get('complexity', 1)
            })
        
        for name in old_names - new_names:
            result['removed_entities'].append({
                'name': name,
                'type': old_entities[name]['type']
            })
        
        for name in old_names & new_names:
            old_e = old_entities[name]
            new_e = new_entities[name]
            # Check if implementation changed
            if old_e.get('hash') != new_e.get('hash'):
                result['modified_entities'].append({
                    'name': name,
                    'type': new_e['type'],
                    'complexity_delta': new_e.get('complexity', 1) - old_e.get('complexity', 1)
                })
        
        # Calculate overall complexity change
        old_complexity = sum(e.get('complexity', 1) for e in old_entities.values())
        new_complexity = sum(e.get('complexity', 1) for e in new_entities.values())
        result['complexity_change'] = new_complexity - old_complexity
        
        # Detect value indicators from decorators and names
        for entity in result['added_entities']:
            if any(d in str(entity.get('decorators', [])) for d in ['click', 'command', 'option']):
                result['value_indicators'].append('cli_enhancement')
            if 'config' in entity['name'].lower():
                result['value_indicators'].append('configuration')
            if entity['name'].startswith('test_'):
                result['value_indicators'].append('testing')
        
        return result
    
    def _extract_python_entities(self, tree: ast.Module) -> Dict[str, Dict]:
        """Extract functions, classes, and their metadata from AST."""
        entities = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                entities[node.name] = {
                    'type': 'function',
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node) or '',
                    'complexity': self._calculate_complexity(node),
                    'hash': hash(ast.dump(node))
                }
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                entities[node.name] = {
                    'type': 'class',
                    'methods': methods,
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node) or '',
                    'complexity': sum(self._calculate_complexity(n) for n in node.body 
                                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
                    'hash': hash(ast.dump(node))
                }
        
        return entities
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)
    
    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function/method."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _analyze_js_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript changes using regex patterns."""
        result = {
            'added_entities': [],
            'modified_entities': [],
            'removed_entities': [],
            'complexity_change': 0,
            'value_indicators': []
        }
        
        # Extract functions and classes using regex
        func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*[=(]|(\w+)\s*:\s*(?:async\s+)?function'
        class_pattern = r'class\s+(\w+)'
        
        old_funcs = set(re.findall(func_pattern, old_content))
        new_funcs = set(re.findall(func_pattern, new_content))
        old_classes = set(re.findall(class_pattern, old_content))
        new_classes = set(re.findall(class_pattern, new_content))
        
        # Flatten tuples
        old_funcs = {f[0] or f[1] for f in old_funcs if f[0] or f[1]}
        new_funcs = {f[0] or f[1] for f in new_funcs if f[0] or f[1]}
        
        for name in new_funcs - old_funcs:
            result['added_entities'].append({'name': name, 'type': 'function'})
        for name in new_classes - old_classes:
            result['added_entities'].append({'name': name, 'type': 'class'})
        for name in old_funcs - new_funcs:
            result['removed_entities'].append({'name': name, 'type': 'function'})
        for name in old_classes - new_classes:
            result['removed_entities'].append({'name': name, 'type': 'class'})
        
        return result
    
    def _analyze_generic_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Generic diff analysis for non-code files."""
        old_lines = set(old_content.splitlines())
        new_lines = set(new_content.splitlines())
        
        added = len(new_lines - old_lines)
        removed = len(old_lines - new_lines)
        
        return {
            'added_entities': [],
            'modified_entities': [],
            'removed_entities': [],
            'complexity_change': 0,
            'value_indicators': [],
            'lines_added': added,
            'lines_removed': removed
        }
    
    def _detect_functional_areas(self, entities: List[Dict], content: str) -> List[str]:
        """Detect which functional areas are affected by changes."""
        areas = set()
        content_lower = content.lower()
        
        for area, patterns in self.VALUE_PATTERNS.items():
            # Check entity names
            for entity in entities:
                name = entity.get('name', '').lower()
                if any(sig.lower() in name for sig in patterns['signatures']):
                    areas.add(area)
                    break
            
            # Check content
            if any(kw.lower() in content_lower for kw in patterns['keywords']):
                areas.add(area)
        
        return list(areas)
    
    def aggregate_changes(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate analysis results across multiple files."""
        all_added = []
        all_modified = []
        all_removed = []
        all_areas = set()
        total_complexity_change = 0
        all_value_indicators = []
        
        for analysis in file_analyses:
            all_added.extend(analysis.get('added_entities', []))
            all_modified.extend(analysis.get('modified_entities', []))
            all_removed.extend(analysis.get('removed_entities', []))
            all_areas.update(analysis.get('functional_areas', []))
            total_complexity_change += analysis.get('complexity_change', 0)
            all_value_indicators.extend(analysis.get('value_indicators', []))
        
        # Count indicators
        indicator_counts = Counter(all_value_indicators)
        primary_indicator = indicator_counts.most_common(1)[0][0] if indicator_counts else None
        
        return {
            'added_entities': all_added,
            'modified_entities': all_modified,
            'removed_entities': all_removed,
            'functional_areas': list(all_areas),
            'complexity_change': total_complexity_change,
            'primary_indicator': primary_indicator,
            'indicator_counts': dict(indicator_counts)
        }
    
    def infer_functional_value(self, aggregated: Dict[str, Any], files: List[str]) -> str:
        """Infer the functional value/impact of the changes."""
        areas = aggregated.get('functional_areas', [])
        added = aggregated.get('added_entities', [])
        modified = aggregated.get('modified_entities', [])
        complexity = aggregated.get('complexity_change', 0)
        primary_indicator = aggregated.get('primary_indicator')
        
        # Check for specific patterns in files
        file_patterns = {
            'analyzer': any('analyzer' in f.lower() for f in files),
            'deep': any('deep' in f.lower() for f in files),
            'smart': any('smart' in f.lower() for f in files),
            'config': any('config' in f.lower() for f in files),
            'cli': any('cli' in f.lower() for f in files),
        }
        
        # Priority-based value inference
        if file_patterns['analyzer'] or file_patterns['deep']:
            if len(added) > 0:
                return "enhanced code analysis capabilities"
            return "improved code analysis"
        
        if 'cli' in areas and added:
            cli_entities = [e for e in added if any(d in str(e.get('decorators', [])) 
                                                    for d in ['click', 'command'])]
            if cli_entities:
                return f"new CLI commands: {', '.join(e['name'] for e in cli_entities[:3])}"
        
        if 'configuration' in areas:
            config_entities = [e for e in added if 'config' in e.get('name', '').lower()]
            if config_entities:
                return "improved configuration management"
        
        if 'api' in areas:
            return "new API capabilities"
        
        if 'auth' in areas:
            return "security enhancements"
        
        if 'testing' in areas:
            test_count = len([e for e in added if e.get('name', '').startswith('test_')])
            if test_count > 0:
                return f"added {test_count} tests for better coverage"
            return "improved test coverage"
        
        if 'formatting' in areas:
            return "improved output formatting"
        
        # Check for refactor patterns
        if complexity < -5:
            return "simplified code structure"
        if complexity > 10:
            return "new functionality"
        
        # Check for architecture improvements
        if len(added) >= 2 and any('analyzer' in e.get('name', '').lower() for e in added):
            return "enhanced architecture with deep analysis"
        
        # Fallback based on added entities
        if len(added) >= 3:
            names = [e['name'] for e in added[:3]]
            return f"added {', '.join(names)}"
        
        if len(modified) >= 2:
            names = [e['name'] for e in modified[:2]]
            return f"enhanced {', '.join(names)}"
        
        if added:
            return f"added {added[0]['name']}"
        
        if modified:
            return f"updated {modified[0]['name']}"
        
        # Generic fallback
        return "code improvements"
    
    def detect_relations(self, file_analyses: List[Dict[str, Any]]) -> List[Tuple[str, str, str]]:
        """Detect relations between changed modules."""
        relations = []
        
        # Group by domain
        domains = defaultdict(list)
        for analysis in file_analyses:
            filepath = analysis.get('filepath', '')
            for area in analysis.get('functional_areas', []):
                domains[area].append(filepath)
        
        # Check for known relation patterns
        domain_set = set(domains.keys())
        for (d1, d2), relation in self.RELATION_PATTERNS.items():
            if d1 in domain_set and d2 in domain_set:
                relations.append((d1, d2, relation))
        
        return relations
    
    def generate_functional_summary(self, files: List[str]) -> Dict[str, Any]:
        """Generate a complete functional summary of changes."""
        file_analyses = []
        
        for filepath in files:
            try:
                # Get old content from git
                old_result = subprocess.run(
                    ['git', 'show', f'HEAD:{filepath}'],
                    capture_output=True, text=True
                )
                old_content = old_result.stdout if old_result.returncode == 0 else ''
                
                # Get new content
                try:
                    with open(filepath, 'r') as f:
                        new_content = f.read()
                except FileNotFoundError:
                    new_content = ''
                
                analysis = self.analyze_file_diff(filepath, old_content, new_content)
                file_analyses.append(analysis)
            except Exception:
                continue
        
        aggregated = self.aggregate_changes(file_analyses)
        value = self.infer_functional_value(aggregated, files)
        relations = self.detect_relations(file_analyses)
        
        return {
            'file_analyses': file_analyses,
            'aggregated': aggregated,
            'functional_value': value,
            'relations': relations,
            'summary': self._build_summary(aggregated, value, relations)
        }
    
    def _build_summary(self, aggregated: Dict, value: str, relations: List) -> str:
        """Build human-readable summary."""
        parts = []
        
        added = aggregated.get('added_entities', [])
        modified = aggregated.get('modified_entities', [])
        areas = aggregated.get('functional_areas', [])
        complexity = aggregated.get('complexity_change', 0)
        
        if added:
            funcs = [e['name'] for e in added if e.get('type') == 'function'][:4]
            classes = [e['name'] for e in added if e.get('type') == 'class'][:2]
            if classes:
                parts.append(f"New classes: {', '.join(classes)}")
            if funcs:
                parts.append(f"New functions: {', '.join(funcs)}")
        
        if modified:
            names = [e['name'] for e in modified[:3]]
            parts.append(f"Modified: {', '.join(names)}")
        
        if relations:
            rel_strs = [f"{r[0]}→{r[1]}: {r[2]}" for r in relations]
            parts.append(f"Relations: {'; '.join(rel_strs)}")
        
        if complexity != 0:
            sign = '+' if complexity > 0 else ''
            parts.append(f"Complexity: {sign}{complexity}")
        
        if areas:
            parts.append(f"Areas: {', '.join(areas)}")
        
        return '\n'.join(parts) if parts else value
