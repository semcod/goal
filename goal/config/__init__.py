"""Goal configuration package - YAML configuration management.

This package provides configuration management for the Goal CLI tool,
including loading, saving, and auto-detecting project settings.
"""

# Constants
from .constants import DEFAULT_CONFIG

# Main config manager
from .manager import (
    GoalConfig,
    init_config,
    load_config,
    ensure_config,
)

__all__ = [
    'GoalConfig',
    'init_config',
    'load_config',
    'ensure_config',
    'DEFAULT_CONFIG',
]
