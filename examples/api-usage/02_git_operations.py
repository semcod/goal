"""
Git operations example using Goal's API.

Shows how to perform git operations programmatically.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from goal.git_ops import (
    get_staged_files,
    get_unstaged_files,
    get_diff_content,
    get_diff_stats,
    is_git_repository,
)


def _check_git_repository() -> bool:
    """Check if current directory is a git repository."""
    print("\n1. Checking git repository...")
    if not is_git_repository():
        print("   ✗ Not a git repository!")
        return False
    print("   ✓ Git repository found")
    return True


def _display_staged_files() -> None:
    """Display staged files."""
    print("\n2. Staged files:")
    staged = get_staged_files()
    if staged and staged != [""]:
        for f in staged[:5]:  # Show first 5
            print(f"   + {f}")
        if len(staged) > 5:
            print(f"   ... and {len(staged) - 5} more")
    else:
        print("   (no staged files)")


def _display_unstaged_files() -> None:
    """Display unstaged files."""
    print("\n3. Unstaged files:")
    unstaged = get_unstaged_files()
    if unstaged and unstaged != [""]:
        for f in unstaged[:5]:
            print(f"   ! {f}")
        if len(unstaged) > 5:
            print(f"   ... and {len(unstaged) - 5} more")
    else:
        print("   (no unstaged files)")


def _display_diff_stats() -> None:
    """Display diff statistics."""
    print("\n4. Diff statistics:")
    stats = get_diff_stats()
    if stats:
        total_adds = sum(s[0] for s in stats.values())
        total_dels = sum(s[1] for s in stats.values())
        print(f"   Total: +{total_adds}/-{total_dels} lines")
        for file, (adds, dels) in list(stats.items())[:3]:
            print(f"   {file}: +{adds}/-{dels}")
    else:
        print("   (no changes)")


def _display_diff_content() -> None:
    """Display diff content preview."""
    print("\n5. Diff preview (first 500 chars):")
    diff = get_diff_content()
    if diff:
        preview = diff[:500].replace("\n", " ")
        print(f"   {preview}...")
    else:
        print("   (no diff)")


def main():
    """Demonstrate git operations."""
    print("=" * 60)
    print("Goal API - Git Operations")
    print("=" * 60)

    if not _check_git_repository():
        return

    _display_staged_files()
    _display_unstaged_files()
    _display_diff_stats()
    _display_diff_content()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
