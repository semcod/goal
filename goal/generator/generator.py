"""Commit message generator - extracted from commit_generator.py."""

import subprocess
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from collections import Counter
import os

try:
    from .git_ops import GitDiffOperations
    from .analyzer import ChangeAnalyzer, ContentAnalyzer
    from ..smart_commit import SmartCommitGenerator
    from ..summary import EnhancedSummaryGenerator
    HAS_SMART_COMMIT = True
    HAS_ENHANCED_SUMMARY = True
except ImportError:
    try:
        from goal.generator.git_ops import GitDiffOperations
        from goal.generator.analyzer import ChangeAnalyzer, ContentAnalyzer
        from goal.smart_commit import SmartCommitGenerator
        from goal.summary import EnhancedSummaryGenerator
        HAS_SMART_COMMIT = True
        HAS_ENHANCED_SUMMARY = True
    except ImportError:
        HAS_SMART_COMMIT = False
        HAS_ENHANCED_SUMMARY = False
        GitDiffOperations = None
        ChangeAnalyzer = None
        ContentAnalyzer = None


class CommitMessageGenerator:
    """Generate conventional commit messages using diff analysis and lightweight classification."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.cache = {}
        self.config = config
        self._smart_generator = None
        self._enhanced_generator = None
        self._git_ops = GitDiffOperations() if GitDiffOperations else None
        self._change_analyzer = ChangeAnalyzer() if ChangeAnalyzer else None
        self._content_analyzer = ContentAnalyzer() if ContentAnalyzer else None
        
        # Initialize smart generator if config provided
        if config and HAS_SMART_COMMIT:
            self._smart_generator = SmartCommitGenerator(config)
        
        # Initialize enhanced summary generator
        if HAS_ENHANCED_SUMMARY:
            self._enhanced_generator = EnhancedSummaryGenerator(config or {})
    
    def get_diff_stats(self, cached: bool = True) -> Dict[str, int]:
        """Get diff statistics using git command."""
        if self._git_ops:
            return self._git_ops.get_diff_stats(cached)
        return {'files': 0, 'added': 0, 'deleted': 0}

    def get_name_status(self, cached: bool = True, paths: Optional[List[str]] = None) -> List[Tuple[str, str]]:
        """Return list of (status, path) from git diff --name-status."""
        if self._git_ops:
            return self._git_ops.get_name_status(cached, paths)
        return []

    def get_numstat_map(self, cached: bool = True, paths: Optional[List[str]] = None) -> Dict[str, Tuple[int, int]]:
        """Return map path -> (added, deleted) from git diff --numstat."""
        if self._git_ops:
            return self._git_ops.get_numstat_map(cached, paths)
        return {}
    
    def get_changed_files(self, cached: bool = True, paths: Optional[List[str]] = None) -> List[str]:
        """Get list of changed files."""
        if self._git_ops:
            return self._git_ops.get_changed_files(cached, paths)
        return []
    
    def get_diff_content(self, cached: bool = True, paths: Optional[List[str]] = None) -> str:
        """Get diff content for analysis."""
        if self._git_ops:
            return self._git_ops.get_diff_content(cached, paths)
        return ""
    
    def classify_change_type(self, files: List[str], diff_content: str, stats: Dict[str, int]) -> str:
        """Classify the type of change using pattern matching and heuristics."""
        if self._change_analyzer:
            return self._change_analyzer.classify_change_type(files, diff_content, stats)
        return 'chore'
    
    def detect_scope(self, files: List[str]) -> Optional[str]:
        """Detect the scope of changes based on file paths."""
        if self._change_analyzer:
            return self._change_analyzer.detect_scope(files)
        return None
    
    def extract_functions_changed(self, diff_content: str) -> List[str]:
        """Extract function/method names from diff."""
        if self._change_analyzer:
            return self._change_analyzer.extract_functions_changed(diff_content)
        return []

    def _short_action_summary(self, files: List[str], diff_content: str) -> str:
        """Return a short 2–6 word action summary (no LLM)."""
        if self._content_analyzer:
            return self._content_analyzer.short_action_summary(files, diff_content)
        return 'update project'

    def _per_file_notes(self, path: str, cached: bool = True) -> List[str]:
        """Generate small descriptive notes for a file based on added lines heuristics."""
        if self._content_analyzer:
            return self._content_analyzer.per_file_notes(path, cached)
        return []
    
    def generate_commit_message(self, cached: bool = True, paths: Optional[List[str]] = None, 
                                 abstraction_level: str = None) -> str:
        """Generate a conventional commit message."""
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
        """Generate commit message with abstraction-based analysis."""
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
        """Generate structured changelog entry using smart abstraction."""
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
        """Generate enhanced business-value focused summary."""
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
    
    def _try_enhanced_summary(self, cached: bool, paths: Optional[List[str]]) -> Optional[Dict[str, str]]:
        """Try to generate enhanced summary if available."""
        if not self._enhanced_generator:
            return None
        enhanced = self.generate_enhanced_summary(cached, paths)
        if not enhanced:
            return None
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

    def _classify_files(self, name_status: List[Tuple[str, str]], files: List[str]) -> Tuple[List[str], List[str], List[str]]:
        """Classify files into added, deleted, modified."""
        added_files = [p for s, p in name_status if s.startswith('A')]
        deleted_files = [p for s, p in name_status if s.startswith('D')]
        modified_files = [p for s, p in name_status if s.startswith('M') or s.startswith('R') or s.startswith('C')]
        # Fallback: treat unknown as modified
        known = set(added_files + deleted_files + modified_files)
        modified_files.extend([f for f in files if f not in known])
        return added_files, deleted_files, modified_files

    def _build_statistics_section(self, stats: Dict[str, int]) -> str:
        """Build statistics line for commit body."""
        return f"Statistics: {stats['files']} files changed, {stats['added']} insertions, {stats['deleted']} deletions"

    def _build_summary_section(
        self,
        files: List[str],
        added_files: List[str],
        modified_files: List[str],
        deleted_files: List[str],
        symbols: List[str]
    ) -> List[str]:
        """Build high-level summary section."""
        from collections import Counter
        dir_counter = Counter((f.split('/')[0] if '/' in f else '.') for f in files)
        ext_counter = Counter((Path(f).suffix or 'other') for f in files)
        
        parts = ["\nSummary:"]
        parts.append("- Dirs: " + ", ".join(f"{k}={v}" for k, v in dir_counter.most_common(6)))
        parts.append("- Exts: " + ", ".join(f"{k}={v}" for k, v in ext_counter.most_common(6)))
        parts.append(f"- A/M/D: {len(added_files)}/{len(modified_files)}/{len(deleted_files)}")
        if added_files:
            parts.append("- Added: " + ", ".join(added_files[:8]) + (" ..." if len(added_files) > 8 else ""))
        if deleted_files:
            parts.append("- Deleted: " + ", ".join(deleted_files[:8]) + (" ..." if len(deleted_files) > 8 else ""))
        if symbols:
            parts.append("- Symbols: " + ", ".join(symbols))
        return parts

    def _build_file_lists(
        self,
        added_files: List[str],
        modified_files: List[str],
        deleted_files: List[str],
        numstat_map: Dict[str, Tuple[int, int]]
    ) -> List[str]:
        """Build file list sections with per-file stats."""
        parts = []
        
        def fmt_file_list(title: str, items: List[str]):
            if not items:
                return
            parts.append(f"\n{title}:")
            for p in items[:20]:
                a, d = numstat_map.get(p, (0, 0))
                parts.append(f"- {p} (+{a}/-{d})")
            if len(items) > 20:
                parts.append(f"- ... and {len(items) - 20} more")
        
        fmt_file_list('Added files', added_files)
        fmt_file_list('Modified files', modified_files)
        fmt_file_list('Deleted files', deleted_files)
        return parts

    def _build_per_file_notes(
        self,
        files: List[str],
        numstat_map: Dict[str, Tuple[int, int]],
        cached: bool
    ) -> List[str]:
        """Build per-file descriptive notes for small changes."""
        if len(files) > 6:
            return []
        
        parts = ["\nChanges (notes):"]
        for p in files:
            a, d = numstat_map.get(p, (0, 0))
            notes = self._per_file_notes(p, cached=cached)
            if notes:
                parts.append(f"- {p} (+{a}/-{d}): " + '; '.join(notes))
            else:
                parts.append(f"- {p} (+{a}/-{d}): update")
        return parts

    def _build_implementation_notes(self) -> List[str]:
        """Build implementation notes section."""
        return [
            "\nImplementation notes (heuristics):",
            "- Type inferred from file paths + diff keywords + add/delete ratio",
            "- Scope prefers 'goal' when goal/* is touched; otherwise based on top-level dirs",
            "- For <=6 files: generate short per-file notes from added lines (defs/classes/click options/headings)",
            "- A/M/D derived from git name-status; per-file +X/-X from git numstat"
        ]

    def generate_detailed_message(self, cached: bool = True, paths: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate a detailed commit message with body."""
        # Try enhanced summary first if available
        enhanced_result = self._try_enhanced_summary(cached, paths)
        if enhanced_result:
            return enhanced_result
        
        main_msg = self.generate_commit_message(cached, paths=paths)
        if not main_msg:
            return None
        
        files = self.get_changed_files(cached, paths=paths)
        stats = self.get_diff_stats(cached)
        diff_content = self.get_diff_content(cached, paths=paths)

        name_status = self.get_name_status(cached, paths=paths)
        numstat_map = self.get_numstat_map(cached, paths=paths)

        added_files, deleted_files, modified_files = self._classify_files(name_status, files)
        symbols = self.extract_functions_changed(diff_content)
        
        # Build body with file details
        body_parts = []
        body_parts.append(self._build_statistics_section(stats))
        body_parts.extend(self._build_summary_section(files, added_files, modified_files, deleted_files, symbols))
        body_parts.extend(self._build_file_lists(added_files, modified_files, deleted_files, numstat_map))
        body_parts.extend(self._build_per_file_notes(files, numstat_map, cached))
        body_parts.extend(self._build_implementation_notes())
        
        return {
            'title': main_msg,
            'body': '\n'.join(body_parts)
        }


# Convenience function for direct usage
def generate_smart_commit_message(cached: bool = True) -> str:
    """Generate a smart commit message."""
    generator = CommitMessageGenerator()
    return generator.generate_commit_message(cached)


__all__ = ['CommitMessageGenerator', 'generate_smart_commit_message']
