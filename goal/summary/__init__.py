"""Summary package - Extracted from monolithic enhanced_summary.py."""

from .quality_filter import SummaryQualityFilter
from .validator import QualityValidator
from .generator import EnhancedSummaryGenerator


# Convenience functions
def generate_business_summary(files, diff_content='', config=None):
    """Convenience function to generate enhanced summary."""
    generator = EnhancedSummaryGenerator(config)
    return generator.generate_enhanced_summary(files, diff_content)


def validate_summary(summary, files=None, config=None):
    """Validate summary against quality gates.
    
    Returns: {valid: bool, errors: [], warnings: [], score: int, fixes: []}
    """
    validator = QualityValidator(config)
    files = files or summary.get('files', [])
    return validator.validate(summary, files)


def auto_fix_summary(summary, files=None, config=None):
    """Auto-fix summary issues and return corrected summary.
    
    Returns: Fixed summary with 'applied_fixes' list
    """
    validator = QualityValidator(config)
    files = files or summary.get('files', [])
    return validator.auto_fix(summary, files)


__all__ = [
    'SummaryQualityFilter',
    'QualityValidator',
    'EnhancedSummaryGenerator',
    'generate_business_summary',
    'validate_summary',
    'auto_fix_summary',
]
