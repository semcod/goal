"""Smart commit package - Code abstraction and smart commit message generation.

This package provides tools for generating meaningful commit messages
by analyzing code changes and extracting abstractions.
"""

from .abstraction import CodeAbstraction
from .generator import SmartCommitGenerator, create_smart_generator

__all__ = [
    'CodeAbstraction',
    'SmartCommitGenerator',
    'create_smart_generator',
]
