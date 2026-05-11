"""Thin facade for commit-message generation: dispatches between the
short summary and detailed (title + body) output formats consumed by the
``goal`` CLI.
"""
from goal.generator import (
    CommitMessageGenerator,
    generate_smart_commit_message,
    GitDiffOperations,
    ChangeAnalyzer,
    ContentAnalyzer,
)

from typing import Dict, Any


def is_detailed_output_requested(args: list) -> bool:
    """Return True when ``--detailed`` appears in the CLI argument vector."""
    return '--detailed' in args


def display_commit_message(generator: CommitMessageGenerator) -> None:
    """Print the short, single-line smart commit message for ``generator``."""
    print(generate_smart_commit_message(generator))


def print_detailed_message(result: Dict[str, Any]) -> None:
    """Print a ``title``/``body`` commit message dict produced by ``generator``."""
    if result:
        print(result['title'])
        print()
        print(result['body'])


def display_detailed_message(generator: CommitMessageGenerator) -> None:
    """Generate and print the detailed (title + body) commit message."""
    result = generator.generate_detailed_message()
    print_detailed_message(result)