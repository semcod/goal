"""Recovery must never destroy uncommitted work.

Field incident (semcod/koru, 2026-07-03): a concurrent agent's uncommitted
file rewrite vanished while goal automation ran. The recovery flows were the
only code paths issuing bare ``git reset --hard``. They now auto-stash dirty
work (including untracked files) before any hard reset and restore it after;
when the stash cannot be re-applied cleanly it stays in ``git stash list``.
"""

import subprocess
from pathlib import Path

import pytest

from goal.recovery.manager import RecoveryManager


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "tracked.txt").write_text("v1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "v1")
    return repo


def _manager(repo: Path) -> RecoveryManager:
    return RecoveryManager(str(repo))


class TestResetHardPreservingWork:
    def test_clean_tree_resets_without_stash(self, repo: Path):
        (repo / "tracked.txt").write_text("v2\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "v2")

        _manager(repo)._reset_hard_preserving_work("HEAD~1", label="test")

        assert (repo / "tracked.txt").read_text() == "v1\n"
        stashes = _git(repo, "stash", "list").stdout
        assert stashes.strip() == ""

    def test_dirty_tracked_change_survives_reset(self, repo: Path):
        (repo / "other.txt").write_text("concurrent agent work\n")
        _git(repo, "add", "other.txt")
        _git(repo, "commit", "-m", "base for other")
        (repo / "other.txt").write_text("uncommitted rewrite\n")

        _manager(repo)._reset_hard_preserving_work("HEAD", label="test")

        assert (repo / "other.txt").read_text() == "uncommitted rewrite\n"

    def test_untracked_file_survives_reset(self, repo: Path):
        (repo / "new_module.py").write_text("print('wip')\n")

        _manager(repo)._reset_hard_preserving_work("HEAD", label="test")

        assert (repo / "new_module.py").read_text() == "print('wip')\n"

    def test_conflicting_work_stays_in_stash(self, repo: Path):
        # Reset target changes the same file the dirty tree modified: the
        # stash pop conflicts, so the work must remain recoverable via stash.
        (repo / "tracked.txt").write_text("v2\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "v2")
        (repo / "tracked.txt").write_text("uncommitted v3\n")

        _manager(repo)._reset_hard_preserving_work("HEAD~1", label="test")

        stashes = _git(repo, "stash", "list").stdout
        content = (repo / "tracked.txt").read_text()
        work_in_tree = "uncommitted v3" in content
        work_in_stash = "goal-recovery-autostash-test" in stashes
        assert work_in_tree or work_in_stash, (
            f"work lost: tree={content!r} stashes={stashes!r}"
        )
