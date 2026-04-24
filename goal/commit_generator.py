# Imports used in this function:
from goal.generator import (
    CommitMessageGenerator,
    generate_smart_commit_message,
    GitDiffOperations,
    ChangeAnalyzer,
    ContentAnalyzer,
)

from typing import Dict, Any

# Neighboring function:
def is_detailed_output_requested(args: list) -> bool:
    return '--detailed' in args


# Neighboring function:
def display_commit_message(generator: CommitMessageGenerator) -> None:
    print(generate_smart_commit_message(generator))


def print_detailed_message(result: Dict[str, Any]) -> None:
    if result:
        print(result['title'])
        print()
        print(result['body'])


# Function to refactor:
def display_detailed_message(generator: CommitMessageGenerator) -> None:
    result = generator.generate_detailed_message()
    print_detailed_message(result)