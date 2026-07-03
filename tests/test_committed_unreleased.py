"""Tests for committed-but-unreleased source detection (goal -a skip bug).

Three times in one day `goal -a` skipped a release because the feature
commits were already in git: staged-file analysis saw a clean tree while
the registry stayed behind HEAD (tillm providers, planfile fastio, pfix).
"""

from __future__ import annotations

import subprocess

import pytest

from goal.publish.changes import (
    _latest_release_tag,
    committed_unreleased_source_files,
)


@pytest.fixture()
def git_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "config", "user.name", "t"], check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "pkg.py").write_text("x = 1\n")
    (tmp_path / "README.md").write_text("readme\n")
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-qm", "init"], check=True)
    subprocess.run(["git", "tag", "v1.0.0"], check=True)
    return tmp_path


def _commit(tmp_path, relpath, content, msg):
    path = tmp_path / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-qm", msg], check=True)


class TestCommittedUnreleased:
    def test_source_commit_after_tag_is_detected(self, git_repo):
        _commit(git_repo, "src/pkg.py", "x = 2\n", "feat: change source")
        pending = committed_unreleased_source_files(["python"])
        assert pending == ["src/pkg.py"]

    def test_docs_only_commits_do_not_trigger_release(self, git_repo):
        _commit(git_repo, "README.md", "readme v2\n", "docs: update")
        assert committed_unreleased_source_files(["python"]) == []

    def test_clean_head_at_tag_reports_nothing(self, git_repo):
        assert committed_unreleased_source_files(["python"]) == []

    def test_no_release_tag_reports_nothing(self, git_repo):
        subprocess.run(["git", "tag", "-d", "v1.0.0"], check=True)
        _commit(git_repo, "src/pkg.py", "x = 3\n", "feat: change")
        assert committed_unreleased_source_files(["python"]) == []

    def test_non_registry_project_reports_nothing(self, git_repo):
        _commit(git_repo, "src/pkg.py", "x = 4\n", "feat: change")
        assert committed_unreleased_source_files(["docs"]) == []

    def test_latest_release_tag_resolution(self, git_repo):
        assert _latest_release_tag() == "v1.0.0"
        _commit(git_repo, "src/pkg.py", "x = 5\n", "feat")
        subprocess.run(["git", "tag", "v1.1.0"], check=True)
        assert _latest_release_tag() == "v1.1.0"
