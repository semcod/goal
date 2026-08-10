"""Contract tests for governed delivery policy and local hook handling."""

import json
from pathlib import Path
import subprocess

import click
import pytest

from goal.governance import delivery


def _config(**delivery_values):
    return {"governance": {"delivery": delivery_values}}


def _git(root: Path, *arguments: str):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "goal-delivery@example.invalid")
    _git(root, "config", "user.name", "goal-delivery-test")
    (root / "README.md").write_text("test\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "--quiet", "-m", "initial")
    return root


def test_absent_policy_preserves_legacy_behavior():
    assert delivery.resolve_delivery_policy({}, None, all_flags=False) is None


def test_policy_requires_goal_all_and_rejects_disallowed_mode():
    config = _config(
        require_goal_a=True,
        default_mode="pull-request",
        allowed_modes=["pull-request"],
    )
    with pytest.raises(click.ClickException, match="goal -a"):
        delivery.resolve_delivery_policy(config, None, all_flags=False)
    with pytest.raises(click.ClickException, match="forbidden"):
        delivery.resolve_delivery_policy(
            config, "direct-main", all_flags=True
        )


def test_install_and_remove_preserve_project_hook(tmp_path):
    root = _repository(tmp_path)
    hook = root / ".git" / "hooks" / "pre-push"
    hook.write_text("#!/bin/sh\necho project-hook\n", encoding="utf-8")

    installed = delivery.install_delivery_hook(cwd=root)

    assert delivery.check_delivery_hook(cwd=root) is True
    assert "echo project-hook" in installed.read_text(encoding="utf-8")
    delivery.remove_delivery_hook(cwd=root)
    remaining = hook.read_text(encoding="utf-8")
    assert "echo project-hook" in remaining
    assert delivery.HOOK_START not in remaining


def test_raw_environment_flag_is_not_authorization(tmp_path, monkeypatch):
    root = _repository(tmp_path)
    policy = delivery.resolve_delivery_policy(
        _config(
            require_goal_a=True,
            default_mode="direct-main",
            allowed_modes=["direct-main"],
            require_clean_governance=False,
        ),
        None,
        all_flags=True,
    )
    monkeypatch.setenv(delivery.CAPABILITY_ENV, "invented")
    monkeypatch.delenv(delivery.TRANSACTION_ENV, raising=False)

    with pytest.raises(click.ClickException, match="raw git push"):
        delivery.authorize_hook_push(policy, "origin", cwd=root)


def test_file_backed_transaction_authorizes_matching_remote(tmp_path):
    root = _repository(tmp_path)
    policy = delivery.resolve_delivery_policy(
        _config(
            default_mode="direct-main",
            allowed_modes=["direct-main"],
            require_clean_governance=False,
        ),
        None,
        all_flags=True,
    )

    with delivery.authorized_push(policy, cwd=root):
        assert delivery.authorize_hook_push(policy, "origin", cwd=root) is True
        transaction = Path(delivery.os.environ[delivery.TRANSACTION_ENV])
        payload = json.loads(transaction.read_text(encoding="utf-8"))
        assert "tokenHash" in payload
        assert delivery.os.environ[delivery.CAPABILITY_ENV] not in transaction.read_text(
            encoding="utf-8"
        )


def test_hook_accepts_an_explicit_allowed_mode_when_default_differs(tmp_path):
    root = _repository(tmp_path)
    config = _config(
        default_mode="pull-request",
        allowed_modes=["pull-request", "direct-main"],
        require_clean_governance=False,
    )
    hook_policy = delivery.resolve_delivery_policy(config, None, all_flags=True)
    direct_policy = delivery.resolve_delivery_policy(
        config, "direct-main", all_flags=True
    )

    with delivery.authorized_push(direct_policy, cwd=root):
        assert delivery.authorize_hook_push(
            hook_policy, "origin", cwd=root
        ) is True


def test_policy_payload_marks_server_enforcement_as_required():
    policy = delivery.resolve_delivery_policy(
        _config(default_mode="publish-only"), None, all_flags=True
    )

    payload = delivery.policy_payload(policy)

    assert payload["localHookIsSecurityBoundary"] is False
    assert payload["serverEnforcementRequired"] is True


def _pull_request_policy():
    return delivery.resolve_delivery_policy(
        _config(
            default_mode="pull-request",
            allowed_modes=["pull-request"],
            require_clean_governance=False,
        ),
        None,
        all_flags=True,
    )


def _publish_only_policy():
    return delivery.resolve_delivery_policy(
        _config(
            default_mode="publish-only",
            allowed_modes=["publish-only"],
            require_clean_governance=False,
            remote="origin",
            base_branch="main",
        ),
        None,
        all_flags=True,
    )


def _publish_repository(tmp_path: Path) -> Path:
    root = _repository(tmp_path)
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "--quiet", str(remote))
    _git(root, "branch", "-M", "main")
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "--quiet", "-u", "origin", "main")
    return root


