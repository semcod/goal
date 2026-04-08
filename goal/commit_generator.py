"""Smart commit message generator using lightweight Python libraries.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.generator package.
"""

# Re-export everything from the new generator package for backward compatibility
from goal.generator import (
    CommitMessageGenerator,
    generate_smart_commit_message,
    GitDiffOperations,
    ChangeAnalyzer,
    ContentAnalyzer,
)


# Maintain backward compatibility for direct function access
__all__ = [
    'CommitMessageGenerator',
    'generate_smart_commit_message',
    'GitDiffOperations',
    'ChangeAnalyzer',
    'ContentAnalyzer',
]


# Example usage as a script
if __name__ == '__main__':
    import sys

    generator = CommitMessageGenerator()

    # Check if we want detailed output
    if '--detailed' in sys.argv:
        result = generator.generate_detailed_message()
        if result:
            print(result['title'])
            print()
            print(result['body'])
    else:
        msg = generator.generate_commit_message()
        if msg:
            print(msg)
        else:
            sys.exit(1)