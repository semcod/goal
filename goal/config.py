"""Goal YAML configuration management.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.config package.
"""

# Re-export everything from the new config package for backward compatibility
try:
    from .config import (
        GoalConfig,
        init_config,
        load_config,
        ensure_config,
        DEFAULT_CONFIG,
    )
except ImportError:
    # Fallback if relative imports fail
    from goal.config import (
        GoalConfig,
        init_config,
        load_config,
        ensure_config,
        DEFAULT_CONFIG,
    )


# Maintain backward compatibility for direct function access
__all__ = [
    'GoalConfig',
    'init_config',
    'load_config',
    'ensure_config',
    'DEFAULT_CONFIG',
]
