"""Post-commit actions for Goal.

Provides functionality for:
- Running custom scripts after commit
- Sending notifications
- Updating external systems
- Automated follow-up tasks
"""

from .manager import PostCommitManager, run_post_commit_actions
from .actions import (
    NotificationAction,
    WebhookAction,
    ScriptAction,
    GitPushAction,
    AVAILABLE_ACTIONS,
)

__all__ = [
    "PostCommitManager",
    "run_post_commit_actions",
    "NotificationAction",
    "WebhookAction",
    "ScriptAction",
    "GitPushAction",
    "AVAILABLE_ACTIONS",
]
