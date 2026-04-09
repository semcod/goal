from goal.generator import (
    CommitMessageGenerator,
    generate_smart_commit_message,
    GitDiffOperations,
    ChangeAnalyzer,
    ContentAnalyzer,
)

def is_detailed_output_requested(args: list) -> bool:
    return '--detailed' in args

def display_detailed_message(generator: CommitMessageGenerator) -> None:
    result = generator.generate_detailed_message()
    if result:
        print(result['title'])
        print()
        print(result['body'])

def display_commit_message(generator: CommitMessageGenerator) -> None:
    print(generate_smart_commit_message(generator))

def main() -> None:
    import sys

    generator = CommitMessageGenerator()

    if is_detailed_output_requested(sys.argv):
        display_detailed_message(generator)
    else:
        display_commit_message(generator)