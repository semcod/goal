"""Goal YAML configuration management."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import yaml


# Default configuration template
DEFAULT_CONFIG = {
    'version': '1.0',
    'project': {
        'name': '',
        'type': [],
        'description': '',
    },
    'versioning': {
        'strategy': 'semver',
        'files': [
            'VERSION',
            'pyproject.toml:version',
        ],
        'bump_rules': {
            'patch': 10,
            'minor': 50,
            'major': 200,
        },
    },
    'git': {
        'commit': {
            'strategy': 'conventional',
            'scope': '',
            'abstraction_level': 'auto',  # auto, high, medium, low
            'abstraction_levels': {
                'high': '{type}({domain}): {benefit}',
                'medium': '{type}({domain}): {action} {entities}',
                'low': '{type}({domain}): update {file_count} files (+{added}/-{deleted})',
            },
            'domain_mapping': {
                'goal/*.py': 'core',
                'src/*.py': 'core',
                'lib/*.py': 'core',
                'app/*.py': 'app',
                'api/*.py': 'api',
                'docs/*': 'docs',
                'tests/*': 'test',
                'test/*': 'test',
                '*.md': 'docs',
                '*.rst': 'docs',
                'pyproject.toml': 'build',
                'setup.py': 'build',
                'setup.cfg': 'build',
                'package.json': 'build',
                'Cargo.toml': 'build',
                'goal.yaml': 'config',
                '.github/*': 'ci',
                '.gitlab-ci.yml': 'ci',
                'Dockerfile': 'docker',
                'docker-compose.yml': 'docker',
            },
            'benefit_keywords': {
                'config': 'better configuration management',
                'cli': 'improved CLI experience',
                'api': 'enhanced API functionality',
                'test': 'improved test coverage',
                'docs': 'better documentation',
                'auth': 'enhanced security',
                'perf': 'improved performance',
                'refactor': 'cleaner code architecture',
                'fix': 'resolved issues',
                'feat': 'new functionality',
            },
            'templates': {
                'feat': {
                    'high': 'feat({domain}): {benefit}',
                    'medium': 'feat({domain}): add {entities}',
                    'low': 'feat({domain}): add {file_count} files (+{added}/-{deleted})',
                },
                'fix': {
                    'high': 'fix({domain}): {benefit}',
                    'medium': 'fix({domain}): resolve {entities}',
                    'low': 'fix({domain}): update {file_count} files (+{added}/-{deleted})',
                },
                'docs': {
                    'high': 'docs({domain}): {benefit}',
                    'medium': 'docs({domain}): document {entities}',
                    'low': 'docs({domain}): update {file_count} files',
                },
                'refactor': {
                    'high': 'refactor({domain}): {benefit}',
                    'medium': 'refactor({domain}): restructure {entities}',
                    'low': 'refactor({domain}): update {file_count} files',
                },
                'test': {
                    'high': 'test({domain}): {benefit}',
                    'medium': 'test({domain}): add tests for {entities}',
                    'low': 'test({domain}): update {file_count} files',
                },
                'build': {
                    'high': 'build({domain}): {benefit}',
                    'medium': 'build({domain}): configure {entities}',
                    'low': 'build({domain}): update {file_count} files',
                },
                'chore': {
                    'high': 'chore({domain}): {benefit}',
                    'medium': 'chore({domain}): update {entities}',
                    'low': 'chore({domain}): update {file_count} files',
                },
                'style': {
                    'high': 'style({domain}): {benefit}',
                    'medium': 'style({domain}): format {entities}',
                    'low': 'style({domain}): update {file_count} files',
                },
                'perf': {
                    'high': 'perf({domain}): {benefit}',
                    'medium': 'perf({domain}): optimize {entities}',
                    'low': 'perf({domain}): update {file_count} files',
                },
            },
            'classify_by': [
                'file_extensions',
                'directory_paths',
                'line_stats',
                'keywords_diff',
                'code_entities',
            ],
            'value_patterns': {
                'configuration': {
                    'signatures': ['config', 'yaml', 'toml', 'settings', 'options'],
                    'impact': 'better configuration management',
                    'changelog_section': 'core',
                },
                'cli': {
                    'signatures': ['click.', '@click', 'command', 'option', 'argparse'],
                    'impact': 'improved CLI experience',
                    'changelog_section': 'core',
                },
                'api': {
                    'signatures': ['endpoint', 'route', 'request', 'response', 'handler'],
                    'impact': 'enhanced API functionality',
                    'changelog_section': 'core',
                },
                'testing': {
                    'signatures': ['test_', 'assert', 'mock', 'fixture', 'pytest'],
                    'impact': 'improved test coverage',
                    'changelog_section': 'test',
                },
                'documentation': {
                    'paths': ['docs/*', '*.md', 'README*'],
                    'impact': 'comprehensive documentation',
                    'changelog_section': 'docs',
                },
                'performance': {
                    'signatures': ['cache', 'async', 'parallel', 'optimize', 'speed'],
                    'impact': 'performance improvements',
                    'changelog_section': 'core',
                },
                'security': {
                    'signatures': ['auth', 'token', 'permission', 'encrypt', 'secure'],
                    'impact': 'security enhancements',
                    'changelog_section': 'core',
                },
                'formatting': {
                    'signatures': ['format', 'render', 'template', 'markdown', 'output'],
                    'impact': 'improved output formatting',
                    'changelog_section': 'core',
                },
            },
            'relations': {
                'config → cli': 'configuration-driven CLI',
                'config → core': 'configurable core logic',
                'test → core': 'better test coverage',
                'docs → core': 'improved documentation',
            },
        },
        'changelog': {
            'enabled': True,
            'template': 'keep-a-changelog',
            'output': 'CHANGELOG.md',
            'sections': ['Added', 'Changed', 'Fixed', 'Deprecated', 'Removed', 'Security'],
            'group_by_domain': True,
            'domain_sections': {
                'core': ['feat', 'fix', 'refactor', 'perf'],
                'docs': ['docs'],
                'test': ['test'],
                'build': ['build', 'chore'],
                'ci': ['ci'],
            },
            'include_entities': True,
            'max_entities_per_entry': 5,
        },
        'tag': {
            'enabled': True,
            'prefix': 'v',
            'format': '{prefix}{version}',
        },
    },
    'strategies': {
        'python': {
            'test': 'pytest tests/ -v',
            'build': 'python -m build',
            'publish': 'twine upload dist/goal-{version}*',
            'dependencies': {
                'file': 'requirements.txt',
                'lock': 'pip freeze > requirements.txt',
            },
        },
        'nodejs': {
            'test': 'npm test',
            'build': 'npm run build',
            'publish': 'npm publish',
            'dependencies': {
                'file': 'package-lock.json',
                'lock': 'npm install',
            },
        },
        'rust': {
            'test': 'cargo test',
            'build': 'cargo build --release',
            'publish': 'cargo publish',
            'dependencies': {
                'file': 'Cargo.lock',
                'lock': 'cargo update',
            },
        },
    },
    'registries': {
        'pypi': {
            'url': 'https://pypi.org/simple/',
            'token_env': 'PYPI_TOKEN',
        },
        'npm': {
            'url': 'https://registry.npmjs.org/',
            'token_env': 'NPM_TOKEN',
        },
    },
    'hooks': {
        'pre_commit': '',
        'post_commit': '',
        'pre_push': '',
        'post_push': '',
    },
    'advanced': {
        'auto_update_config': True,
        'performance': {
            'max_files': 50,
            'timeout_test': 300,
        },
    },
    'quality': {
        'commit_summary': {
            'min_value_words': 3,
            'max_generic_terms': 0,
            'required_metrics': 2,
            'relation_threshold': 0.7,
            'generic_terms': ['update', 'improve', 'enhance', 'fix', 'change', 
                            'modify', 'cleaner', 'better', 'refactor', 'misc'],
        },
        'enhanced_summary': {
            'enabled': True,
            'min_capabilities': 1,
            'min_value_score': 50,
            'include_metrics': True,
            'include_relations': True,
            'include_roles': True,
        },
        'gates': {
            'max_complexity_percent': 200,
            'max_duplicate_relations': 0,
            'min_unique_files_ratio': 0.8,
            'min_capabilities': 1,
            'max_banned_words': 0,
        },
        'role_patterns': {
            r'_analyze_(python|js|generic)_diff': 'language-specific code analyzer',
            r'CodeChangeAnalyzer': 'AST-based change detector',
            r'analyze_file_diff': 'diff analysis engine',
            r'generate_functional_summary': 'business value summarizer',
            r'generate.*message': 'commit message generator',
            r'EnhancedSummaryGenerator': 'enterprise changelog generator',
            r'GoalConfig': 'configuration manager',
            r'@click\\.command': 'CLI command',
            r'@click\\.option': 'CLI option',
            r'format_.*result': 'output formatter',
            r'_calculate_complexity': 'complexity analyzer',
        },
        'value_patterns': {
            'ast_analysis': {
                'signatures': ['ast.parse', 'ast.walk', 'libcst', 'tree-sitter', 'AST'],
                'capability': 'deep code analysis engine',
                'impact': 'intelligent change detection',
            },
            'dependency_graph': {
                'signatures': ['networkx', 'relations', 'dependencies', 'graph'],
                'capability': 'code relationship mapping',
                'impact': 'architecture understanding',
            },
            'quality_metrics': {
                'signatures': ['radon', 'cyclomatic', 'complexity', 'coverage'],
                'capability': 'code quality metrics',
                'impact': 'maintainability tracking',
            },
            'multi_language': {
                'signatures': ['_analyze_python', '_analyze_js', 'language', 'parser'],
                'capability': 'multi-language support',
                'impact': 'universal code analysis',
            },
        },
        'commit_message': {
            'min_length': 15,
            'max_length': 72,
            'max_entities': 5,
            'require_type': True,
            'require_scope': True,
        },
        'changelog': {
            'min_entries_per_release': 1,
            'max_file_lines': 10,
            'include_commit_hash': True,
        },
    },
    'code_parsers': {
        'python': {
            'extract': ['def ', 'class ', 'async def ', '@click.', '@app.', '@router.'],
            'ignore': ['import ', 'from ', '#', '"""', "'''"],
            'entity_pattern': r'(?:def|class|async def)\s+(\w+)',
        },
        'javascript': {
            'extract': ['function ', 'const ', 'class ', 'export ', 'async '],
            'ignore': ['import ', '//', '/*', '*/'],
            'entity_pattern': r'(?:function|class|const)\s+(\w+)',
        },
        'typescript': {
            'extract': ['function ', 'const ', 'class ', 'interface ', 'type ', 'export '],
            'ignore': ['import ', '//', '/*', '*/'],
            'entity_pattern': r'(?:function|class|const|interface|type)\s+(\w+)',
        },
        'rust': {
            'extract': ['fn ', 'struct ', 'enum ', 'impl ', 'pub ', 'mod '],
            'ignore': ['//', '/*', '*/'],
            'entity_pattern': r'(?:fn|struct|enum|impl|mod)\s+(\w+)',
        },
        'go': {
            'extract': ['func ', 'type ', 'struct ', 'interface '],
            'ignore': ['//', '/*', '*/'],
            'entity_pattern': r'(?:func|type)\s+(\w+)',
        },
        'markdown': {
            'extract': ['# ', '## ', '### ', '#### ', '- **'],
            'ignore': ['<!--', '-->'],
            'entity_pattern': r'^#+\s+(.+)$',
        },
    },
}


