"""Batch delegates the protected workflow and keeps caller effect boundaries."""

import json
import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner
import pytest

from goal.cli import all_cmd


def test_child_retains_repair_preview_and_publication_opt_out(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(all_cmd.subprocess, "run", lambda args, **kwargs: calls.append((args, kwargs)) or subprocess.CompletedProcess(args, 0))
    assert all_cmd._run_goal_a(str(tmp_path), True, {
        "koru": True, "no_publish": True, "delivery_mode": "pull-request",
        "version": "1.2.3", "config_path": "/explicit/goal.yaml",
    }) == 0
    command, options = calls[0]
    assert command[:5] == [sys.executable, "-I", "-m", "goal", "-a"]
    assert "-k" in command and "--dry-run" in command and "--no-publish" in command
    assert command[command.index("--delivery-mode") + 1] == "pull-request"
    assert command[command.index("--target-version") + 1] == "1.2.3"
    assert command[command.index("--config") + 1] == "/explicit/goal.yaml"
    assert "--force-publish" not in command
    assert options == {"cwd": str(tmp_path)}


def test_child_failure_propagates(monkeypatch, tmp_path):
    monkeypatch.setattr(all_cmd.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 17))
    assert all_cmd._run_goal_a(str(tmp_path), False) == 17


@pytest.mark.parametrize("kind", ["ready", "unknown", "untrusted", "malformed", "failed"])
def test_only_successful_typed_readiness_is_selected(monkeypatch, kind):
    plan = {"schema": "goal.release-plan/v1", "ready_for_goal": kind in {"ready", "untrusted"},
            "authorization_granted": kind == "untrusted"}
    output = "not json" if kind == "malformed" else json.dumps(plan)
    calls = []
    def invoke(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 2 if kind == "failed" else 0, output, "")
    monkeypatch.setattr(all_cmd.subprocess, "run", invoke)
    assert all_cmd._pending_release("project", "/specific.yaml") is (kind == "ready")
    assert calls[0][0][:4] == [sys.executable, "-I", "-m", "goal.publish.state"]
    assert calls[0][0][-2:] == ["--project-config", "/specific.yaml"]


def test_batch_includes_clean_pending_releases_and_preserves_no_publish(monkeypatch):
    monkeypatch.setattr(all_cmd, "_classify_targets", lambda paths: (["dirty"], ["ready", "idle"], []))
    queried, executed = [], []
    monkeypatch.setattr(all_cmd, "_pending_release", lambda path, config: queried.append(path) or path == "ready")
    monkeypatch.setattr(all_cmd, "_run_goal_a", lambda path, preview, options: executed.append((path, preview, options)) or 0)
    monkeypatch.setattr(all_cmd, "_explicit_yes", lambda: True)
    runner = CliRunner()
    result = runner.invoke(all_cmd.all_, ["workspace"], obj={"koru": True, "dry_run": True})
    assert result.exit_code == 0, result.output
    assert [row[0] for row in executed] == ["dirty", "ready"]
    assert all(row[1] and row[2]["koru"] for row in executed)
    executed.clear()
    queried.clear()
    result = runner.invoke(all_cmd.all_, ["workspace"], obj={"no_publish": True})
    assert result.exit_code == 0, result.output
    assert [row[0] for row in executed] == ["dirty"] and not queried
    assert executed[0][2]["no_publish"] is True


def test_batch_reports_failure_and_does_not_claim_publication(monkeypatch):
    monkeypatch.setattr(all_cmd, "_classify_targets", lambda paths: (["one", "two"], [], []))
    monkeypatch.setattr(all_cmd, "_run_goal_a", lambda path, *args: 0 if path == "one" else 9)
    monkeypatch.setattr(all_cmd, "_explicit_yes", lambda: True)
    result = CliRunner().invoke(all_cmd.all_, ["workspace"], obj={})
    assert result.exit_code == 1
    assert "1 failed" in result.output
    assert "published" not in result.output.lower()


def test_registered_linked_worktree_is_a_repository_and_aliases_are_deduplicated(tmp_path):
    primary = tmp_path / "primary"
    primary.mkdir()
    def git(*args):
        subprocess.run(["git", "-C", str(primary), *args], check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    (primary / "file").write_text("fixture")
    git("add", ".")
    git("commit", "-qm", "fixture")
    linked = tmp_path / "linked"
    git("worktree", "add", "--detach", str(linked))
    assert (linked / ".git").is_file() and all_cmd._is_git_repo(str(linked))
    alias = tmp_path / "alias"
    alias.symlink_to(linked, target_is_directory=True)
    assert len(all_cmd._expand_targets([str(linked), str(alias)])) == 1
    assert not all_cmd._is_git_repo(str(linked / "not-a-root"))
