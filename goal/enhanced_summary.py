"""Enhanced summary generator for functional commit messages.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.summary package.
"""

from goal.summary import (
    SummaryQualityFilter,
    QualityValidator,
    EnhancedSummaryGenerator,
    generate_business_summary,
    validate_summary,
    auto_fix_summary,
)

__all__ = [
    "SummaryQualityFilter",
    "QualityValidator",
    "EnhancedSummaryGenerator",
    "generate_business_summary",
    "validate_summary",
    "auto_fix_summary",
]
