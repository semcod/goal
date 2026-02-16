"""Tests for external repository cloning and interactive git repo detection."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from goal.cli import (
    is_git_repository,
    validate_repo_url,
    clone_repository,
    ensure_git_repository,
    main,
)


# ---------------------------------------------------------------------------
# validate_repo_url
# ---------------------------------------------------------------------------

class TestValidateRepoUrl:
    """Tests for URL validation (HTTP/HTTPS/SSH)."""

    @pytest.mark.parametrize("url", [
        "https://github.com/user/repo.git",
        "https://github.com/user/repo",
        "http://gitlab.com/org/project.git",
        "https://bitbucket.org/team/repo",
    ])
    def test_valid_http_urls(self, url):
        assert validate_repo_url(url) is True

    @pytest.mark.parametrize("url", [
        "git@github.com:user/repo.git",
        "git@gitlab.com:org/project.git",
        "git@bitbucket.org:team/repo",
    ])
    def test_valid_ssh_urls(self, url):
        assert validate_repo_url(url) is True

    @pytest.mark.parametrize("url", [
        "",
        "not-a-url",
        "ftp://example.com/repo.git",
        "/local/path/to/repo",
        "github.com/user/repo",
        "git@:missing-host.git",
    ])
    def test_invalid_urls(self, url):
        assert validate_repo_url(url) is False

    def test_whitespace_is_stripped(self):
        assert validate_repo_url("  https://github.com/user/repo.git  ") is True


# ---------------------------------------------------------------------------
# is_git_repository
# ---------------------------------------------------------------------------

class TestIsGitRepository:
    def test_true_inside_git_repo(self, tmp_path):
        """Returns True when .git directory exists."""
        (tmp_path / ".git").mkdir()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert is_git_repository() is True
        finally:
            os.chdir(old)

    def test_false_outside_git_repo(self, tmp_path):
        """Returns False in a plain directory."""
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert is_git_repository() is False
        finally:
            os.chdir(old)


# ---------------------------------------------------------------------------
# clone_repository
# ---------------------------------------------------------------------------

class TestCloneRepository:
    def test_invalid_url_returns_failure(self):
        success, msg = clone_repository("not-a-url")
        assert success is False
        assert "Invalid repository URL" in msg

    def test_clone_success(self, tmp_path):
        """Clone a local bare repo to verify the plumbing works."""
        # Create a bare repo to clone from
        bare = tmp_path / "bare.git"
        bare.mkdir()
        subprocess.run(["git", "init", "--bare", str(bare)], check=True,
                        capture_output=True)

        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Use file:// protocol which matches http pattern after we patch validation
            with mock.patch("goal.cli.validate_repo_url", return_value=True):
                success, repo_dir = clone_repository(f"file://{bare}", target_dir="cloned")
            assert success is True
            assert repo_dir == "cloned"
            assert (tmp_path / "cloned" / ".git").exists()
        finally:
            os.chdir(old)

    def test_clone_failure_bad_remote(self, tmp_path):
        """Clone from a non-existent remote returns failure."""
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            with mock.patch("goal.cli.validate_repo_url", return_value=True):
                success, msg = clone_repository("https://invalid.example.com/no/repo.git")
            assert success is False
            assert "Failed to clone" in msg
        finally:
            os.chdir(old)


# ---------------------------------------------------------------------------
# ensure_git_repository (interactive)
# ---------------------------------------------------------------------------

class TestEnsureGitRepository:
    def test_returns_true_when_already_in_repo(self, tmp_path):
        (tmp_path / ".git").mkdir()
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            assert ensure_git_repository() is True
        finally:
            os.chdir(old)

    def test_exit_option(self, tmp_path):
        """User chooses option 3 (exit) → returns False."""
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            with mock.patch("click.prompt", return_value=3):
                assert ensure_git_repository() is False
        finally:
            os.chdir(old)

    def test_init_option(self, tmp_path):
        """User chooses option 2 (git init) → initializes repo."""
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            with mock.patch("click.prompt", return_value=2):
                result = ensure_git_repository()
            assert result is True
            assert (tmp_path / ".git").exists()
        finally:
            os.chdir(old)

    def test_clone_option_with_valid_url(self, tmp_path):
        """User chooses option 1 (clone) with a valid local bare repo."""
        bare = tmp_path / "bare.git"
        bare.mkdir()
        subprocess.run(["git", "init", "--bare", str(bare)], check=True,
                        capture_output=True)

        work = tmp_path / "work"
        work.mkdir()
        old = os.getcwd()
        try:
            os.chdir(work)
            url = f"file://{bare}"
            with mock.patch("click.prompt", side_effect=[1, url]), \
                 mock.patch("goal.cli.validate_repo_url", return_value=True):
                result = ensure_git_repository()
            assert result is True
            # We should now be inside the cloned repo
            assert is_git_repository() is True
        finally:
            os.chdir(old)

    def test_clone_option_invalid_url(self, tmp_path):
        """User chooses option 1 but provides an invalid URL."""
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            with mock.patch("click.prompt", side_effect=[1, "not-a-url"]):
                result = ensure_git_repository()
            assert result is False
        finally:
            os.chdir(old)


# ---------------------------------------------------------------------------
# CLI: goal clone <url>
# ---------------------------------------------------------------------------

class TestCloneCommand:
    def test_clone_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["clone", "--help"])
        assert result.exit_code == 0
        assert "Clone an external git repository" in result.output

    def test_clone_invalid_url(self):
        runner = CliRunner()
        result = runner.invoke(main, ["clone", "not-a-url"])
        assert result.exit_code != 0
        assert "Invalid repository URL" in result.output

    def test_clone_valid_local_bare(self, tmp_path):
        """End-to-end: clone a local bare repo via the CLI command."""
        bare = tmp_path / "bare.git"
        bare.mkdir()
        subprocess.run(["git", "init", "--bare", str(bare)], check=True,
                        capture_output=True)

        runner = CliRunner()
        target = str(tmp_path / "cloned")
        with mock.patch("goal.cli.validate_repo_url", return_value=True):
            result = runner.invoke(main, ["clone", f"file://{bare}", target])
        assert result.exit_code == 0
        assert "cloned" in result.output.lower() or "✓" in result.output
        assert (tmp_path / "cloned" / ".git").exists()
