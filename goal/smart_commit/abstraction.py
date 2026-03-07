"""Code abstraction - extracts meaningful abstractions from code changes."""

import fnmatch
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        """Extract meaningful topics from markdown changes, filtering out noise."""
        topics = []
        
        # Patterns to ignore (changelog noise, version numbers, dates)
        ignore_patterns = [
            r'^\[.*\d+\.\d+.*\]',  # Version numbers like [1.2.0]
            r'^\d{4}-\d{2}-\d{2}',  # Dates
            r'^(Added|Changed|Deprecated|Removed|Fixed|Security)$',  # Changelog sections
            r'^(Changelog|CHANGELOG|Change\s*Log)',  # Changelog headers
            r'^(Unreleased|\[Unreleased\])',  # Unreleased section
            r'^v?\d+\.\d+',  # Version numbers
            r'^Table of Contents',  # TOC
            r'^#+$',  # Empty headers
        ]
        
        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                line = line[1:].strip()
                # Extract headers
                if line.startswith('#'):
                    topic = re.sub(r'^#+\s*', '', line).strip()
                    if topic and len(topic) > 2:
                        # Skip noise patterns
                        if not any(re.match(p, topic, re.IGNORECASE) for p in ignore_patterns):
                            topics.append(topic)
        
        return topics[:5]
    
    def infer_benefit(self, entities: List[str], domain: str, commit_type: str, 
                       files: List[str] = None, features: List[str] = None) -> str:
        """Infer business benefit from entities, files, and detected features."""
        # If we have detected features, use them directly
        if features:
            if len(features) == 1:
                return f"{features[0]} support"
            elif len(features) <= 3:
                return ', '.join(features[:-1]) + f" and {features[-1]} support"
            else:
                return f"{features[0]}, {features[1]} and {len(features) - 2} more features"
        
        # Check for specific patterns in entities
        entity_str = ' '.join(entities).lower()
        
        # Pattern matching for common functionality
        benefit_patterns = [
            (r'kubernetes|k8s|deployment|pod|service', 'Kubernetes support'),
            (r'terraform|tf|provider|resource', 'Terraform support'),
            (r'docker|container|compose', 'Docker support'),
            (r'ansible|playbook|task', 'Ansible support'),
            (r'gitlab|github|ci|cd|pipeline', 'CI/CD support'),
            (r'analyzer|parser|detect', 'analysis capabilities'),
            (r'config|settings|yaml|json', 'configuration management'),
            (r'cli|command|option|arg', 'CLI experience'),
            (r'api|endpoint|route|handler', 'API functionality'),
            (r'test|spec|assert', 'test coverage'),
            (r'doc|readme|guide|tutorial|example', 'documentation'),
            (r'auth|login|token|session', 'security'),
            (r'cache|perf|optim|speed', 'performance'),
            (r'refactor|clean|extract|split', 'code architecture'),
            (r'fix|bug|issue|error', 'bug fixes'),
        ]
        
        for pattern, benefit in benefit_patterns:
            if re.search(pattern, entity_str):
                return benefit
        
        # Check file paths for technology hints
        if files:
            file_str = ' '.join(files).lower()
            for pattern, benefit in benefit_patterns:
                if re.search(pattern, file_str):
                    return benefit
        
        # Fallback to domain-based benefit
        domain_benefits = self.benefit_keywords
        if domain in domain_benefits:
            return domain_benefits[domain]
        
        # Fallback to commit type benefit
        if commit_type in domain_benefits:
            return domain_benefits[commit_type]
        
        return 'improved functionality'
    
    def detect_features(self, files: List[str], entities: List[str]) -> List[str]:
        """Detect high-level features from files and entities."""
        features = []
        file_str = ' '.join(files).lower()
        entity_str = ' '.join(entities).lower()
        combined = file_str + ' ' + entity_str
        
        # Technology/feature detection patterns
        feature_patterns = [
            (r'kubernetes|k8s|deployment\.ya?ml|pod|service\.ya?ml', 'Kubernetes'),
            (r'terraform|\.tf$|provider|resource\s', 'Terraform'),
            (r'docker.compose|compose\.ya?ml', 'Docker Compose'),
            (r'dockerfile', 'Docker'),
            (r'ansible|playbook\.ya?ml', 'Ansible'),
            (r'gitlab.ci|\.gitlab-ci', 'GitLab CI'),
            (r'github.actions|\.github/workflows', 'GitHub Actions'),
            (r'jenkins|jenkinsfile', 'Jenkins'),
            (r'helm|chart\.ya?ml|values\.ya?ml', 'Helm'),
            (r'nginx|nginx\.conf', 'Nginx'),
            (r'apache|httpd\.conf', 'Apache'),
            (r'systemd|\.service$', 'systemd'),
            (r'makefile', 'Make'),
        ]
        
        for pattern, feature in feature_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                if feature not in features:
                    features.append(feature)
        
        # Detect analyzer additions
        analyzer_match = re.findall(r'analyzers?[/\\](\w+)', file_str)
        for analyzer in analyzer_match:
            name = analyzer.replace('_', ' ').title()
            if name not in features and name.lower() not in ['init', 'base', 'generic']:
                features.append(f"{name} analyzer")
        
        return features[:5]  # Limit to 5 features
    
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
