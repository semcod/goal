"""Goal recovery module - Automated git push recovery system.

This module provides automated recovery from common git push failures:
- Invalid/expired tokens
- Large files exceeding GitHub limits
- Divergent history conflicts
- Corrupted objects
- LFS configuration issues
- Force-push recovery
"""

from .strategies import (
    RecoveryStrategy,
    AuthErrorStrategy,
    LargeFileStrategy,
    DivergentHistoryStrategy,
    CorruptedObjectStrategy,
    LFSIssueStrategy,
    ForcePushStrategy,
)
from .manager import RecoveryManager
from .exceptions import (
    RecoveryError,
    AuthError,
    LargeFileError,
    DivergentHistoryError,
    CorruptedObjectError,
    LFSIssueError,
    RollbackError,
)

__all__ = [
    "RecoveryStrategy",
    "RecoveryManager",
    "AuthErrorStrategy",
    "LargeFileStrategy",
    "DivergentHistoryStrategy",
    "CorruptedObjectStrategy",
    "LFSIssueStrategy",
    "ForcePushStrategy",
    "RecoveryError",
    "AuthError",
    "LargeFileError",
    "DivergentHistoryError",
    "CorruptedObjectError",
    "LFSIssueError",
    "RollbackError",
]
