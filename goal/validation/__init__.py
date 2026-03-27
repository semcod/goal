"""Custom validation rules for Goal.

Provides functionality for:
- User-defined validation rules
- Custom commit message validation
- File pattern validation
- Custom validation scripts
"""

from .manager import ValidationRuleManager, run_custom_validations
from .rules import (
    MessagePatternRule,
    FilePatternRule,
    ScriptRule,
    CommitSizeRule,
    AVAILABLE_RULES
)

__all__ = [
    'ValidationRuleManager',
    'run_custom_validations',
    'MessagePatternRule',
    'FilePatternRule',
    'ScriptRule',
    'CommitSizeRule',
    'AVAILABLE_RULES',
]
