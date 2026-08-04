"""Recovery strategies for different git push failure scenarios.

Backward-compatible shim — classes now live in individual modules under
goal/recovery/.  Import from here or from goal.recovery as before.
"""

from .base import RecoveryStrategy
from .auth import AuthErrorStrategy
from .large_file import LargeFileStrategy
from .divergent import DivergentHistoryStrategy
from .corrupted import CorruptedObjectStrategy
from .lfs import LFSIssueStrategy
from .force_push import ForcePushStrategy

__all__ = [
    "RecoveryStrategy",
    "AuthErrorStrategy",
    "LargeFileStrategy",
    "DivergentHistoryStrategy",
    "CorruptedObjectStrategy",
    "LFSIssueStrategy",
    "ForcePushStrategy",
]