def test_publish_only_requires_clean_exact_remote_base(tmp_path):
    root = _publish_repository(tmp_path)

    delivery.validate_delivery_ready(_publish_only_policy(), cwd=root)

    (root / "README.md").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(click.ClickException, match="clean working tree"):
        delivery.validate_delivery_ready(_publish_only_policy(), cwd=root)


def test_publish_only_rejects_clean_local_commit_ahead_of_remote(tmp_path):
    root = _publish_repository(tmp_path)
    (root / "README.md").write_text("local-only\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "--quiet", "-m", "local-only")

    with pytest.raises(click.ClickException, match="authoritative remote base"):
        delivery.validate_delivery_ready(_publish_only_policy(), cwd=root)


def test_merged_branch_pr_is_not_reused_for_a_new_delivery(tmp_path, monkeypatch):
    root = _repository(tmp_path)
    head = "goal/ticket-027"
    _git(root, "switch", "-c", head)
    expected_head = _git(root, "rev-parse", "HEAD").stdout.strip()
    original_run = delivery._run
    calls = []
    open_queries = 0

    def fake_run(arguments, *, cwd=None):
        nonlocal open_queries
        calls.append(arguments)
        if arguments[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:3] == ["gh", "pr", "list"]:
            open_queries += 1
            # The first open-only query excludes the historical merged PR.
            payload = (
                []
                if open_queries == 1
                else [
                    {
                        "url": "https://github.com/example/repo/pull/29",
                        "headRefOid": expected_head,
                    }
                ]
            )
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")
        if arguments[:3] == ["gh", "pr", "create"]:
            return subprocess.CompletedProcess(
                arguments, 0, "https://github.com/example/repo/pull/29\n", ""
            )
        return original_run(arguments, cwd=cwd)

    monkeypatch.setattr(delivery, "_run", fake_run)

    resolved_head, url = delivery.deliver_pull_request(
        _pull_request_policy(),
        ticket="ticket-027",
        title="fix: bind open PR",
        cwd=root,
    )

    assert resolved_head == head
    assert url == "https://github.com/example/repo/pull/29"
    assert open_queries == 2
    assert any(call[:3] == ["gh", "pr", "create"] for call in calls)
    first_query = next(call for call in calls if call[:3] == ["gh", "pr", "list"])
    assert first_query[first_query.index("--state") + 1] == "open"
    assert first_query[first_query.index("--base") + 1] == "main"
    assert first_query[first_query.index("--head") + 1] == head


def test_open_pr_is_reused_only_at_current_pushed_head(tmp_path, monkeypatch):
    root = _repository(tmp_path)
    head = "goal/ticket-027"
    _git(root, "switch", "-c", head)
    expected_head = _git(root, "rev-parse", "HEAD").stdout.strip()
    original_run = delivery._run
    calls = []

    def fake_run(arguments, *, cwd=None):
        calls.append(arguments)
        if arguments[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:3] == ["gh", "pr", "list"]:
            payload = [
                {
                    "url": "https://github.com/example/repo/pull/30",
                    "headRefOid": expected_head,
                }
            ]
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")
        return original_run(arguments, cwd=cwd)

    monkeypatch.setattr(delivery, "_run", fake_run)

    _, url = delivery.deliver_pull_request(
        _pull_request_policy(),
        ticket="ticket-027",
        title="fix: bind open PR",
        cwd=root,
    )

    assert url == "https://github.com/example/repo/pull/30"
    assert not any(call[:3] == ["gh", "pr", "create"] for call in calls)


def test_open_pr_with_stale_head_fails_closed(tmp_path, monkeypatch):
    root = _repository(tmp_path)
    head = "goal/ticket-027"
    _git(root, "switch", "-c", head)
    original_run = delivery._run

    def fake_run(arguments, *, cwd=None):
        if arguments[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:3] == ["gh", "pr", "list"]:
            payload = [
                {
                    "url": "https://github.com/example/repo/pull/30",
                    "headRefOid": "0" * 40,
                }
            ]
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")
        return original_run(arguments, cwd=cwd)

    monkeypatch.setattr(delivery, "_run", fake_run)

    with pytest.raises(click.ClickException, match="not current pushed HEAD"):
        delivery.deliver_pull_request(
            _pull_request_policy(),
            ticket="ticket-027",
            title="fix: bind open PR",
            cwd=root,
        )
