"""Contract tests for governed delivery policy and local hook handling."""

import json
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys

import click
import pytest

from goal.governance import delivery


def test_pr_preflight_supplies_real_base_to_unchanged_gate(tmp_path, monkeypatch):
    root = _publish_repository(tmp_path)
    base = _git(root, "rev-parse", "HEAD").stdout.strip()
    for relative in delivery.GOVERNANCE_PACKAGE_FILES.values():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    gate = root / "project/governance-check.sh"
    gate.parent.mkdir(parents=True)
    gate.write_text(
        '#!/bin/sh\n[ "$#" = 2 ] && [ "$1" = --base ] && '
        f'[ "$2" = "{base}" ] || exit 17\n', encoding="utf-8"
    )
    gate.chmod(0o755)
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "candidate after adoption")
    original_run = delivery._run
    def run(arguments, **kwargs):
        if arguments == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        return original_run(arguments, **kwargs)
    monkeypatch.setattr(delivery, "_run", run)
    monkeypatch.setattr(delivery.shutil, "which", lambda command: "/usr/bin/gh")
    policy = replace(_pull_request_policy(), require_clean_governance=True)
    before = _git(root, "status", "--porcelain").stdout
    delivery.validate_delivery_ready(policy, cwd=root)
    assert _git(root, "status", "--porcelain").stdout == before


def test_pr_preflight_ignores_stale_tracking_ref_and_uses_configured_remote(tmp_path):
    root = _publish_repository(tmp_path)
    stale = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "remote", "rename", "origin", "upstream")
    (root / "README.md").write_text("advanced target\n", encoding="utf-8")
    _git(root, "commit", "--quiet", "-am", "target advance")
    current = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "push", "--quiet", "upstream", "HEAD:release")
    _git(root, "update-ref", "refs/remotes/upstream/release", stale)
    policy = replace(_pull_request_policy(), remote="upstream", base_branch="release")
    assert delivery._pull_request_validation_base(policy, root) == current
    assert _git(root, "rev-parse", "upstream/release").stdout.strip() == stale


@pytest.mark.parametrize("output", ["", "invalid\trefs/heads/main\n", "a" * 40 + "\trefs/heads/other\n", ("a" * 40 + "\trefs/heads/main\n") * 2])
def test_pr_preflight_rejects_invalid_remote_observation(tmp_path, monkeypatch, output):
    root = _repository(tmp_path)
    monkeypatch.setattr(delivery, "_run", lambda args, **kwargs: subprocess.CompletedProcess(args, 0, output, ""))
    with pytest.raises(click.ClickException, match="exactly one authoritative"):
        delivery._pull_request_validation_base(_pull_request_policy(), root)


def test_pr_preflight_does_not_fall_back_when_remote_is_unavailable(tmp_path):
    root = _publish_repository(tmp_path)
    _git(root, "remote", "set-url", "origin", str(tmp_path / "missing-remote"))
    with pytest.raises(click.ClickException, match="exactly one authoritative"):
        delivery._pull_request_validation_base(_pull_request_policy(), root)


def test_pr_preflight_requires_observed_commit_to_exist_locally(tmp_path, monkeypatch):
    root = _repository(tmp_path)
    original_run = delivery._run
    def run(arguments, **kwargs):
        if arguments[:2] == ["git", "ls-remote"]:
            return subprocess.CompletedProcess(arguments, 0, "a" * 40 + "\trefs/heads/main\n", "")
        return original_run(arguments, **kwargs)
    monkeypatch.setattr(delivery, "_run", run)
    with pytest.raises(click.ClickException, match="fetch origin/main"):
        delivery._pull_request_validation_base(_pull_request_policy(), root)


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


def test_pending_pr_delivery_accepts_conventional_commit_ticket_scope(tmp_path):
    root = _publish_repository(tmp_path)
    _git(root, "switch", "-c", "ticket/049-resume")
    head_sha = _commit_ticket_change(
        root, "build(ticket-049): remove pfix auto-repair configuration"
    )

    candidate = delivery.pending_pull_request_delivery(
        _pull_request_policy(), ticket="ticket-049", cwd=root
    )

    assert candidate is not None
    assert candidate.head_sha == head_sha
    assert candidate.title == "build(ticket-049): remove pfix auto-repair configuration"


