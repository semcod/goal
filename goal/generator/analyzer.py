"""Analysis logic for commit message generation - extracted from commit_generator.py."""

import re
import os
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from pathlib import Path


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


class ContentAnalyzer:
    """Analyze content for short summaries and per-file notes."""
    
    def short_action_summary(self, files: List[str], diff_content: str) -> str:
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

    def per_file_notes(self, path: str, cached: bool = True) -> List[str]:
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


__all__ = ['ChangeAnalyzer', 'ContentAnalyzer']
