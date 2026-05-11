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

from goal.deep_analyzer_patterns import RELATION_PATTERNS, VALUE_PATTERNS
from goal.deep_analyzer_aggregate import CodeChangeAggregatorMixin


class CodeChangeAnalyzer(CodeChangeAggregatorMixin):
    """Analyzes code changes to extract functional meaning."""

    VALUE_PATTERNS = VALUE_PATTERNS
    RELATION_PATTERNS = RELATION_PATTERNS

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
        
        result['value_indicators'] = self._detect_value_indicators(result['added_entities'])
        
        return result
    
    @staticmethod
    def _detect_value_indicators(added_entities: List[Dict]) -> List[str]:
        """Detect value indicators from added entity decorators and names."""
        indicators: List[str] = []
        for entity in added_entities:
            if any(d in str(entity.get('decorators', [])) for d in ['click', 'command', 'option']):
                indicators.append('cli_enhancement')
            if 'config' in entity['name'].lower():
                indicators.append('configuration')
            if entity['name'].startswith('test_'):
                indicators.append('testing')
        return indicators
    
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
