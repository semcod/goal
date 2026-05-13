"""
Commit message generation example.

Shows how to generate smart commit messages using Goal's API.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from goal.generator import generate_smart_commit_message
from goal.git_ops import get_staged_files, get_diff_content


def main():
    """Demonstrate commit message generation."""
    print("=" * 60)
    print("Goal API - Commit Message Generation")
    print("=" * 60)

    # Get staged files and diff
    files = get_staged_files()
    diff = get_diff_content()

    if not files or files == [""]:
        print("\n✗ No staged files to analyze")
        print("   Run: git add <files>")
        return

    print(f"\n1. Analyzing {len(files)} staged files...")
    print(f"   Diff size: {len(diff)} chars")

    # Generate smart commit message
    print("\n2. Generating smart commit message...")
    try:
        message = generate_smart_commit_message(cached=False)
        if message:
            print(f"   Generated: {message[:70]}...")
        else:
            print("   (no message generated - check if files are staged)")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Alternative: Generate with abstraction levels
    print("\n3. Alternative: Using CommitMessageGenerator directly...")
    try:
        from goal.generator import CommitMessageGenerator

        generator = CommitMessageGenerator()

        # Try different abstraction levels
        for level in ["minimal", "summary", "detailed"]:
            try:
                msg = generator.generate_commit_message(
                    cached=False, paths=files[:5], abstraction_level=level
                )
                if msg:
                    print(f"   {level}: {msg[:50]}...")
            except Exception as e:
                print(f"   {level}: (error: {e})")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
