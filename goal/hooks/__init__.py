"""Pre-commit hooks integration for Goal.

Provides functionality for:
- Installing pre-commit hooks
- Running validation checks before commits
- Managing hook configuration
"""

from .manager import HooksManager, install_hooks, uninstall_hooks, run_hooks
from .config import get_hook_config, create_precommit_config

__all__ = [
    'HooksManager',
    'install_hooks',
    'uninstall_hooks',
    'run_hooks',
    'get_hook_config',
    'create_precommit_config',
]
