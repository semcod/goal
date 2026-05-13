"""Tests for goal/changelog.py."""

import tempfile
from pathlib import Path
from goal.changelog import update_changelog


def test_update_changelog_creates_new_file():
    """Test that update_changelog creates CHANGELOG.md if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            update_changelog("1.0.0", ["file1.py", "file2.py"], "feat: add new feature")

            changelog = Path("CHANGELOG.md")
            assert changelog.exists()
            content = changelog.read_text()
            assert "1.0.0" in content
            assert "file1.py" in content
            assert "file2.py" in content
        finally:
            os.chdir(old_cwd)


def test_update_changelog_appends_to_existing():
    """Test that update_changelog appends to existing CHANGELOG.md."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            # Create initial changelog
            initial = """# Changelog

## [Unreleased]

### Changed
- Initial version
"""
            Path("CHANGELOG.md").write_text(initial)

            update_changelog("1.1.0", ["new_feature.py"], "feat: add feature")

            content = Path("CHANGELOG.md").read_text()
            assert "1.1.0" in content
            assert "new_feature.py" in content
            assert "Initial version" in content  # Original preserved
        finally:
            os.chdir(old_cwd)


def test_update_changelog_with_domain_grouping():
    """Test domain grouping feature."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            config = {
                "git": {
                    "changelog": {"group_by_domain": True},
                    "commit": {
                        "domain_mapping": {
                            "feat/*": "feat",
                            "fix/*": "fix",
                            "docs/*": "docs",
                        }
                    },
                }
            }

            update_changelog(
                "2.0.0",
                ["feat/auth.py", "fix/bug.py", "docs/readme.md"],
                "release: version 2.0.0",
                config=config,
            )

            content = Path("CHANGELOG.md").read_text()
            assert "2.0.0" in content
            assert "### Feat" in content or "feat" in content.lower()
        finally:
            os.chdir(old_cwd)


def test_update_changelog_limits_files():
    """Test that more than 10 files gets truncated."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            files = [f"file{i}.py" for i in range(15)]
            update_changelog("1.0.0", files, "feat: many changes")

            content = Path("CHANGELOG.md").read_text()
            assert "and 5 more files" in content
        finally:
            os.chdir(old_cwd)


def test_update_changelog_with_unreleased_section():
    """Test handling of existing [Unreleased] section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            initial = """# Changelog

## [Unreleased]

### Added
- Some feature

## [1.0.0] - 2024-01-01

Initial release.
"""
            Path("CHANGELOG.md").write_text(initial)

            update_changelog("1.1.0", ["bugfix.py"], "fix: bug fix")

            content = Path("CHANGELOG.md").read_text()
            assert "1.1.0" in content
            assert "[Unreleased]" in content
            assert "1.0.0" in content
        finally:
            os.chdir(old_cwd)
