"""File validator for security checks before commit.

This module validates files before they are committed to prevent:
- Large files that GitHub would reject (>10MB by default)
- API tokens and sensitive credentials from being leaked
- Unintended dot folders (like .idea, .vscode) from being committed
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Set
import click


class ValidationError(Exception):
    """Base validation error."""
    pass


class FileSizeError(ValidationError):
    """Error for files exceeding size limit."""
    def __init__(self, file_path: str, size_mb: float, limit_mb: float):
        self.file_path = file_path
        self.size_mb = size_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"File {file_path} is {size_mb:.1f}MB, which exceeds the limit of {limit_mb}MB"
        )


class TokenDetectedError(ValidationError):
    """Error when API tokens are detected in files."""
    def __init__(self, file_path: str, token_type: str, line_num: Optional[int] = None):
        self.file_path = file_path
        self.token_type = token_type
        self.line_num = line_num
        location = f" at line {line_num}" if line_num else ""
        super().__init__(
            f"Potential {token_type} token detected in {file_path}{location}. "
            "Please remove or replace with environment variable."
        )


class DotFolderError(ValidationError):
    """Error when dot folders are detected that should be in .gitignore."""
    def __init__(self, dot_folders: List[str]):
        self.dot_folders = dot_folders
        super().__init__(
            f"Dot folders/files detected that should be in .gitignore: {', '.join(dot_folders)}"
        )


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except OSError:
        return 0.0


def detect_tokens_in_content(content: str, patterns: List[str]) -> List[Tuple[str, Optional[int]]]:
    """Detect tokens in file content using regex patterns.
    
    Returns:
        List of (token_type, line_number) tuples
    """
    detected = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            try:
                if re.search(pattern, line, re.IGNORECASE):
                    # Determine token type from pattern
                    if 'ghp_' in pattern or 'gho_' in pattern or 'ghu_' in pattern:
                        token_type = "GitHub Personal Access"
                    elif 'AKIA' in pattern:
                        token_type = "AWS Access Key"
                    elif 'sk-' in pattern:
                        token_type = "Stripe API"
                    elif 'xoxb' in pattern:
                        token_type = "Slack Bot"
                    elif 'xoxp' in pattern:
                        token_type = "Slack User"
                    elif 'glpat' in pattern:
                        token_type = "GitLab"
                    elif 'Bearer' in pattern:
                        token_type = "Bearer Token"
                    elif 'Token' in pattern:
                        token_type = "API Token"
                    else:
                        token_type = "API Key"
                    
                    detected.append((token_type, line_num))
                    # Only report first match per line to avoid spam
                    break
            except re.error:
                # Skip invalid regex patterns
                continue
    
    return detected


def load_gitignore(gitignore_path: str = '.gitignore') -> Tuple[Set[str], Set[str]]:
    """Load .gitignore patterns, returning (ignored_patterns, whitelisted_patterns)."""
    ignored = set()
    whitelisted = set()
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('!'):
                    whitelisted.add(line[1:])
                else:
                    ignored.add(line)
    
    return ignored, whitelisted


def save_gitignore(ignored: Set[str], gitignore_path: str = '.gitignore') -> None:
    """Save patterns to .gitignore."""
    # Read existing content to preserve comments and order
    existing_lines = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            existing_lines = f.readlines()
    
    # Find where to insert new patterns (before any existing patterns)
    insert_idx = 0
    for i, line in enumerate(existing_lines):
        if line.strip() and not line.strip().startswith('#'):
            insert_idx = i
            break
    
    # Insert new patterns
    new_patterns = [p + '\n' for p in sorted(ignored) if p not in ''.join(existing_lines)]
    if new_patterns:
        existing_lines[insert_idx:insert_idx] = new_patterns
        
        with open(gitignore_path, 'w') as f:
            f.writelines(existing_lines)


def check_dot_folders(files: List[str], config) -> List[str]:
    """Check for dot folders/files that should be in .gitignore.
    
    Returns:
        List of dot folders/files that need to be added to .gitignore
    """
    # Common safe dot files that shouldn't trigger warnings
    safe_dot_files = {
        '.gitignore', '.gitattributes', '.editorconfig', '.git',
        '.github', '.gitlab-ci.yml', '.pre-commit-config.yaml'
    }
    
    # Load current .gitignore
    ignored, whitelisted = load_gitignore()
    
    # Get configuration
    auto_manage = config.get('advanced.file_validation.auto_manage_gitignore', True) if config else True
    known_dot_folders = config.get('advanced.file_validation.known_dot_folders', []) if config else []
    
    # Add known problematic folders
    problematic_folders = {
        '.idea', '.vscode', '.DS_Store', 'Thumbs.db', '.pytest_cache',
        '.coverage', '.mypy_cache', '.tox', '.nox', '.venv', '.env',
        '.python-version', '.ruff_cache', '.cursorignore', '.cursorindexingignore'
    }
    problematic_folders.update(known_dot_folders)
    
    # Check staged files
    problematic_found = []
    for file_path in files:
        path = Path(file_path)
        
        # Check if it's a dot file/folder or has a dot parent
        is_dot_file = path.name.startswith('.')
        has_dot_parent = any(p.startswith('.') for p in path.parts[:-1])  # Check all parts except the filename
        
        if not (is_dot_file or has_dot_parent):
            continue
        
        # Skip safe files
        if path.name in safe_dot_files:
            continue
        
        # Skip if any parent is safe
        if any(p in safe_dot_files for p in path.parts[:-1]):
            continue
        
        # Skip if explicitly whitelisted
        is_whitelisted = False
        for pattern in whitelisted:
            if path.match(pattern) or any(p.match(pattern) for p in [path] + list(path.parents)):
                is_whitelisted = True
                break
        if is_whitelisted:
            continue
        
        # Skip if already ignored
        if any(path.match(pattern) for pattern in ignored):
            continue
        
        # Check if it matches problematic patterns
        if (path.name in problematic_folders or 
            any(path.name.startswith(folder) or str(path).startswith(folder + '/') for folder in problematic_folders) or
            any(str(path).startswith(folder + '/') for folder in problematic_folders)):
            problematic_found.append(str(path))
    
    return problematic_found


def manage_dot_folders(files: List[str], config, dry_run: bool = False) -> None:
    """Proactively manage dot folders in .gitignore.
    
    Args:
        files: List of staged files to check
        config: GoalConfig object
        dry_run: If True, only report what would be done
        
    Raises:
        DotFolderError: If problematic dot folders are found
    """
    problematic = check_dot_folders(files, config)
    
    if not problematic:
        return
    
    # Get configuration
    auto_add = config.get('advanced.file_validation.auto_add_dot_folders', True) if config else True
    
    if auto_add and not dry_run:
        # Load current ignored patterns
        ignored, _ = load_gitignore()
        
        # Add problematic patterns
        for item in problematic:
            # Add directory pattern if it's a directory
            if os.path.isdir(item):
                ignored.add(f"{item}/")
            else:
                ignored.add(item)
        
        # Save updated .gitignore
        save_gitignore(ignored)
        
        click.echo(click.style(
            f"✅ Added {len(problematic)} dot folder(s)/file(s) to .gitignore: {', '.join(problematic)}",
            fg='green'
        ))
        
        # Re-stage files to unstage the newly ignored ones
        from goal.git_ops import run_git
        run_git('add', '.gitignore')
        run_git('update-index', '--refresh')
        
        # Show which files were unstaged
        for item in problematic:
            if os.path.exists(item):
                run_git('reset', '--', item)
                click.echo(click.style(f"  → Unstaged: {item}", fg='yellow'))
    else:
        # Just report the issue
        raise DotFolderError(problematic)


def validate_files(
    files: List[str],
    max_size_mb: float = 10.0,
    block_large_files: bool = True,
    token_patterns: Optional[List[str]] = None,
    detect_tokens: bool = True,
    exclude_patterns: Optional[Set[str]] = None,
    auto_handle_large: bool = True
) -> List[str]:
    """Validate files before commit.
    
    Args:
        files: List of file paths to validate
        max_size_mb: Maximum file size in megabytes
        block_large_files: Whether to block large files or just warn
        token_patterns: List of regex patterns for token detection
        detect_tokens: Whether to check for tokens
        exclude_patterns: Set of file patterns to exclude from validation
        auto_handle_large: Whether to automatically handle large files
        
    Returns:
        List of large files that were handled
        
    Raises:
        FileSizeError: If a file exceeds size limit and blocking is enabled
        TokenDetectedError: If tokens are detected in files
    """
    if exclude_patterns is None:
        exclude_patterns = {
            '.git/', '.gitignore', '.DS_Store', 'Thumbs.db',
            '*.pyc', '*.pyo', '__pycache__/', '.pytest_cache/',
            'node_modules/', '.npm/', '.cache/', '*.log', '*.tmp'
        }
    
    large_files_found = []
    
    # Default token patterns if not provided
    if token_patterns is None:
        token_patterns = [
            r'ghp_[a-zA-Z0-9]{36}',
            r'gho_[a-zA-Z0-9]{36}',
            r'ghu_[a-zA-Z0-9]{36}',
            r'ghs_[a-zA-Z0-9]{36}',
            r'ghr_[a-zA-Z0-9]{36}',
            r'AKIA[0-9A-Z]{16}',
            r'sk-[a-zA-Z0-9]{48}',
            r'xoxb-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}',
            r'xoxp-[0-9]{13}-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}',
            r'glpat-[a-zA-Z0-9_-]{20}',
            r'pk_live_[a-zA-Z0-9]{24}',
            r'pk_test_[a-zA-Z0-9]{24}',
            r'sk_live_[a-zA-Z0-9]{24}',
            r'sk_test_[a-zA-Z0-9]{24}',
            r'[a-zA-Z0-9_-]{20,}=[a-zA-Z0-9_-]{20,}',
            r'Bearer\s+[a-zA-Z0-9_-]{20,}',
            r'Token\s+[a-zA-Z0-9_-]{20,}',
            r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----',
            r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----',
            r'-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----',
            r'^[A-Z_]+=[a-zA-Z0-9_-]{20,}',
        ]
    
    # Check each file
    for file_path in files:
        # Skip excluded patterns
        if any(file_path.endswith(pattern.replace('*', '')) or pattern in file_path 
               for pattern in exclude_patterns):
            continue
        
        # Check file exists
        if not os.path.exists(file_path):
            continue
        
        # Check file size
        size_mb = get_file_size_mb(file_path)
        if size_mb > max_size_mb:
            large_files_found.append(file_path)
            if auto_handle_large:
                # Auto-handle by adding to gitignore
                continue
            elif block_large_files:
                raise FileSizeError(file_path, size_mb, max_size_mb)
            else:
                click.echo(
                    click.style(
                        f"Warning: {file_path} is {size_mb:.1f}MB (exceeds {max_size_mb}MB limit)",
                        fg='yellow'
                    )
                )
        
        # Check for tokens in text files
        if detect_tokens and size_mb <= 1.0:  # Only check files <= 1MB for performance
            try:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                detected = detect_tokens_in_content(content, token_patterns)
                for token_type, line_num in detected:
                    raise TokenDetectedError(file_path, token_type, line_num)
                    
            except UnicodeDecodeError:
                # Skip binary files
                pass
            except PermissionError:
                # Skip files we can't read
                pass
    
    # Auto-handle large files if found
    if large_files_found and auto_handle_large:
        handle_large_files(large_files_found)
    
    return large_files_found


def handle_large_files(large_files: List[str]) -> None:
    """Automatically handle large files by adding them to .gitignore and unstaging.
    
    Args:
        large_files: List of large file paths to handle
    """
    if not large_files:
        return
    
    # Load current ignored patterns
    ignored, _ = load_gitignore()
    
    # Add large files to gitignore
    for file_path in large_files:
        ignored.add(file_path)
    
    # Save updated .gitignore
    save_gitignore(ignored)
    
    click.echo(click.style(
        f"✅ Added {len(large_files)} large file(s) to .gitignore: {', '.join(large_files)}",
        fg='green'
    ))
    
    # Re-stage files to unstage the large files
    from goal.git_ops import run_git
    run_git('add', '.gitignore')
    run_git('update-index', '--refresh')
    
    # Show which files were unstaged
    for file_path in large_files:
        if os.path.exists(file_path):
            run_git('reset', '--', file_path)
            size_mb = get_file_size_mb(file_path)
            click.echo(click.style(f"  → Unstaged: {file_path} ({size_mb:.1f}MB)", fg='yellow'))


def validate_staged_files(config) -> None:
    """Validate staged files using configuration.
    
    This is a convenience function that extracts validation settings
    from the goal config and validates staged files.
    
    Args:
        config: GoalConfig object containing validation settings
        
    Raises:
        ValidationError: If validation fails
    """
    from goal.git_ops import get_staged_files
    
    files = get_staged_files()
    if not files or files == ['']:
        return
    
    # First, manage dot folders
    manage_dot_folders(files, config)
    
    # Get updated list of staged files after dot folder management
    files = get_staged_files()
    if not files or files == ['']:
        return
    
    # Handle None config
    if config is None:
        # Use defaults when no config is available
        max_size_mb = 10.0
        block_large_files = True
        detect_tokens = True
        token_patterns = []
        auto_handle_large = True
    else:
        # Get validation settings from config
        validation_config = config.get('advanced.file_validation', {})
        max_size_mb = validation_config.get('max_file_size_mb', 10.0)
        block_large_files = validation_config.get('block_large_files', True)
        detect_tokens = validation_config.get('detect_api_tokens', True)
        token_patterns = validation_config.get('token_patterns', [])
        auto_handle_large = validation_config.get('auto_handle_large_files', True)
    
    # Run validation with auto-handling
    large_files = validate_files(
        files=files,
        max_size_mb=max_size_mb,
        block_large_files=block_large_files,
        token_patterns=token_patterns,
        detect_tokens=detect_tokens,
        auto_handle_large=auto_handle_large
    )
    
    # If large files were handled, refresh the file list
    if large_files and auto_handle_large:
        files = get_staged_files()
        if not files or files == ['']:
            return
