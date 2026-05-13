"""Exception classes for the recovery system."""


class RecoveryError(Exception):
    """Base exception for all recovery operations."""

    def __init__(self, message: str, details: str = None):
        """Store ``message`` and optional human-readable ``details``."""
        self.message = message
        self.details = details
        super().__init__(message)


class AuthError(RecoveryError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: str = None):
        """Construct an authentication-failure recovery error."""
        super().__init__(message, details)


class LargeFileError(RecoveryError):
    """Raised when large files block the push."""

    def __init__(self, message: str = "Large file detected", files: list = None):
        """Record the offending ``files`` and build a details string from them."""
        self.files = files or []
        details = f"Files: {', '.join(self.files)}" if self.files else None
        super().__init__(message, details)


class DivergentHistoryError(RecoveryError):
    """Raised when local and remote histories have diverged."""

    def __init__(
        self, message: str = "Divergent history detected", details: str = None
    ):
        """Construct a divergent-history recovery error."""
        super().__init__(message, details)


class CorruptedObjectError(RecoveryError):
    """Raised when git objects are corrupted."""

    def __init__(
        self, message: str = "Corrupted git objects detected", details: str = None
    ):
        """Construct a corrupted-object recovery error."""
        super().__init__(message, details)


class LFSIssueError(RecoveryError):
    """Raised when Git LFS has issues."""

    def __init__(self, message: str = "Git LFS issue detected", details: str = None):
        """Construct a Git LFS recovery error."""
        super().__init__(message, details)


class RollbackError(RecoveryError):
    """Raised when rollback operation fails."""

    def __init__(self, message: str = "Rollback failed", details: str = None):
        super().__init__(message, details)


class NetworkError(RecoveryError):
    """Raised when network connectivity issues occur."""

    def __init__(self, message: str = "Network error", details: str = None):
        super().__init__(message, details)


class QuotaExceededError(RecoveryError):
    """Raised when GitHub API quota is exceeded."""

    def __init__(self, message: str = "API quota exceeded", details: str = None):
        super().__init__(message, details)
