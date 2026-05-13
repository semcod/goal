"""Custom validation rule implementations."""

import os
import re
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ValidationRule(ABC):
    """Base class for custom validation rules."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate based on rule configuration.

        Args:
            context: Dictionary with validation context (files, message, stats, etc.)

        Returns:
            Tuple of (success, error_message)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get rule name."""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate rule configuration."""
        pass


class MessagePatternRule(ValidationRule):
    """Validate commit message against pattern."""

    def get_name(self) -> str:
        """Return the registry name ``"message_pattern"``."""
        return "message_pattern"

    def validate_config(self) -> bool:
        """Require a ``pattern`` key in the rule config."""
        return "pattern" in self.config

    def validate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        message = context.get("message", "")
        pattern = self.config.get("pattern", "")

        if not pattern:
            return True, None

        try:
            if re.search(pattern, message, re.IGNORECASE):
                return True, None
            else:
                error_msg = self.config.get(
                    "error_message",
                    f"Commit message does not match required pattern: {pattern}",
                )
                return False, error_msg
        except re.error as e:
            return False, f"Invalid regex pattern: {e}"


class FilePatternRule(ValidationRule):
    """Validate files against pattern rules."""

    def get_name(self) -> str:
        """Return the registry name ``"file_pattern"``."""
        return "file_pattern"

    def validate_config(self) -> bool:
        """Require a ``pattern`` key in the rule config."""
        return "pattern" in self.config

    def validate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        files = context.get("files", [])
        pattern = self.config.get("pattern", "")
        min_count = self.config.get("min_count", 0)
        max_count = self.config.get("max_count", None)
        forbidden = self.config.get("forbidden", False)

        if not pattern:
            return True, None

        try:
            matching_files = [f for f in files if re.search(pattern, f)]
            count = len(matching_files)

            if forbidden:
                if count > 0:
                    return (
                        False,
                        f"Forbidden file pattern '{pattern}' found in: {', '.join(matching_files[:3])}",
                    )
                return True, None

            if min_count and count < min_count:
                return (
                    False,
                    f"Expected at least {min_count} files matching '{pattern}', found {count}",
                )

            if max_count is not None and count > max_count:
                return (
                    False,
                    f"Expected at most {max_count} files matching '{pattern}', found {count}",
                )

            return True, None
        except re.error as e:
            return False, f"Invalid regex pattern: {e}"


class ScriptRule(ValidationRule):
    """Run custom validation script."""

    def get_name(self) -> str:
        """Return the registry name ``"script"``."""
        return "script"

    def validate_config(self) -> bool:
        """Require a ``command`` key in the rule config."""
        return "command" in self.config

    def validate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        command = self.config.get("command")
        if not command:
            return False, "Script command not configured"

        # Set environment variables with context
        env = os.environ.copy()
        env["GOAL_COMMIT_MESSAGE"] = context.get("message", "")
        env["GOAL_COMMIT_HASH"] = context.get("hash", "")
        env["GOAL_STAGED_FILES"] = "\n".join(context.get("files", []))

        working_dir = self.config.get("working_dir", ".")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.get("timeout", 60),
            )

            if result.returncode == 0:
                return True, None
            else:
                error_msg = (
                    result.stderr.strip()
                    or f"Script failed with exit code {result.returncode}"
                )
                return False, error_msg
        except subprocess.TimeoutExpired:
            return False, "Validation script timed out"
        except Exception as e:
            return False, f"Script execution failed: {e}"


class CommitSizeRule(ValidationRule):
    """Validate commit size (lines changed)."""

    def get_name(self) -> str:
        return "commit_size"

    def validate_config(self) -> bool:
        return True

    def validate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        stats = context.get("stats", {})

        total_added = sum(s.get("added", 0) for s in stats.values())
        total_deleted = sum(s.get("deleted", 0) for s in stats.values())
        total_changed = total_added + total_deleted

        max_lines = self.config.get("max_lines")
        max_files = self.config.get("max_files")
        min_files = self.config.get("min_files")

        files = context.get("files", [])
        file_count = len(files)

        if max_lines and total_changed > max_lines:
            return (
                False,
                f"Commit too large: {total_changed} lines changed (max: {max_lines})",
            )

        if max_files and file_count > max_files:
            return False, f"Too many files: {file_count} (max: {max_files})"

        if min_files and file_count < min_files:
            return False, f"Too few files: {file_count} (min: {min_files})"

        return True, None


class MessageLengthRule(ValidationRule):
    """Validate commit message length."""

    def get_name(self) -> str:
        return "message_length"

    def validate_config(self) -> bool:
        return True

    def validate(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        message = context.get("message", "")
        title = message.split("\n")[0] if message else ""

        min_length = self.config.get("min_length")
        max_length = self.config.get("max_length")
        max_title_length = self.config.get("max_title_length")

        if min_length and len(message) < min_length:
            return (
                False,
                f"Commit message too short: {len(message)} chars (min: {min_length})",
            )

        if max_length and len(message) > max_length:
            return (
                False,
                f"Commit message too long: {len(message)} chars (max: {max_length})",
            )

        if max_title_length and len(title) > max_title_length:
            return (
                False,
                f"Commit title too long: {len(title)} chars (max: {max_title_length})",
            )

        return True, None


# Registry of available rules
AVAILABLE_RULES = {
    "message_pattern": MessagePatternRule,
    "file_pattern": FilePatternRule,
    "script": ScriptRule,
    "commit_size": CommitSizeRule,
    "message_length": MessageLengthRule,
}
