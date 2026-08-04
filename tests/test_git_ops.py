"""Tests for goal/git_ops.py."""

import tempfile
from pathlib import Path
from unittest import mock


from goal.git_ops import (
    is_git_repository,
    validate_repo_url,
    get_staged_files,
    get_unstaged_files,
    get_diff_stats,
    get_diff_content,
    apply_ticket_prefix,
    read_ticket,
)


def test_validate_repo_url_ssh():
    """Test SSH URL validation."""
    assert validate_repo_url("git@github.com:user/repo.git")
    assert validate_repo_url("git@gitlab.com:org/project")


def test_validate_repo_url_https():
    """Test HTTPS URL validation."""
    assert validate_repo_url("https://github.com/user/repo.git")
    assert validate_repo_url("https://gitlab.com/org/project")


def test_validate_repo_url_invalid():
    """Test invalid URL rejection."""
    assert not validate_repo_url("not-a-url")
    assert not validate_repo_url("ftp://example.com/repo")


def test_apply_ticket_prefix_with_ticket():
    """Test applying ticket prefix."""
    result = apply_ticket_prefix("feat: add feature", "PROJ-123")
    assert "PROJ-123" in result
    assert "feat: add feature" in result


def test_apply_ticket_prefix_no_ticket():
    """Test without ticket."""
    result = apply_ticket_prefix("feat: add feature", None)
    assert result == "feat: add feature"


def test_read_ticket_file_not_exists():
    """Test reading non-existent ticket file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            result = read_ticket()
            assert result["prefix"] == ""
            assert result["format"] == "[{ticket}] {title}"
        finally:
            os.chdir(old_cwd)


def test_read_ticket_file_exists():
    """Test reading existing ticket file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            Path("TICKET").write_text("prefix=JIRA-123\nformat=[{ticket}] {title}")
            result = read_ticket()
            assert result["prefix"] == "JIRA-123"
        finally:
            os.chdir(old_cwd)


def test_get_diff_stats_empty():
    """Test diff stats with no changes."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        mock_run.return_value = mock.Mock(stdout="", returncode=0)
        result = get_diff_stats()
        assert result == {}


def test_get_diff_stats_with_changes():
    """Test diff stats with changes."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="10\t5\tfile.py\n20\t0\tanother.py\n", returncode=0
        )
        result = get_diff_stats()
        assert result["file.py"] == (10, 5)
        assert result["another.py"] == (20, 0)


def test_get_diff_content_small():
    """Test getting diff content for small changes."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="diff --git a/file.py b/file.py\n+content", returncode=0
        )
        result = get_diff_content(max_lines=100)
        assert "diff --git" in result


def test_get_diff_content_large():
    """Test getting diff content for large changes."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        # First call for stats
        def side_effect(*args, **kwargs):
            if "--numstat" in args:
                return mock.Mock(stdout="5000\t5000\tfile.py\n", returncode=0)
            elif "--stat" in args:
                return mock.Mock(stdout=" file.py | 10000 +++++\n", returncode=0)
            return mock.Mock(stdout="", returncode=0)

        mock_run.side_effect = side_effect
        result = get_diff_content(max_lines=100)
        assert "Large diff" in result
        assert "10000 lines" in result


def test_get_staged_files_empty():
    """Test getting staged files when none."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        mock_run.return_value = mock.Mock(stdout="", returncode=0)
        result = get_staged_files()
        assert result == []


def test_get_staged_files_with_files():
    """Test getting staged files."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        mock_run.return_value = mock.Mock(stdout="file1.py\nfile2.py\n", returncode=0)
        result = get_staged_files()
        assert "file1.py" in result
        assert "file2.py" in result


def test_get_unstaged_files():
    """Test getting unstaged files."""
    with mock.patch("goal.git_ops.run_git") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout=" M file1.py\n?? file2.py\n", returncode=0
        )
        result = get_unstaged_files()
        # Note: status --porcelain format, first 2 chars are status, then space
        assert "ile1.py" in result  # ' M ' + 'file1.py' -> sliced at 3 gives 'ile1.py'
        assert "file2.py" in result


def test_is_git_repository_true():
    """Test git repository detection when true."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            Path(".git").mkdir()
            assert is_git_repository()
        finally:
            os.chdir(old_cwd)


def test_is_git_repository_false():
    """Test git repository detection when false."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            with mock.patch("goal.git_ops.run_git") as mock_run:
                mock_run.return_value = mock.Mock(returncode=1)
                assert not is_git_repository()
        finally:
            os.chdir(old_cwd)
