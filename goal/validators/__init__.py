"""Goal validators package - security and file validation.

This package provides validation for files before commit,
including file size limits, API token detection, and proactive .gitignore management.
"""

# Backward compatible exports from file_validator shim
from .file_validator import (
    validate_files,
    validate_staged_files,
    ValidationError,
    FileSizeError,
    TokenDetectedError,
    DotFolderError,
    manage_dot_folders,
    get_file_size_mb,
    BYTES_PER_MB,
    DEFAULT_MAX_FILE_SIZE_MB,
    GITHUB_MAX_FILE_SIZE_MB,
)

# New granular submodule imports
from .exceptions import (
    ValidationError as ValidationError,
    FileSizeError as FileSizeError,
    TokenDetectedError as TokenDetectedError,
    DotFolderError as DotFolderError,
)
from .tokens import detect_tokens_in_content, get_default_token_patterns
from .gitignore import load_gitignore, save_gitignore
from .dot_folders import check_dot_folders

__all__ = [
    'validate_files',
    'validate_staged_files',
    'ValidationError',
    'FileSizeError',
    'TokenDetectedError',
    'DotFolderError',
    'manage_dot_folders',
    'check_dot_folders',
    'detect_tokens_in_content',
    'get_default_token_patterns',
    'load_gitignore',
    'save_gitignore',
    'get_file_size_mb',
    'BYTES_PER_MB',
    'DEFAULT_MAX_FILE_SIZE_MB',
    'GITHUB_MAX_FILE_SIZE_MB',
]
