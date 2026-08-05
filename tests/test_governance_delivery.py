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


def test_policy_payload_marks_server_enforcement_as_required():
    policy = delivery.resolve_delivery_policy(
        _config(default_mode="publish-only"), None, all_flags=True
    )

    payload = delivery.policy_payload(policy)

    assert payload["localHookIsSecurityBoundary"] is False
    assert payload["serverEnforcementRequired"] is True
