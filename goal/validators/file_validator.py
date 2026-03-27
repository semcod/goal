"""File validator for security checks before commit.

This module validates files before they are committed to prevent:
- Large files that GitHub would reject (>10MB by default)
- API tokens and sensitive credentials from being leaked
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


def validate_files(
    files: List[str],
    max_size_mb: float = 10.0,
    block_large_files: bool = True,
    token_patterns: Optional[List[str]] = None,
    detect_tokens: bool = True,
    exclude_patterns: Optional[Set[str]] = None
) -> None:
    """Validate files before commit.
    
    Args:
        files: List of file paths to validate
        max_size_mb: Maximum file size in megabytes
        block_large_files: Whether to block large files or just warn
        token_patterns: List of regex patterns for token detection
        detect_tokens: Whether to check for tokens
        exclude_patterns: Set of file patterns to exclude from validation
        
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
            if block_large_files:
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
    
    # Handle None config
    if config is None:
        # Use defaults when no config is available
        max_size_mb = 10.0
        block_large_files = True
        detect_tokens = True
        token_patterns = []
    else:
        # Get validation settings from config
        validation_config = config.get('advanced.file_validation', {})
        max_size_mb = validation_config.get('max_file_size_mb', 10.0)
        block_large_files = validation_config.get('block_large_files', True)
        detect_tokens = validation_config.get('detect_api_tokens', True)
        token_patterns = validation_config.get('token_patterns', [])
    
    # Run validation
    validate_files(
        files=files,
        max_size_mb=max_size_mb,
        block_large_files=block_large_files,
        token_patterns=token_patterns,
        detect_tokens=detect_tokens
    )
