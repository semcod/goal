"""Smart commit message generation with code abstraction.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.smart_commit package.
"""

# Re-export everything from the new smart_commit package for backward compatibility
try:
    from .smart_commit import (
        CodeAbstraction,
        SmartCommitGenerator,
        create_smart_generator,
    )
except ImportError:
    # Fallback if relative imports fail
    from goal.smart_commit import (
        CodeAbstraction,
        SmartCommitGenerator,
        create_smart_generator,
    )


# Maintain backward compatibility for direct function access
__all__ = [
    'CodeAbstraction',
    'SmartCommitGenerator',
    'create_smart_generator',
]
