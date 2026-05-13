"""Project bootstrapping - re-exports for backward compatibility."""

from goal.bootstrap.detector import detect_project_types_deep
from goal.bootstrap.installer import ensure_project_environment
from goal.bootstrap.configurator import scaffold_test_file

__all__ = [
    "detect_project_types_deep",
    "ensure_project_environment",
    "scaffold_test_file",
]