@pytest.mark.parametrize(
    ("subject", "bound"),
    [
        ("[ticket-049] fix(delivery): keep candidate", True),
        ("fix(ticket-049): keep candidate", True),
        ("fix(delivery, ticket-049)!: keep candidate", True),
        ("fix(ticket-049, delivery): keep candidate", True),
        ("fix(ticket-049, ticket-049): same ticket identity", True),
        ("fix(ticket-049, ticket-05): another numeric ticket", False),
        ("fix(ticket-0491): keep candidate", False),
        ("fix(delivery): ticket-049 keep candidate", False),
        ("[ticket-0491] fix: keep candidate", False),
        ("fix(ticket-049):keep candidate", False),
    ],
)
def test_subject_binds_ticket_forms(subject, bound):
    assert delivery.subject_binds_ticket(subject, "ticket-049") is bound


@pytest.mark.parametrize("ticket", ["ticket-049", "ticket-050"])
@pytest.mark.parametrize(
    "scope",
    [
        "ticket-049, ticket-050",
        "ticket-050, ticket-049",
        "delivery, ticket-049, ticket-050",
        "ticket-049, ticket-049, ticket-050",
    ],
)
def test_subject_binds_ticket_rejects_multiple_ticket_identities(scope, ticket):
    subject = f"fix({scope}): ambiguous ownership"
    assert delivery.subject_binds_ticket(subject, ticket) is False


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
    alias = "goal/ticket-055"
    canonical = "ticket/055-close"
    stale_sha = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "branch", alias)
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
            payload = [] if arguments[arguments.index("--head") + 1] == alias else [
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
    assert _git(root, "rev-parse", alias).stdout.strip() == stale_sha
    push = next(call for call in calls if call[:2] == ["git", "push"])
    assert push == [
        "git",
        "push",
        "-u",
        "origin",
        "HEAD:refs/heads/ticket/055-close",
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


@pytest.mark.parametrize("branch,ticket", [
    ("ticket/102-canonical-pr-branch", "ticket-102"),
    ("ticket/1234-canonical-pr-branch", "ticket-1234"),
])
def test_pr_head_preserves_canonical_ticket_branch(tmp_path, branch, ticket):
    root = _repository(tmp_path)
    _git(root, "switch", "-c", branch)
    assert delivery._pr_head(ticket, root) == branch


@pytest.mark.parametrize("branch,ticket", [
    ("ticket/102-canonical-pr-branch", "ticket-103"),
    ("ticket/102-canonical-pr-branch", None),
    ("ticket/102-invalid_slug", "ticket-102"),
    ("ticket/102", "ticket-102"),
])
def test_pr_head_rejects_invalid_ticket_binding(tmp_path, branch, ticket):
    root = _repository(tmp_path)
    _git(root, "switch", "-c", branch)
    with pytest.raises(click.ClickException, match="ticket"):
        delivery._pr_head(ticket, root)


@pytest.mark.parametrize("branch", ["main", "feature/legacy", None])
def test_pr_head_keeps_legacy_and_detached_mapping(tmp_path, branch):
    root = _repository(tmp_path)
    if branch is None:
        _git(root, "checkout", "--detach")
    elif branch != "main":
        _git(root, "switch", "-c", branch)
    assert delivery._pr_head("ticket-102", root) == "goal/ticket-102"


@pytest.mark.parametrize("existing", ["none", "canonical", "legacy", "both", "failure", "invalid"])
def test_canonical_publication_observes_existing_prs_before_push(tmp_path, monkeypatch, existing):
    root = _repository(tmp_path)
    canonical, legacy = "ticket/102-canonical-pr-branch", "goal/ticket-102"
    _git(root, "switch", "-c", canonical)
    expected = _git(root, "rev-parse", "HEAD").stdout.strip()
    calls, created = [], False
    original_run = delivery._run

    def run(arguments, *, cwd=None):
        nonlocal created
        calls.append(arguments)
        if arguments[:2] == ["git", "push"]:
            return subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments[:3] == ["gh", "pr", "list"]:
            if existing == "failure":
                return subprocess.CompletedProcess(arguments, 1, "", "API unavailable")
            if existing == "invalid":
                return subprocess.CompletedProcess(arguments, 0, "{}", "")
            head = arguments[arguments.index("--head") + 1]
            present = (existing == "both" or (existing == "legacy" and head == legacy)
                       or (existing == "canonical" and head == canonical) or created)
            pushed = any(c[:2] == ["git", "push"] for c in calls)
            payload = [{"url": "https://github.com/example/repo/pull/102",
                        "headRefOid": expected if pushed else "a" * 40}] if present else []
            return subprocess.CompletedProcess(arguments, 0, json.dumps(payload), "")
        if arguments[:3] == ["gh", "pr", "create"]:
            created = True
            return subprocess.CompletedProcess(arguments, 0, "created", "")
        return original_run(arguments, cwd=cwd)

    monkeypatch.setattr(delivery, "_run", run)
    if existing in {"both", "failure", "invalid"}:
        with pytest.raises(click.ClickException):
            delivery.deliver_pull_request(_pull_request_policy(), ticket="ticket-102", title="bound", cwd=root)
        assert not any(c[:2] == ["git", "push"] or c[:3] == ["gh", "pr", "create"] for c in calls)
        return
    head, url = delivery.deliver_pull_request(_pull_request_policy(), ticket="ticket-102", title="bound", cwd=root)
    expected_branch = legacy if existing == "legacy" else canonical
    assert head == expected_branch
    assert url.endswith("/102")
    push_index = next(i for i, c in enumerate(calls) if c[:2] == ["git", "push"])
    assert calls[push_index][-1] == "HEAD:refs/heads/" + expected_branch
    queries = [c[c.index("--head") + 1] for c in calls[:push_index] if c[:3] == ["gh", "pr", "list"]]
    assert queries == [canonical, legacy]
    assert created == (existing == "none")
    assert _git(root, "branch", "--show-current").stdout.strip() == canonical


def _clone_with_governed_ticket_worktree(tmp_path: Path) -> Path:
    """Default checkout without governance; its ticket worktree carries the adoption."""
    root = _publish_repository(tmp_path)
    (root / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
    _git(root, "add", ".gitignore")
    _git(root, "commit", "--quiet", "-m", "ignore worktrees")
    _git(root, "push", "--quiet", "origin", "main")
    ticket = root / ".worktrees" / "ticket-001--adoption"
    _git(root, "worktree", "add", "--quiet", "-b", "ticket/001-adoption", str(ticket))
    manifest = ticket / delivery.GOVERNANCE_PACKAGE_FILES["manifest"]
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}\n", encoding="utf-8")
    return root


def test_default_checkout_of_governed_clone_refuses_legacy_delivery(tmp_path, monkeypatch):
    root = _clone_with_governed_ticket_worktree(tmp_path)
    monkeypatch.setattr(delivery, "_governance_gate",
                        lambda *args, **kwargs: pytest.fail("no gate exists in this checkout"))
    with pytest.raises(click.ClickException, match=delivery.GOVERNED_CLONE_DIAGNOSTIC) as error:
        delivery.validate_legacy_governance(cwd=root)
    assert "ticket-001--adoption" in str(error.value)


def test_primary_worktree_lease_marks_clone_governed(tmp_path):
    root = _publish_repository(tmp_path)
    lease = root / ".subactor" / "leases" / "ticket-002--work.json"
    lease.parent.mkdir(parents=True)
    lease.write_text("{}\n", encoding="utf-8")
    with pytest.raises(click.ClickException, match=delivery.GOVERNED_CLONE_DIAGNOSTIC):
        delivery.validate_legacy_governance(cwd=root)


def test_linked_worktree_without_governance_keeps_legacy_flow(tmp_path):
    root = _publish_repository(tmp_path)
    _git(root, "worktree", "add", "--quiet", "-b", "feature", str(tmp_path / "feature"))
    assert delivery.governed_clone_evidence(root) == []
    assert delivery.validate_legacy_governance(cwd=root) is False


def test_goal_all_in_default_checkout_neither_rewrites_config_nor_pushes_main(tmp_path):
    root = _clone_with_governed_ticket_worktree(tmp_path)
    # A generated config naming a version file that exists only in a ticket
    # worktree: auto-detection used to prune it, commit and push it to main.
    config = root / "goal.yaml"
    config.write_text(
        "version: '1.0'\nproject:\n  name: fixture\n  type: []\nversioning:\n"
        "  strategy: semver\n  files:\n"
        "  - .worktrees/ticket-001--adoption/src/fixture/__init__.py:__version__\n",
        encoding="utf-8",
    )
    _git(root, "add", "goal.yaml")
    _git(root, "commit", "--quiet", "-m", "generated goal config")
    _git(root, "push", "--quiet", "origin", "main")
    before_config = config.read_bytes()
    before_remote = _git(root, "ls-remote", "origin", "refs/heads/main").stdout
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, "-m", "goal", "-a", "--no-publish"],
        cwd=root, env=environment, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert delivery.GOVERNED_CLONE_DIAGNOSTIC in result.stdout + result.stderr
    assert config.read_bytes() == before_config
    assert _git(root, "ls-remote", "origin", "refs/heads/main").stdout == before_remote
    assert _git(root, "status", "--porcelain").stdout == ""
