"""Smart commit message generator using lightweight Python libraries."""

import re
import os
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import subprocess

# Import smart_commit for abstraction-based generation
try:
    from .smart_commit import SmartCommitGenerator, CodeAbstraction
    HAS_SMART_COMMIT = True
except ImportError:
    HAS_SMART_COMMIT = False

# Import enhanced summary for business-value focused messages
try:
    from .enhanced_summary import EnhancedSummaryGenerator
    HAS_ENHANCED_SUMMARY = True
except ImportError:
    HAS_ENHANCED_SUMMARY = False


class CommitMessageGenerator:
    """Generate conventional commit messages using diff analysis and lightweight classification."""
    
    # File type patterns for classification
    TYPE_PATTERNS = {
        'feat': [
            r'\.py$', r'\.js$', r'\.ts$', r'\.jsx$', r'\.tsx$',
            r'src/', r'lib/', r'components/', r'modules/',
            r'add', r'new', r'create', r'implement'
        ],
        'fix': [
            r'fix', r'bug', r'patch', r'repair', r'resolve',
            r'error', r'exception', r'issue', r'problem'
        ],
        'docs': [
            r'\.md$', r'\.rst$', r'\.txt$', r'readme', r'doc',
            r'comment', r'license', r'guide', r'tutorial'
        ],
        'style': [
            r'format', r'style', r'lint', r'whitespace',
            r'prettier', r'black', r'flake8', r'eslint'
        ],
        'refactor': [
            r'refactor', r'restructure', r'reorganize', r'rename',
            r'move', r'extract', r'inline', r'simplify'
        ],
        'perf': [
            r'perf', r'optimize', r'speed', r'cache',
            r'fast', r'slow', r'improve', r'boost'
        ],
        'test': [
            r'test', r'spec', r'coverage', r'pytest',
            r'\.test\.', r'_test\.py$', r'tests/'
        ],
        'build': [
            r'makefile', r'dockerfile', r'docker-compose',
            r'\.yml$', r'\.yaml$', r'\.json$', r'ci', r'cd',
            r'build', r'compile', r'webpack', r'vite'
        ],
        'chore': [
            r'deps', r'dependenc', r'update', r'bump',
            r'config', r'\.cfg$', r'\.ini$', r'\.toml$',
            r'version', r'requirements', r'package\.json'
        ]
    }
    
    # Scope detection patterns
    SCOPE_PATTERNS = {
        'goal': r'goal|cli|release',
        'examples': r'example|demo',
        'docs': r'doc|readme|md',
        'tests': r'test|spec',
        'build': r'makefile|docker|ci|cd',
        'config': r'config|setup|pyproject',
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.cache = {}
        self.config = config
        self._smart_generator = None
        self._enhanced_generator = None
        
        # Initialize smart generator if config provided
        if config and HAS_SMART_COMMIT:
            self._smart_generator = SmartCommitGenerator(config)
        
        # Initialize enhanced summary generator
        if HAS_ENHANCED_SUMMARY:
            self._enhanced_generator = EnhancedSummaryGenerator(config or {})
    
    def get_diff_stats(self, cached: bool = True) -> Dict[str, int]:
        """Get diff statistics using git command."""
        cache_key = f"diff_stats_{cached}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if cached:
                result = subprocess.run(
                    ['git', 'diff', '--cached', '--numstat'],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ['git', 'diff', '--numstat'],
                    capture_output=True,
                    text=True
                )
            
            stats = {'files': 0, 'added': 0, 'deleted': 0}
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        deleted = int(parts[1]) if parts[1] != '-' else 0
                        stats['files'] += 1
                        stats['added'] += added
                        stats['deleted'] += deleted
            
            self.cache[cache_key] = stats
            return stats
            
        except Exception:
            return {'files': 0, 'added': 0, 'deleted': 0}

    def get_name_status(self, cached: bool = True, paths: Optional[List[str]] = None) -> List[Tuple[str, str]]:
        """Return list of (status, path) from git diff --name-status."""
        paths_key = ','.join(paths) if paths else '*'
        cache_key = f"name_status_{cached}_{paths_key}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')
        cmd.append('--name-status')
        if paths:
            cmd.append('--')
            cmd.extend(paths)

        items: List[Tuple[str, str]] = []
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0].strip()
                    path = parts[-1].strip()
                    items.append((status, path))
        except Exception:
            items = []

        self.cache[cache_key] = items
        return items

    def get_numstat_map(self, cached: bool = True, paths: Optional[List[str]] = None) -> Dict[str, Tuple[int, int]]:
        """Return map path -> (added, deleted) from git diff --numstat."""
        paths_key = ','.join(paths) if paths else '*'
        cache_key = f"numstat_map_{cached}_{paths_key}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')
        cmd.append('--numstat')
        if paths:
            cmd.append('--')
            cmd.extend(paths)

        out: Dict[str, Tuple[int, int]] = {}
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    a = int(parts[0]) if parts[0] != '-' else 0
                    d = int(parts[1]) if parts[1] != '-' else 0
                    f = parts[2]
                    out[f] = (a, d)
        except Exception:
            out = {}

        self.cache[cache_key] = out
        return out
    
    def get_changed_files(self, cached: bool = True, paths: Optional[List[str]] = None) -> List[str]:
        """Get list of changed files. If paths provided, limit diff to those paths."""
        paths_key = ','.join(paths) if paths else '*'
        cache_key = f"changed_files_{cached}_{paths_key}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            cmd = ['git', 'diff']
            if cached:
                cmd.append('--cached')
            cmd.append('--name-only')
            if paths:
                cmd.append('--')
                cmd.extend(paths)
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            self.cache[cache_key] = files
            return files
            
        except Exception:
            return []
    
    def get_diff_content(self, cached: bool = True, paths: Optional[List[str]] = None) -> str:
        """Get diff content for analysis. If paths provided, limit diff to those paths."""
        paths_key = ','.join(paths) if paths else '*'
        cache_key = f"diff_content_{cached}_{paths_key}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            cmd = ['git', 'diff']
            if cached:
                cmd.append('--cached')
            cmd.append('-U3')
            if paths:
                cmd.append('--')
                cmd.extend(paths)
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            self.cache[cache_key] = result.stdout
            return result.stdout
            
        except Exception:
            return ""
    
    def classify_change_type(self, files: List[str], diff_content: str, stats: Dict[str, int]) -> str:
        """Classify the type of change using pattern matching and heuristics."""
        scores = defaultdict(int)

        # Strong signal: code changes in main package should not become docs
        has_package_code = any(
            (f.startswith('goal/') or f.startswith('src/') or f.startswith('lib/'))
            and (f.endswith('.py') or f.endswith('.js') or f.endswith('.ts'))
            for f in files
        )
        has_docs_only = all(
            f.endswith(('.md', '.rst', '.txt')) or 'docs/' in f or 'readme' in f.lower()
            for f in files
        )

        has_ci_only = all(
            f.startswith('.github/')
            or f.startswith('.gitlab/')
            or f.endswith(('.yml', '.yaml'))
            for f in files
        )

        has_new_goal_python_file = (
            'new file mode' in diff_content
            and any(f.startswith('goal/') and f.endswith('.py') for f in files)
        )
        
        # Analyze file paths
        for file_path in files:
            file_lower = file_path.lower()
            for change_type, patterns in self.TYPE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, file_lower):
                        scores[change_type] += 2
        
        # Analyze diff content
        diff_lower = diff_content.lower()
        for change_type, patterns in self.TYPE_PATTERNS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, diff_lower))
                scores[change_type] += matches
        
        # Heuristic based on statistics
        if stats['files'] == 1:
            # Single file changes
            file = files[0]
            if any(test in file for test in ['test', 'spec']):
                scores['test'] += 3
            elif file.endswith('.md'):
                scores['docs'] += 3
        
        # Add/delete ratio heuristics
        ratio = stats['added'] / max(stats['deleted'], 1)
        if ratio > 5:
            scores['feat'] += 2  # Lots of additions = new feature
        elif ratio < 0.5:
            scores['refactor'] += 2  # Lots of deletions = refactoring
        elif stats['deleted'] > stats['added']:
            scores['fix'] += 1  # More deletions might be bug fix

        # If code exists, down-weight docs a bit to prevent wrong type
        if has_package_code:
            scores['docs'] = max(0, scores['docs'] - 5)
            scores['chore'] += 1

        # New functionality signals
        if has_package_code:
            if re.search(r'^\+\s*def\s+\w+\s*\(', diff_content, re.MULTILINE):
                scores['feat'] += 3
            if re.search(r'^\+\s*@click\.(command|group|option)\b', diff_content, re.MULTILINE):
                scores['feat'] += 4
            if 'new command' in diff_lower or 'add command' in diff_lower:
                scores['feat'] += 2

        if has_new_goal_python_file:
            scores['feat'] += 4

        # Prefer fix when diff mentions bug/error explicitly
        if any(k in diff_lower for k in ['fix', 'bug', 'error', 'exception', 'crash']):
            scores['fix'] += 2

        if has_docs_only:
            scores['docs'] += 5

        if has_ci_only:
            scores['build'] += 5
        
        # Special cases
        if any('version' in f or 'package' in f or 'pyproject' in f for f in files):
            scores['chore'] += 3
        
        if any('docker' in f or 'ci' in f or 'cd' in f for f in files):
            scores['build'] += 3
        
        # Prefer fix when we clearly fix something
        if scores.get('fix', 0) >= max(scores.get('feat', 0), scores.get('chore', 0), scores.get('docs', 0)) + 1:
            return 'fix'

        # If changes are docs-only or CI-only, force the expected type
        if has_docs_only and not has_package_code:
            return 'docs'
        if has_ci_only and not has_package_code:
            return 'build'

        # Prefer feat when we clearly add new capabilities (avoid defaulting to chore)
        if has_package_code and (
            re.search(r'^\+\s*@click\.(command|group|option)\b', diff_content, re.MULTILINE)
            or has_new_goal_python_file
            or scores.get('feat', 0) >= scores.get('chore', 0)
        ):
            return 'feat'

        # Return the type with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'chore'  # Default
    
    def detect_scope(self, files: List[str]) -> Optional[str]:
        """Detect the scope of changes based on file paths."""
        scope_counts = Counter()
        
        for file_path in files:
            for scope, pattern in self.SCOPE_PATTERNS.items():
                if re.search(pattern, file_path.lower()):
                    scope_counts[scope] += 1
        
        if scope_counts:
            # Prefer core package scope when present
            if any(f.startswith('goal/') for f in files):
                return 'goal'
            return scope_counts.most_common(1)[0][0]
        
        # Try to extract from directory structure
        dirs = [os.path.dirname(f).split('/')[0] for f in files if os.path.dirname(f)]
        dir_counts = Counter(d for d in dirs if d and d != '.')
        
        if dir_counts:
            most_common_dir = dir_counts.most_common(1)[0][0]
            # Avoid generic scopes
            if most_common_dir not in ['src', 'lib', 'app']:
                return most_common_dir
        
        return None
    
    def extract_functions_changed(self, diff_content: str) -> List[str]:
        """Extract function/method names from diff."""
        functions = []
        
        # Python functions
        py_funcs = re.findall(r'^\+\s*def\s+(\w+)\s*\(', diff_content, re.MULTILINE)
        functions.extend(py_funcs)
        
        # Python classes
        py_classes = re.findall(r'^\+\s*class\s+(\w+)', diff_content, re.MULTILINE)
        functions.extend([f'class {c}' for c in py_classes])
        
        # JavaScript/TypeScript functions
        js_funcs = re.findall(r'^\+\s*(?:function|const|let|var)\s+(\w+)\s*[=(]', diff_content, re.MULTILINE)
        functions.extend(js_funcs)
        
        # JavaScript classes
        js_classes = re.findall(r'^\+\s*class\s+(\w+)', diff_content, re.MULTILINE)
        functions.extend([f'class {c}' for c in js_classes])
        
        # Return unique functions, limited to 5
        return list(set(functions))[:5]

    def _short_action_summary(self, files: List[str], diff_content: str) -> str:
        """Return a short 2–6 word action summary (no LLM)."""
        file_lower = [f.lower() for f in files]
        diff_lower = diff_content.lower()

        tags: List[str] = []

        has_markdown = any('formatter.py' in f for f in file_lower) or 'markdown' in diff_lower
        has_hooks = any('git-hooks' in f for f in file_lower) or any('prepare-commit-msg' in f for f in file_lower)
        has_commit_gen = any('commit_generator.py' in f for f in file_lower) or 'commit message' in diff_lower
        has_cli = any(f.startswith('goal/') for f in file_lower) and ('@click.' in diff_lower or 'click.option' in diff_lower)

        if has_markdown:
            tags.append('markdown output')
        if has_commit_gen:
            tags.append('commit messages')
        if has_hooks:
            tags.append('hooks')
        if has_cli and not tags:
            tags.append('cli workflow')

        # Build a compact grouped summary from up to 2 themes
        if tags:
            pick = tags[:2]
            if pick == ['markdown output']:
                return 'add markdown output'
            if pick == ['commit messages']:
                return 'improve commit messages'
            if pick == ['hooks']:
                return 'add git hooks'

            if len(pick) == 2:
                # Keep it short: "add X and Y"
                return f"add {pick[0]} and {pick[1]}"

            return f"add {pick[0]}"

        if any(f.startswith('docs/') for f in file_lower) or any('readme.md' in f for f in file_lower):
            if any(f.startswith('goal/') for f in file_lower):
                return 'update cli docs'
            return 'update docs'

        if any(f.startswith('examples/') for f in file_lower):
            if any(f.startswith('goal/') for f in file_lower):
                return 'update examples and cli'
            return 'update examples'

        # Fallbacks
        if len(files) == 1:
            base = os.path.basename(files[0])
            if base.lower().endswith('.md'):
                return 'update documentation'
            return f"update {base}"

        return 'update project'

    def _per_file_notes(self, path: str, cached: bool = True) -> List[str]:
        """Generate small descriptive notes for a file based on added lines heuristics."""
        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')
        cmd.extend(['-U0', '--', path])

        try:
            diff = subprocess.run(cmd, capture_output=True, text=True).stdout
        except Exception:
            return []

        notes: List[str] = []
        added_lines = [l[1:].strip() for l in diff.splitlines() if l.startswith('+') and not l.startswith('+++')]

        if path.endswith('.py'):
            funcs = re.findall(r'^def\s+(\w+)\s*\(', '\n'.join(added_lines), re.MULTILINE)
            classes = re.findall(r'^class\s+(\w+)', '\n'.join(added_lines), re.MULTILINE)
            if classes:
                notes.append('add classes: ' + ', '.join(sorted(set(classes))[:4]))
            if funcs:
                notes.append('add functions: ' + ', '.join(sorted(set(funcs))[:4]))
            if any('click.option' in l for l in added_lines):
                notes.append('add/update cli options')
            if any('markdown' in l.lower() for l in added_lines):
                notes.append('add markdown formatting')

        if path.endswith(('.md', '.rst')):
            # Filter out changelog noise from headings
            noise_patterns = [
                r'^\[.*\d+\.\d+.*\]',  # [1.2.0]
                r'^\d{4}-\d{2}-\d{2}',  # Dates
                r'^(Added|Changed|Deprecated|Removed|Fixed|Security)$',
                r'^(Changelog|CHANGELOG|Unreleased)',
                r'^v?\d+\.\d+',  # Version numbers
            ]
            headings = []
            for l in added_lines:
                if l.startswith('#'):
                    h = re.sub(r'^#+\s*', '', l).strip()
                    if h and len(h) > 2:
                        if not any(re.match(p, h, re.IGNORECASE) for p in noise_patterns):
                            headings.append(h)
            if headings:
                notes.append('update sections: ' + ', '.join(headings[:4]))
            elif 'changelog' in path.lower():
                notes.append('update changelog entries')
            elif 'readme' in path.lower():
                notes.append('update documentation')

        if path.endswith('.sh'):
            if any('chmod' in l or 'hook' in l for l in added_lines):
                notes.append('add hook install script')

        # Deduplicate and cap
        out = []
        for n in notes:
            if n not in out:
                out.append(n)
        return out[:3]
    
    def generate_commit_message(self, cached: bool = True, paths: Optional[List[str]] = None, 
                                 abstraction_level: str = None) -> str:
        """Generate a conventional commit message.
        
        Args:
            cached: Whether to use cached (staged) changes.
            paths: Optional list of specific file paths to analyze.
            abstraction_level: Abstraction level ('auto', 'high', 'medium', 'low').
                              If None, uses config or falls back to legacy.
        """
        # Get all the data
        files = self.get_changed_files(cached, paths=paths)
        if not files:
            return None
        
        # Use smart generator if available and configured
        if self._smart_generator and abstraction_level != 'legacy':
            try:
                analysis = self._smart_generator.analyze_changes(files)
                level = abstraction_level if abstraction_level else None
                return self._smart_generator.generate_message(analysis, level)
            except Exception:
                pass  # Fall back to legacy generation
        
        diff_content = self.get_diff_content(cached, paths=paths)
        stats = self.get_diff_stats(cached)
        
        # Classify the change
        change_type = self.classify_change_type(files, diff_content, stats)
        
        # Detect scope
        scope = self.detect_scope(files)
        
        # Extract functions for detailed messages
        functions = self.extract_functions_changed(diff_content)
        
        # Build the message
        if scope:
            base = f"{change_type}({scope})"
        else:
            base = change_type

        # Short action summary (2–6 words)
        desc = self._short_action_summary(files, diff_content)
        return f"{base}: {desc}"
    
    def generate_abstraction_message(self, level: str = 'auto', 
                                      cached: bool = True) -> Optional[Dict[str, Any]]:
        """Generate commit message with abstraction-based analysis.
        
        Args:
            level: Abstraction level ('auto', 'high', 'medium', 'low').
            cached: Whether to use cached (staged) changes.
            
        Returns:
            Dict with 'title', 'body', 'analysis', and 'level' keys, or None.
        """
        if not self._smart_generator:
            return None
        
        files = self.get_changed_files(cached)
        if not files:
            return None
        
        try:
            analysis = self._smart_generator.analyze_changes(files)
            actual_level = level if level != 'auto' else self._smart_generator.abstraction.determine_abstraction_level(analysis)
            
            title = self._smart_generator.generate_message(analysis, actual_level)
            
            # Generate detailed body
            detailed = self.generate_detailed_message(cached)
            body = detailed['body'] if detailed else ''
            
            return {
                'title': title,
                'body': body,
                'analysis': analysis,
                'level': actual_level,
            }
        except Exception:
            return None
    
    def generate_changelog_entry(self, cached: bool = True, 
                                  commit_hash: str = None) -> Optional[Dict[str, Any]]:
        """Generate structured changelog entry using smart abstraction.
        
        Returns:
            Dict with changelog entry details, or None.
        """
        if not self._smart_generator:
            return None
        
        files = self.get_changed_files(cached)
        if not files:
            return None
        
        try:
            analysis = self._smart_generator.analyze_changes(files)
            return self._smart_generator.generate_changelog_entry(analysis, commit_hash)
        except Exception:
            return None
    
    def generate_enhanced_summary(self, cached: bool = True, 
                                   paths: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Generate enhanced business-value focused summary.
        
        Returns:
            Dict with 'title', 'body', 'capabilities', 'roles', 'relations', 
            'metrics', and 'analysis' keys, or None.
        """
        if not self._enhanced_generator:
            return None
        
        files = self.get_changed_files(cached, paths=paths)
        if not files:
            return None
        
        try:
            diff_content = self.get_diff_content(cached, paths=paths)
            if paths:
                numstat_map = self.get_numstat_map(cached, paths=paths)
                lines_added = sum(v[0] for v in numstat_map.values())
                lines_deleted = sum(v[1] for v in numstat_map.values())
            else:
                stats = self.get_diff_stats(cached)
                lines_added = stats.get('added', 0)
                lines_deleted = stats.get('deleted', 0)

            result = self._enhanced_generator.generate_enhanced_summary(
                files,
                diff_content,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
            )

            # Use intent from enhanced summary (more accurate classification)
            commit_type = result.get('intent', 'refactor')
            scope = self.detect_scope(files)

            # Enhance title with conventional commit format
            if result.get('title'):
                result['title'] = f"{commit_type}({scope}): {result['title']}"

            return result
        except Exception:
            return None
    
    def generate_detailed_message(self, cached: bool = True, paths: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate a detailed commit message with body."""
        # Try enhanced summary first if available
        if self._enhanced_generator:
            enhanced = self.generate_enhanced_summary(cached, paths)
            if enhanced:
                return {
                    'title': enhanced['title'],
                    'body': enhanced['body'],
                    'enhanced': True,
                    'metrics': enhanced.get('metrics'),
                    'capabilities': enhanced.get('capabilities'),
                    'roles': enhanced.get('roles'),
                    'relations': enhanced.get('relations'),
                    'intent': enhanced.get('intent'),
                    'analysis': enhanced.get('analysis'),
                    'files': enhanced.get('files')
                }
        
        main_msg = self.generate_commit_message(cached, paths=paths)
        if not main_msg:
            return None
        
        files = self.get_changed_files(cached, paths=paths)
        stats = self.get_diff_stats(cached)
        diff_content = self.get_diff_content(cached, paths=paths)

        name_status = self.get_name_status(cached, paths=paths)
        numstat_map = self.get_numstat_map(cached, paths=paths)

        added_files = [p for s, p in name_status if s.startswith('A')]
        deleted_files = [p for s, p in name_status if s.startswith('D')]
        modified_files = [p for s, p in name_status if s.startswith('M') or s.startswith('R') or s.startswith('C')]
        # Fallback: treat unknown as modified
        known = set(added_files + deleted_files + modified_files)
        modified_files.extend([f for f in files if f not in known])

        # Group files by top-level dir and by extension for better summary
        dir_counter = Counter((f.split('/')[0] if '/' in f else '.') for f in files)
        ext_counter = Counter((Path(f).suffix or 'other') for f in files)

        symbols = self.extract_functions_changed(diff_content)
        
        # Build body with file details
        body_parts = []
        
        # Add statistics
        body_parts.append(f"Statistics: {stats['files']} files changed, {stats['added']} insertions, {stats['deleted']} deletions")

        # High-level summary
        body_parts.append("\nSummary:")
        body_parts.append("- Dirs: " + ", ".join(f"{k}={v}" for k, v in dir_counter.most_common(6)))
        body_parts.append("- Exts: " + ", ".join(f"{k}={v}" for k, v in ext_counter.most_common(6)))
        body_parts.append(f"- A/M/D: {len(added_files)}/{len(modified_files)}/{len(deleted_files)}")
        if added_files:
            body_parts.append("- Added: " + ", ".join(added_files[:8]) + (" ..." if len(added_files) > 8 else ""))
        if deleted_files:
            body_parts.append("- Deleted: " + ", ".join(deleted_files[:8]) + (" ..." if len(deleted_files) > 8 else ""))
        if symbols:
            body_parts.append("- Symbols: " + ", ".join(symbols))

        # File status lists with per-file +X/-X
        def fmt_file_list(title: str, items: List[str]):
            if not items:
                return
            body_parts.append(f"\n{title}:")
            for p in items[:20]:
                a, d = numstat_map.get(p, (0, 0))
                body_parts.append(f"- {p} (+{a}/-{d})")
            if len(items) > 20:
                body_parts.append(f"- ... and {len(items) - 20} more")

        fmt_file_list('Added files', added_files)
        fmt_file_list('Modified files', modified_files)
        fmt_file_list('Deleted files', deleted_files)

        # Per-file descriptive notes for small changes
        if len(files) <= 6:
            body_parts.append("\nChanges (notes):")
            for p in files:
                a, d = numstat_map.get(p, (0, 0))
                notes = self._per_file_notes(p, cached=cached)
                if notes:
                    body_parts.append(f"- {p} (+{a}/-{d}): " + '; '.join(notes))
                else:
                    body_parts.append(f"- {p} (+{a}/-{d}): update")
        
        # Implementation notes (heuristics, no LLM)
        body_parts.append("\nImplementation notes (heuristics):")
        body_parts.append("- Type inferred from file paths + diff keywords + add/delete ratio")
        body_parts.append("- Scope prefers 'goal' when goal/* is touched; otherwise based on top-level dirs")
        body_parts.append("- For <=6 files: generate short per-file notes from added lines (defs/classes/click options/headings)")
        body_parts.append("- A/M/D derived from git name-status; per-file +X/-X from git numstat")
        
        return {
            'title': main_msg,
            'body': '\n'.join(body_parts)
        }


# Convenience function for direct usage
def generate_smart_commit_message(cached: bool = True) -> str:
    """Generate a smart commit message."""
    generator = CommitMessageGenerator()
    return generator.generate_commit_message(cached)


# Example usage as a script
if __name__ == '__main__':
    import sys
    
    generator = CommitMessageGenerator()
    
    # Check if we want detailed output
    if '--detailed' in sys.argv:
        result = generator.generate_detailed_message()
        if result:
            print(result['title'])
            print()
            print(result['body'])
    else:
        msg = generator.generate_commit_message()
        if msg:
            print(msg)
        else:
            sys.exit(1)
