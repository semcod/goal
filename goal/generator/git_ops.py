"""Git operations for commit message generation - extracted from commit_generator.py."""

import subprocess
from typing import Dict, List, Tuple, Optional


class GitDiffOperations:
    """Git diff operations with caching."""
    
    def __init__(self):
        self.cache = {}
    
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
    
    def clear_cache(self):
        """Clear the operation cache."""
        self.cache.clear()


__all__ = ['GitDiffOperations']
