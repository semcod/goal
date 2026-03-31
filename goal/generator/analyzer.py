"""Analysis logic for commit message generation - extracted from commit_generator.py."""

import re
import os
import subprocess
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Tuple


class ChangeAnalyzer:
    """Analyze git changes to classify type, detect scope, and extract functions."""
    
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
    
    def classify_change_type(self, files: List[str], diff_content: str, stats: Dict[str, int]) -> str:
        """Classify the type of change using pattern matching and heuristics."""
        scores = defaultdict(int)

        # Detect signal types from files and diff
        signals = self._detect_signals(files, diff_content)

        # Score based on file patterns and diff content
        self._score_by_file_patterns(scores, files)
        self._score_by_diff_content(scores, diff_content)
        self._score_by_statistics(scores, files, stats)
        self._score_by_signals(scores, signals, files, diff_content)

        # Apply preference rules and return final type
        return self._resolve_change_type(scores, signals, files, diff_content)

    def _detect_signals(self, files: List[str], diff_content: str) -> Dict[str, bool]:
        """Detect key signals from files and diff content."""
        return {
            'has_package_code': self._has_package_code(files),
            'has_docs_only': self._is_docs_only(files),
            'has_ci_only': self._is_ci_only(files),
            'has_new_goal_python_file': self._has_new_goal_python_file(files, diff_content),
        }

    def _has_package_code(self, files: List[str]) -> bool:
        """Check if changes include code in main package directories."""
        return any(
            (f.startswith('goal/') or f.startswith('src/') or f.startswith('lib/'))
            and (f.endswith('.py') or f.endswith('.js') or f.endswith('.ts'))
            for f in files
        )

    def _is_docs_only(self, files: List[str]) -> bool:
        """Check if changes are documentation-only."""
        return all(
            f.endswith(('.md', '.rst', '.txt')) or 'docs/' in f or 'readme' in f.lower()
            for f in files
        )

    def _is_ci_only(self, files: List[str]) -> bool:
        """Check if changes are CI/CD-only."""
        return all(
            f.startswith('.github/') or f.startswith('.gitlab/') or f.endswith(('.yml', '.yaml'))
            for f in files
        )

    def _has_new_goal_python_file(self, files: List[str], diff_content: str) -> bool:
        """Check if a new Python file is being added to goal/."""
        return (
            'new file mode' in diff_content
            and any(f.startswith('goal/') and f.endswith('.py') for f in files)
        )

    def _score_by_file_patterns(self, scores: defaultdict, files: List[str]) -> None:
        """Score change types based on file path patterns."""
        for file_path in files:
            file_lower = file_path.lower()
            for change_type, patterns in self.TYPE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, file_lower):
                        scores[change_type] += 2

    def _score_by_diff_content(self, scores: defaultdict, diff_content: str) -> None:
        """Score change types based on diff content patterns."""
        diff_lower = diff_content.lower()
        for change_type, patterns in self.TYPE_PATTERNS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, diff_lower))
                scores[change_type] += matches

    def _score_by_statistics(self, scores: defaultdict, files: List[str], stats: Dict[str, int]) -> None:
        """Apply scoring heuristics based on change statistics."""
        # Single file heuristics
        if stats['files'] == 1:
            file = files[0]
            if any(test in file for test in ['test', 'spec']):
                scores['test'] += 3
            elif file.endswith('.md'):
                scores['docs'] += 3

        # Add/delete ratio heuristics
        ratio = stats['added'] / max(stats['deleted'], 1)
        if ratio > 5:
            scores['feat'] += 2
        elif ratio < 0.5:
            scores['refactor'] += 2
        elif stats['deleted'] > stats['added']:
            scores['fix'] += 1

    def _score_by_signals(self, scores: defaultdict, signals: Dict[str, bool], files: List[str], diff_content: str) -> None:
        """Apply scoring based on detected signals."""
        if signals['has_package_code']:
            scores['docs'] = max(0, scores['docs'] - 5)
            scores['chore'] += 1
            self._score_new_functionality(scores, signals, diff_content)

        if signals['has_new_goal_python_file']:
            scores['feat'] += 4

        # Explicit bug fix mentions
        if any(k in diff_content.lower() for k in ['fix', 'bug', 'error', 'exception', 'crash']):
            scores['fix'] += 2

        if signals['has_docs_only']:
            scores['docs'] += 5

        if signals['has_ci_only']:
            scores['build'] += 5

        # Version/config file signals
        if any('version' in f or 'package' in f or 'pyproject' in f for f in files):
            scores['chore'] += 3

        if any('docker' in f or 'ci' in f or 'cd' in f for f in files):
            scores['build'] += 3

    def _score_new_functionality(self, scores: defaultdict, signals: Dict[str, bool], diff_content: str) -> None:
        """Score for new functionality signals in code."""
        if re.search(r'^\+\s*def\s+\w+\s*\(', diff_content, re.MULTILINE):
            scores['feat'] += 3
        if re.search(r'^\+\s*@click\.(command|group|option)\b', diff_content, re.MULTILINE):
            scores['feat'] += 4
        if 'new command' in diff_content.lower() or 'add command' in diff_content.lower():
            scores['feat'] += 2

    def _resolve_change_type(self, scores: defaultdict, signals: Dict[str, bool],
                             files: List[str], diff_content: str) -> str:
        """Resolve the final change type from scores and signals."""
        has_package_code = signals['has_package_code']
        has_docs_only = signals['has_docs_only']
        has_ci_only = signals['has_ci_only']
        has_new_goal_python_file = signals['has_new_goal_python_file']

        # Prefer fix when clearly fixing something
        if scores.get('fix', 0) >= max(scores.get('feat', 0), scores.get('chore', 0), scores.get('docs', 0)) + 1:
            return 'fix'

        # Force docs/build for exclusive changes
        if has_docs_only and not has_package_code:
            return 'docs'
        if has_ci_only and not has_package_code:
            return 'build'

        # Prefer feat for new capabilities
        if has_package_code and (
            re.search(r'^\+\s*@click\.(command|group|option)\b', diff_content, re.MULTILINE)
            or has_new_goal_python_file
            or scores.get('feat', 0) >= scores.get('chore', 0)
        ):
            return 'feat'

        # Return highest scoring type
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return 'chore'
    
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


