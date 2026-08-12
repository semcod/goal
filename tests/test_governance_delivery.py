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
        delivery.resolve_delivery_policy(config, "direct-main", all_flags=True)


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
        assert delivery.os.environ[
            delivery.CAPABILITY_ENV
        ] not in transaction.read_text(encoding="utf-8")


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
        assert delivery.authorize_hook_push(hook_policy, "origin", cwd=root) is True


def test_policy_payload_marks_server_enforcement_as_required():
    policy = delivery.resolve_delivery_policy(
        _config(default_mode="publish-only"), None, all_flags=True
    )

    payload = delivery.policy_payload(policy)

    assert payload["localHookIsSecurityBoundary"] is False
    assert payload["serverEnforcementRequired"] is True


def _ticket(root: Path, ticket: str, status: str) -> None:
    directory = root / "project" / ticket
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "README.md").write_text(
        f"# {ticket}\n\n- **Status**: {status}\n",
        encoding="utf-8",
    )


def test_pull_request_ticket_resolution_is_unique_and_explicit_wins(tmp_path):
    root = _repository(tmp_path)
    policy = _pull_request_policy()
    _ticket(root, "ticket-041", "DONE")
    _ticket(root, "ticket-056", "IN_PROGRESS")

    assert delivery.resolve_pull_request_ticket(policy, None, cwd=root) == "ticket-056"

    _ticket(root, "ticket-057", "IN_PROGRESS")
    assert (
        delivery.resolve_pull_request_ticket(policy, "ticket-056", cwd=root)
        == "ticket-056"
    )
    with pytest.raises(click.ClickException, match="explicit `--ticket`.*ticket-056, ticket-057"):
        delivery.resolve_pull_request_ticket(policy, None, cwd=root)


def test_pull_request_ticket_resolution_fails_closed_without_active_ticket(tmp_path):
    root = _repository(tmp_path)
    with pytest.raises(click.ClickException, match="none was found"):
        delivery.resolve_pull_request_ticket(_pull_request_policy(), None, cwd=root)


def test_delivery_event_is_outside_primary_and_linked_worktrees(tmp_path):
    root = _repository(tmp_path)
    linked = tmp_path / "linked"
    _git(root, "worktree", "add", "--detach", str(linked))
    policy = delivery.resolve_delivery_policy(
        _config(
            default_mode="direct-main",
            allowed_modes=["direct-main"],
            require_clean_governance=False,
        ),
        None,
        all_flags=True,
    )

    delivery.record_delivery_event(policy, "started", cwd=linked)

    audit = root / ".git" / "goal-delivery" / "delivery-events.jsonl"
    assert audit.is_file()
    assert json.loads(audit.read_text(encoding="utf-8"))["result"] == "started"
    assert not (root / ".governance" / "delivery-events.jsonl").exists()
    assert not (linked / ".governance" / "delivery-events.jsonl").exists()
    assert _git(root, "status", "--porcelain").stdout == ""
    assert _git(linked, "status", "--porcelain").stdout == ""


def test_delivery_runs_source_hub_health_before_target_wrapper(tmp_path, monkeypatch):
    root = tmp_path / "new-project"
    for relative in delivery.SOURCE_HUB_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    gate = root / "project" / "governance-check.sh"
    gate.parent.mkdir(parents=True)
    gate.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")

    monkeypatch.setattr(
        delivery,
        "_run",
        lambda *_args, **_kwargs: pytest.fail("target wrapper was executed"),
    )
    calls = []
    monkeypatch.setattr(
        delivery,
        "run_source_hub_health",
        lambda candidate: (
            calls.append(candidate)
            or delivery.SourceHubHealthResult(0, "GOV-HUB-PASS\n", "", 3)
        ),
    )

    delivery._governance_gate(root)

    assert calls == [root]


def test_delivery_surfaces_failed_source_hub_health(tmp_path, monkeypatch):
    root = tmp_path / "new-project"
    for relative in delivery.SOURCE_HUB_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        delivery,
        "run_source_hub_health",
        lambda _candidate: delivery.SourceHubHealthResult(
            9, "suite output\n", "GOV-HUB-001: failed\n", 1
        ),
    )

    with pytest.raises(click.ClickException, match="GOV-HUB-001: failed"):
        delivery._governance_gate(root)


def test_delivery_rejects_incomplete_adopted_package_before_wrapper(
    tmp_path, monkeypatch
):
    root = tmp_path / "target"
    gate = root / "project" / "governance-check.sh"
    gate.parent.mkdir(parents=True)
    gate.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    manifest = root / delivery.GOVERNANCE_PACKAGE_FILES["manifest"]
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        delivery,
        "_run",
        lambda *_args, **_kwargs: pytest.fail("incomplete wrapper was executed"),
    )

    with pytest.raises(click.ClickException, match="complete adopted package"):
        delivery._governance_gate(root)


