"""File validator for security checks before commit.

This module is now a compatibility shim. The actual implementations have been split into:
- goal.validators.exceptions - ValidationError and related exceptions
- goal.validators.tokens - Token detection logic
- goal.validators.gitignore - Gitignore management utilities
- goal.validators.dot_folders - Dot folder validation and management

Please update imports to use the new locations directly.
"""

import os
from typing import List, Optional, Set

import click

from goal.validators.exceptions import ValidationError, FileSizeError, TokenDetectedError, DotFolderError
from goal.validators.tokens import detect_tokens_in_content, get_default_token_patterns
from goal.validators.gitignore import load_gitignore, save_gitignore
from goal.validators.dot_folders import check_dot_folders, manage_dot_folders


# Constants for file size limits
BYTES_PER_MB = 1024 * 1024
DEFAULT_MAX_FILE_SIZE_MB = 10
GITHUB_MAX_FILE_SIZE_MB = 100


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    try:
        return os.path.getsize(file_path) / BYTES_PER_MB
    except OSError:
        return 0.0


def _is_excluded(file_path: str, exclude_patterns: Set[str]) -> bool:
    """Check if a file matches any exclusion pattern."""
    return any(
        file_path.endswith(pattern.replace('*', '')) or pattern in file_path
        for pattern in exclude_patterns
    )


def _handle_oversized_file(file_path: str, size_mb: float, max_size_mb: float,
                           auto_handle: bool, block: bool) -> None:
    """Warn or raise for an oversized file (unless auto-handled)."""
    if auto_handle:
        return
    if block:
        raise FileSizeError(file_path, size_mb, max_size_mb)
    click.echo(click.style(
        f"Warning: {file_path} is {size_mb:.1f}MB (exceeds {max_size_mb}MB limit)",
        fg='yellow'
    ))


def _check_file_for_tokens(file_path: str, token_patterns: List[str]) -> None:
    """Read a text file and raise TokenDetectedError if tokens are found."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for token_type, line_num in detect_tokens_in_content(content, token_patterns):
            raise TokenDetectedError(file_path, token_type, line_num)
    except (UnicodeDecodeError, PermissionError):
        pass


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
            'node_modules/', '.npm/', '.cache/', '*.log', '*.tmp',
            'tests/', 'test_*.py', '*_test.py',
            'examples/', 'example/'
        }

    large_files_found = []

    # Default token patterns if not provided
    if token_patterns is None:
        token_patterns = get_default_token_patterns()

    for file_path in files:
        if _is_excluded(file_path, exclude_patterns):
            continue
        if not os.path.exists(file_path):
            continue

        size_mb = get_file_size_mb(file_path)
        if size_mb > max_size_mb:
            large_files_found.append(file_path)
            _handle_oversized_file(file_path, size_mb, max_size_mb,
                                   auto_handle_large, block_large_files)
            if auto_handle_large:
                continue

        if detect_tokens and size_mb <= 1.0:
            _check_file_for_tokens(file_path, token_patterns)

    # Auto-handle large files if found
    if large_files_found and auto_handle_large:
        handle_large_files(large_files_found)

    return large_files_found


def handle_large_files(large_files: List[str]) -> None:
    """Automatically handle large files by adding them to .gitignore and unstaging.

    Args:
        large_files: List of large file paths to handle
    """
    from goal.git_ops import run_git

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
    run_git('add', '.gitignore')
    run_git('update-index', '--refresh')

    # Show which files were unstaged
    for file_path in large_files:
        if os.path.exists(file_path):
            run_git('reset', '--', file_path)
            size_mb = get_file_size_mb(file_path)
            click.echo(click.style(f"  → Unstaged: {file_path} ({size_mb:.1f}MB)", fg='yellow'))


def _get_deleted_staged_files() -> set:
    """Return the set of file paths staged for deletion."""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=D'],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return set(result.stdout.strip().split('\n'))
    except Exception:
        pass
    return set()


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

    # Exclude files staged for deletion — they are being removed, not added.
    deleted = _get_deleted_staged_files()
    if deleted:
        files = [f for f in files if f not in deleted]
    if not files:
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


__all__ = [
    'ValidationError',
    'FileSizeError',
    'TokenDetectedError',
    'DotFolderError',
    'validate_files',
    'validate_staged_files',
    'manage_dot_folders',
    'load_gitignore',
    'save_gitignore',
    'get_file_size_mb',
    'BYTES_PER_MB',
    'DEFAULT_MAX_FILE_SIZE_MB',
    'GITHUB_MAX_FILE_SIZE_MB',
]