class ContentAnalyzer:
    """Analyze content for short summaries and per-file notes."""

    # Tag detectors: (label, file_match, diff_match)
    # A tag is activated when file_match(files) or diff_match(diff) is truthy.
    _TAG_DETECTORS: List[Tuple[str, str, str]] = [
        ('markdown output', 'formatter.py', 'markdown'),
        ('commit messages', 'commit_generator.py', 'commit message'),
        ('hooks',          'git-hooks',     'prepare-commit-msg'),
    ]

    # Single-tag → fixed summary overrides
    _TAG_SUMMARIES: Dict[str, str] = {
        'markdown output': 'add markdown output',
        'commit messages': 'improve commit messages',
        'hooks':           'add git hooks',
    }

    # Noise patterns for changelog/version headings in .md/.rst files
    _HEADING_NOISE = [
        r'^\[.*\d+\.\d+.*\]',
        r'^\d{4}-\d{2}-\d{2}',
        r'^(Added|Changed|Deprecated|Removed|Fixed|Security)$',
        r'^(Changelog|CHANGELOG|Unreleased)',
        r'^v?\d+\.\d+',
    ]

    def short_action_summary(self, files: List[str], diff_content: str) -> str:
        """Return a short 2–6 word action summary (no LLM)."""
        file_lower = [f.lower() for f in files]
        diff_lower = diff_content.lower()

        tags = self._detect_tags(file_lower, diff_lower)

        if tags:
            return self._summary_from_tags(tags)

        fallback = self._summary_from_paths(file_lower, files)
        if fallback:
            return fallback

        return 'update project'

    def _detect_tags(self, file_lower: List[str], diff_lower: str) -> List[str]:
        """Detect thematic tags from files and diff content."""
        tags: List[str] = []
        for label, file_needle, diff_needle in self._TAG_DETECTORS:
            if any(file_needle in f for f in file_lower) or diff_needle in diff_lower:
                tags.append(label)

        # CLI tag only when no other tags matched
        if not tags:
            has_cli = (any(f.startswith('goal/') for f in file_lower)
                       and ('@click.' in diff_lower or 'click.option' in diff_lower))
            if has_cli:
                tags.append('cli workflow')
        return tags

    def _summary_from_tags(self, tags: List[str]) -> str:
        """Build summary string from detected tags."""
        pick = tags[:2]
        if len(pick) == 1 and pick[0] in self._TAG_SUMMARIES:
            return self._TAG_SUMMARIES[pick[0]]
        if len(pick) == 2:
            return f"add {pick[0]} and {pick[1]}"
        return f"add {pick[0]}"

    def _summary_from_paths(self, file_lower: List[str], files: List[str]) -> Optional[str]:
        """Derive summary from file paths when no tags matched."""
        has_goal = any(f.startswith('goal/') for f in file_lower)

        if any(f.startswith('docs/') for f in file_lower) or any('readme.md' in f for f in file_lower):
            return 'update cli docs' if has_goal else 'update docs'

        if any(f.startswith('examples/') for f in file_lower):
            return 'update examples and cli' if has_goal else 'update examples'

        if len(files) == 1:
            base = os.path.basename(files[0])
            return 'update documentation' if base.lower().endswith('.md') else f"update {base}"

        return None

    # ------------------------------------------------------------------
    # per_file_notes
    # ------------------------------------------------------------------

    def per_file_notes(self, path: str, cached: bool = True) -> List[str]:
        """Generate small descriptive notes for a file based on added lines heuristics."""
        added_lines = self._get_added_lines(path, cached)
        if added_lines is None:
            return []

        notes: List[str] = []
        if path.endswith('.py'):
            self._notes_python(added_lines, notes)
        if path.endswith(('.md', '.rst')):
            self._notes_docs(added_lines, path, notes)
        if path.endswith('.sh'):
            self._notes_shell(added_lines, notes)

        # Deduplicate and cap
        return list(dict.fromkeys(notes))[:3]

    @staticmethod
    def _get_added_lines(path: str, cached: bool) -> Optional[List[str]]:
        """Extract added lines from git diff."""
        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')
        cmd.extend(['-U0', '--', path])
        try:
            diff = subprocess.run(cmd, capture_output=True, text=True).stdout
        except Exception:
            return None
        return [l[1:].strip() for l in diff.splitlines() if l.startswith('+') and not l.startswith('+++')]

    @staticmethod
    def _notes_python(added_lines: List[str], notes: List[str]) -> None:
        """Collect notes for Python files."""
        joined = '\n'.join(added_lines)
        classes = re.findall(r'^class\s+(\w+)', joined, re.MULTILINE)
        funcs = re.findall(r'^def\s+(\w+)\s*\(', joined, re.MULTILINE)
        if classes:
            notes.append(f"add classes: {', '.join(sorted(set(classes))[:4])}")
        if funcs:
            notes.append(f"add functions: {', '.join(sorted(set(funcs))[:4])}")
        if any('click.option' in l for l in added_lines):
            notes.append('add/update cli options')
        if any('markdown' in l.lower() for l in added_lines):
            notes.append('add markdown formatting')

    @classmethod
    def _notes_docs(cls, added_lines: List[str], path: str, notes: List[str]) -> None:
        """Collect notes for documentation files."""
        headings = []
        for l in added_lines:
            if l.startswith('#'):
                h = re.sub(r'^#+\s*', '', l).strip()
                if h and len(h) > 2:
                    if not any(re.match(p, h, re.IGNORECASE) for p in cls._HEADING_NOISE):
                        headings.append(h)
        if headings:
            notes.append(f"update sections: {', '.join(headings[:4])}")
        elif 'changelog' in path.lower():
            notes.append('update changelog entries')
        elif 'readme' in path.lower():
            notes.append('update documentation')

    @staticmethod
    def _notes_shell(added_lines: List[str], notes: List[str]) -> None:
        """Collect notes for shell scripts."""
        if any('chmod' in l or 'hook' in l for l in added_lines):
            notes.append('add hook install script')


__all__ = ['ChangeAnalyzer', 'ContentAnalyzer']
