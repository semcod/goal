"""Smart commit generator — compatibility facade."""

from typing import Any, Dict

from goal.smart_commit.generator_core import SmartCommitGeneratorCore
from goal.smart_commit.generator_generate import SmartCommitGeneratorGenerateMixin


class SmartCommitGenerator(SmartCommitGeneratorGenerateMixin, SmartCommitGeneratorCore):
    """Generates smart commit messages using code abstraction."""


def create_smart_generator(config: Dict[str, Any]) -> SmartCommitGenerator:
    """Factory function to create SmartCommitGenerator."""
    return SmartCommitGenerator(config)