class GoalConfig:
    """Manages goal.yaml configuration file."""
    
    CONFIG_FILENAME = 'goal.yaml'
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager.
        
        Args:
            config_path: Optional path to config file. If None, looks for goal.yaml
                        in current directory or parent directories.
        """
        self.config_path = self._find_config(config_path)
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def _find_config(self, config_path: Optional[str] = None) -> Path:
        """Find the configuration file."""
        if config_path:
            return Path(config_path)
        
        # Look in current directory first
        current = Path.cwd()
        config_file = current / self.CONFIG_FILENAME
        if config_file.exists():
            return config_file
        
        # Look in parent directories up to git root
        git_root = self._find_git_root()
        if git_root:
            config_file = git_root / self.CONFIG_FILENAME
            if config_file.exists():
                return config_file
        
        # Default to current directory
        return current / self.CONFIG_FILENAME
    
    def _find_git_root(self) -> Optional[Path]:
        """Find the git repository root."""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').exists():
                return current
            current = current.parent
        return None
    
    def exists(self) -> bool:
        """Check if config file exists."""
        return self.config_path.exists()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self._loaded:
            return self._config
        
        if not self.exists():
            self._config = self._get_default_config()
        else:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f) or {}
                # Merge with defaults to ensure all keys exist
                self._config = self._merge_configs(self._get_default_config(), loaded)
            except Exception:
                self._config = self._get_default_config()
        
        self._loaded = True
        return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with auto-detected values."""
        config = DEFAULT_CONFIG.copy()
        config = self._deep_copy(config)
        
        # Auto-detect project info
        config['project']['name'] = self._detect_project_name()
        config['project']['type'] = self._detect_project_types()
        config['project']['description'] = self._detect_description()
        
        # Set default scope based on project name
        if config['project']['name']:
            config['git']['commit']['scope'] = config['project']['name']
        
        # Auto-detect version files
        config['versioning']['files'] = self._detect_version_files()
        
        return config
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a nested dict/list structure."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        return obj
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two configurations, with override taking precedence."""
        result = self._deep_copy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = self._deep_copy(value)
        
        return result
    
    def _detect_project_name(self) -> str:
        """Detect project name from various sources."""
        # Try pyproject.toml
        if Path('pyproject.toml').exists():
            try:
                content = Path('pyproject.toml').read_text()
                match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
                if match:
                    return match.group(1)
            except Exception:
                pass
        
        # Try package.json
        if Path('package.json').exists():
            try:
                import json
                data = json.loads(Path('package.json').read_text())
                if 'name' in data:
                    return data['name']
            except Exception:
                pass
        
        # Try Cargo.toml
        if Path('Cargo.toml').exists():
            try:
                content = Path('Cargo.toml').read_text()
                match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if match:
                    return match.group(1)
            except Exception:
                pass
        
        # Fallback to directory name
        return Path.cwd().name
    
    def _detect_project_types(self) -> List[str]:
        """Detect project types from files."""
        types = []
        
        type_files = {
            'python': ['pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt'],
            'nodejs': ['package.json'],
            'rust': ['Cargo.toml'],
            'go': ['go.mod'],
            'ruby': ['Gemfile'],
            'php': ['composer.json'],
            'dotnet': ['*.csproj', '*.fsproj'],
            'java': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
        }
        
        for ptype, files in type_files.items():
            for file_pattern in files:
                if '*' in file_pattern:
                    if list(Path('.').glob(file_pattern)):
                        types.append(ptype)
                        break
                elif Path(file_pattern).exists():
                    types.append(ptype)
                    break
        
        return types
    
    def _detect_description(self) -> str:
        """Detect project description from various sources."""
        # Try pyproject.toml
        if Path('pyproject.toml').exists():
            try:
                content = Path('pyproject.toml').read_text()
                match = re.search(r'^description\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
                if match:
                    return match.group(1)
            except Exception:
                pass
        
        # Try package.json
        if Path('package.json').exists():
            try:
                import json
                data = json.loads(Path('package.json').read_text())
                if 'description' in data:
                    return data['description']
            except Exception:
                pass
        
        return ''
    
    def _detect_version_files(self) -> List[str]:
        """Detect version files in the project."""
        version_files = []
        
        if Path('VERSION').exists():
            version_files.append('VERSION')
        
        if Path('pyproject.toml').exists():
            version_files.append('pyproject.toml:version')
        
        if Path('package.json').exists():
            version_files.append('package.json:version')
        
        if Path('Cargo.toml').exists():
            version_files.append('Cargo.toml:version')
        
        if Path('setup.py').exists():
            version_files.append('setup.py:version')
        
        # Check for __init__.py with __version__
        for init_file in Path('.').rglob('__init__.py'):
            try:
                content = init_file.read_text()
                if '__version__' in content:
                    version_files.append(f'{init_file}:__version__')
                    break
            except Exception:
                pass
        
        if not version_files:
            version_files.append('VERSION')
        
        return version_files
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file."""
        if config is not None:
            self._config = config
        elif not self._loaded:
            self.load()
        
        # Add header comment
        header = f"""# goal.yaml - Goal configuration file
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Documentation: https://github.com/wronai/goal#configuration
#
# This file configures Goal's behavior for:
# - Version management (semver/calver)
# - Commit message generation
# - Changelog updates
# - Build/test/publish strategies
# - Registry authentication
#
# Edit this file to customize Goal's behavior for your project.

"""
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(header)
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.
        
        Example: config.get('git.commit.strategy')
        """
        if not self._loaded:
            self.load()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dot-notation key.
        
        Example: config.set('git.commit.strategy', 'semantic')
        """
        if not self._loaded:
            self.load()
        
        keys = key.split('.')
        target = self._config
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
    
    def update_from_detection(self) -> bool:
        """Update config based on current project state.
        
        Returns True if changes were made.
        """
        if not self._loaded:
            self.load()
        
        changed = False
        
        # Update project types
        detected_types = self._detect_project_types()
        if set(detected_types) != set(self._config.get('project', {}).get('type', [])):
            self._config['project']['type'] = detected_types
            changed = True
        
        # Update version files
        detected_files = self._detect_version_files()
        current_files = self._config.get('versioning', {}).get('files', [])
        if set(detected_files) != set(current_files):
            self._config['versioning']['files'] = detected_files
            changed = True
        
        return changed
    
    def validate(self) -> List[str]:
        """Validate the configuration.
        
        Returns a list of validation errors (empty if valid).
        """
        if not self._loaded:
            self.load()
        
        errors = []
        
        # Check required fields
        if not self.get('project.name'):
            errors.append("project.name is required")
        
        # Check versioning strategy
        strategy = self.get('versioning.strategy')
        if strategy not in ['semver', 'calver', 'date']:
            errors.append(f"Invalid versioning.strategy: {strategy}")
        
        # Check commit strategy
        commit_strategy = self.get('git.commit.strategy')
        if commit_strategy not in ['conventional', 'semantic', 'custom']:
            errors.append(f"Invalid git.commit.strategy: {commit_strategy}")
        
        # Check version files exist
        for vfile in self.get('versioning.files', []):
            file_path = vfile.split(':')[0]
            if not Path(file_path).exists() and file_path != 'VERSION':
                errors.append(f"Version file not found: {file_path}")
        
        return errors
    
    def get_commit_template(self, commit_type: str) -> str:
        """Get commit message template for a given type."""
        templates = self.get('git.commit.templates', {})
        return templates.get(commit_type, '{type}({scope}): {description}')
    
    def get_strategy(self, project_type: str) -> Dict[str, Any]:
        """Get build/test/publish strategy for a project type."""
        strategies = self.get('strategies', {})
        return strategies.get(project_type, {})
    
    def get_registry(self, registry_name: str) -> Dict[str, Any]:
        """Get registry configuration."""
        registries = self.get('registries', {})
        return registries.get(registry_name, {})
    
    def should_auto_update(self) -> bool:
        """Check if config should be auto-updated."""
        return self.get('advanced.auto_update_config', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        if not self._loaded:
            self.load()
        return self._deep_copy(self._config)


def init_config(force: bool = False) -> GoalConfig:
    """Initialize a new goal.yaml configuration file.
    
    Args:
        force: If True, overwrite existing config.
    
    Returns:
        GoalConfig instance with the new configuration.
    """
    config = GoalConfig()
    
    if config.exists() and not force:
        return config
    
    config.load()
    config.save()
    
    return config


def load_config(config_path: Optional[str] = None) -> GoalConfig:
    """Load configuration from file or create default.
    
    Args:
        config_path: Optional path to config file.
    
    Returns:
        GoalConfig instance with loaded configuration.
    """
    config = GoalConfig(config_path)
    config.load()
    return config


def ensure_config(auto_update: bool = True) -> GoalConfig:
    """Ensure configuration exists and is up-to-date.
    
    This is the main entry point for getting configuration in Goal commands.
    It will:
    1. Create goal.yaml if it doesn't exist
    2. Load existing configuration
    3. Optionally update it based on project detection
    
    Args:
        auto_update: If True, update config based on detection.
    
    Returns:
        GoalConfig instance.
    """
    config = GoalConfig()
    
    if not config.exists():
        config.load()
        config.save()
    else:
        config.load()
        if auto_update and config.should_auto_update():
            if config.update_from_detection():
                config.save()
    
    return config