def test_delivery_failure_surfaces_v2_remediation_and_safe_runbook(
    tmp_path, monkeypatch
):
    root = tmp_path / "target"
    for relative in delivery.GOVERNANCE_PACKAGE_FILES.values():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    gate = root / "project" / "governance-check.sh"
    gate.parent.mkdir(parents=True)
    gate.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    catalog = root / delivery.GOVERNANCE_DIAGNOSTICS
    catalog.write_text(
        json.dumps(
            {
                "schema": "new-project.diagnostics/v2",
                "codes": {
                    "GOV-TICKET-001": {
                        "message": "Ticket is missing.",
                        "remediation": "Create exactly one bounded ticket.",
                        "documentation": "error/GOV-TICKET-001.md",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    runbook = root / ".governance" / "error" / "GOV-TICKET-001.md"
    runbook.parent.mkdir()
    runbook.write_text("# Runbook\n", encoding="utf-8")
    monkeypatch.setattr(
        delivery,
        "_run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 1, "GOV-TICKET-001: failed\n", "validator detail\n"
        ),
    )

    with pytest.raises(click.ClickException) as error:
        delivery._governance_gate(root)

    assert "canonical remediation for GOV-TICKET-001" in error.value.message
    assert "Create exactly one bounded ticket." in error.value.message
    assert "runbook for GOV-TICKET-001: .governance/error/GOV-TICKET-001.md" in (
        error.value.message
    )


def test_diagnostic_guidance_rejects_escaping_runbook(tmp_path):
    root = tmp_path / "target"
    catalog = root / delivery.GOVERNANCE_DIAGNOSTICS
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "schema": "new-project.diagnostics/v2",
                "codes": {
                    "GOV-PATH-001": {
                        "message": "Unsafe path.",
                        "remediation": "Keep paths relative.",
                        "documentation": "../outside.md",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "outside.md").write_text("not a managed runbook\n", encoding="utf-8")

    guidance = delivery.governance_diagnostic_guidance(root, "GOV-PATH-001: failed")

    assert guidance == ["canonical remediation for GOV-PATH-001: Keep paths relative."]


def test_diagnostic_guidance_preserves_v1_message_only_catalog(tmp_path):
    root = tmp_path / "target"
    catalog = root / delivery.GOVERNANCE_DIAGNOSTICS
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "schema": "new-project.diagnostics/v1",
                "codes": {"GOV-TICKET-001": "Ticket is missing."},
            }
        ),
        encoding="utf-8",
    )

    assert delivery.governance_diagnostic_guidance(root, "GOV-TICKET-001: failed") == []


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


def _commit_ticket_change(
    root: Path, message: str, content: str = "candidate\n"
) -> str:
    (root / "candidate.txt").write_text(content, encoding="utf-8")
    _git(root, "add", "candidate.txt")
    _git(root, "commit", "--quiet", "-m", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def test_pending_pr_delivery_accepts_clean_ticket_bound_ahead_range(tmp_path):
    root = _publish_repository(tmp_path)
    base_sha = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "switch", "-c", "ticket/049-resume")
    head_sha = _commit_ticket_change(
        root, "[ticket-049] fix(delivery): preserve committed candidate"
    )

    policy = _pull_request_policy()
    candidate = delivery.pending_pull_request_delivery(
        policy, ticket="ticket-049", cwd=root
    )

    assert candidate == delivery.PendingPullRequestDelivery(
        base_sha=base_sha,
        head_sha=head_sha,
        title="[ticket-049] fix(delivery): preserve committed candidate",
        files=("candidate.txt",),
    )
    delivery.record_delivery_event(policy, "started", cwd=root)
    assert (
        delivery.pending_pull_request_delivery(
            policy, ticket="ticket-049", cwd=root
        )
        == candidate
    )


def test_pending_pr_delivery_rejects_unbound_ahead_commit(tmp_path):
    root = _publish_repository(tmp_path)
    _git(root, "switch", "-c", "ticket/049-resume")
    _commit_ticket_change(root, "fix: unrelated candidate")

    with pytest.raises(click.ClickException, match="not bound to ticket-049"):
        delivery.pending_pull_request_delivery(
            _pull_request_policy(), ticket="ticket-049", cwd=root
        )


def test_pending_pr_delivery_ignores_dirty_equal_and_merged_histories(tmp_path):
    root = _publish_repository(tmp_path)
    policy = _pull_request_policy()

    assert (
        delivery.pending_pull_request_delivery(policy, ticket="ticket-049", cwd=root)
        is None
    )

    (root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    assert (
        delivery.pending_pull_request_delivery(policy, ticket="ticket-049", cwd=root)
        is None
    )
    (root / "dirty.txt").unlink()

    base_sha = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "switch", "-c", "ticket/049-resume")
    _commit_ticket_change(root, "[ticket-049] fix(delivery): merged candidate")
    _git(root, "push", "--quiet", "origin", "HEAD:main")
    _git(root, "checkout", "--quiet", "--detach", base_sha)

    assert (
        delivery.pending_pull_request_delivery(policy, ticket="ticket-049", cwd=root)
        is None
    )


def test_pending_pr_delivery_fails_closed_on_divergent_remote_base(tmp_path):
    root = _publish_repository(tmp_path)
    _git(root, "switch", "-c", "ticket/049-resume")
    _commit_ticket_change(root, "[ticket-049] fix(delivery): local candidate")
    _git(root, "switch", "main")
    _commit_ticket_change(
        root,
        "[ticket-049] fix(delivery): conflicting base",
        content="remote\n",
    )
    _git(root, "push", "--quiet", "origin", "main")
    _git(root, "switch", "ticket/049-resume")

    with pytest.raises(click.ClickException, match="history divergent"):
        delivery.pending_pull_request_delivery(
            _pull_request_policy(), ticket="ticket-049", cwd=root
        )


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


def test_pull_request_push_preserves_colliding_local_branch(tmp_path, monkeypatch):
    """Canonical remote publication must not create or rewrite a local alias."""
    root = _repository(tmp_path)
    canonical = "goal/ticket-055"
    stale_sha = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "branch", canonical)
    _git(root, "switch", "-c", "ticket/055-close")
    expected_head = _commit_ticket_change(
        root, "[ticket-055] close governed delivery evidence"
    )
    original_run = delivery._run
    calls = []

    def fake_run(arguments, *, cwd=None):
        calls.append(arguments)
        if arguments[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:3] == ["gh", "pr", "list"]:
            payload = [
                {
                    "url": "https://github.com/example/repo/pull/55",
                    "headRefOid": expected_head,
                }
            ]
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")
        return original_run(arguments, cwd=cwd)

    monkeypatch.setattr(delivery, "_run", fake_run)

    resolved_head, url = delivery.deliver_pull_request(
        _pull_request_policy(),
        ticket="ticket-055",
        title="[ticket-055] close governed delivery evidence",
        cwd=root,
    )

    assert resolved_head == canonical
    assert url == "https://github.com/example/repo/pull/55"
    assert _git(root, "branch", "--show-current").stdout.strip() == "ticket/055-close"
    assert _git(root, "rev-parse", canonical).stdout.strip() == stale_sha
    push = next(call for call in calls if call[:2] == ["git", "push"])
    assert push == [
        "git",
        "push",
        "-u",
        "origin",
        "HEAD:refs/heads/goal/ticket-055",
    ]
    assert "--force" not in push
    assert not any(call[:2] == ["git", "switch"] for call in calls)


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


def test_open_pr_stale_head_is_retried_until_current_pushed_head(tmp_path, monkeypatch):
    root = _repository(tmp_path)
    head = "goal/ticket-044"
    _git(root, "switch", "-c", head)
    expected_head = _git(root, "rev-parse", "HEAD").stdout.strip()
    original_run = delivery._run
    open_queries = 0
    sleeps = []

    def fake_run(arguments, *, cwd=None):
        nonlocal open_queries
        if arguments[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:3] == ["gh", "pr", "list"]:
            open_queries += 1
            payload = [
                {
                    "url": "https://github.com/example/repo/pull/44",
                    "headRefOid": "0" * 40 if open_queries == 1 else expected_head,
                }
            ]
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")
        return original_run(arguments, cwd=cwd)

    monkeypatch.setattr(delivery, "_run", fake_run)
    monkeypatch.setattr(delivery.time, "sleep", sleeps.append)

    _, url = delivery.deliver_pull_request(
        _pull_request_policy(),
        ticket="ticket-044",
        title="fix: retry stale PR head",
        cwd=root,
    )

    assert url == "https://github.com/example/repo/pull/44"
    assert open_queries == 2
    assert sleeps == [delivery.PULL_REQUEST_HEAD_RETRY_SECONDS]


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

    sleeps = []
    monkeypatch.setattr(delivery, "_run", fake_run)
    monkeypatch.setattr(delivery.time, "sleep", sleeps.append)

    with pytest.raises(click.ClickException, match="not current pushed HEAD"):
        delivery.deliver_pull_request(
            _pull_request_policy(),
            ticket="ticket-027",
            title="fix: bind open PR",
            cwd=root,
        )

    assert sleeps == [delivery.PULL_REQUEST_HEAD_RETRY_SECONDS] * (
        delivery.PULL_REQUEST_HEAD_ATTEMPTS - 1
    )
