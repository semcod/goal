"""Exercise pending source verification with real Git histories and frozen pushes."""

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import click
import pytest
from click.testing import CliRunner

from goal.governance import delivery
from goal.governance import review_preparation as review


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


@pytest.fixture
def hub(tmp_path, monkeypatch):
    primary = tmp_path / "hub"
    primary.mkdir()
    git(primary, "init", "-q", "-b", "main")
    git(primary, "config", "user.name", "Test")
    git(primary, "config", "user.email", "test@example.invalid")
    (primary / ".gitignore").write_text("/.worktrees/\n/.subactor/\n")
    for directory in ("governance", "scripts", "tests", ".github/workflows"):
        (primary / directory).mkdir(parents=True)
    for name in (
        "manifest.default",
        "package-manifest",
        "manifest.hub",
        "stack-profiles",
    ):
        (primary / f"governance/{name}.json").write_text("{}\n")
    (primary / "scripts/governance_check.py").write_text(
        "print('candidate governance ran')\n"
    )
    (primary / "scripts/check_required_checks.py").write_text(
        "print('required checks compared')\n"
    )
    # Fixture adapter stands in for the separately maintained native controller.
    # The Goal caller must still check current identity and re-observe the head.
    (primary / "scripts/change_lease_check.py").write_text(
        "import os,sys\nsys.exit(int(os.getenv('TEST_NATIVE_REJECTION','0')))\n"
    )
    (primary / "tests/slow.test.sh").write_text("exit 17\n")
    (primary / ".github/workflows/ci.yml").write_text(
        "jobs:\n  test:\n    steps:\n      - run: bash tests/slow.test.sh\n"
    )
    git(primary, "add", ".")
    git(primary, "commit", "-qm", "baseline")
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "-q", str(remote))
    git(primary, "remote", "add", "origin", str(remote))
    git(primary, "push", "-q", "origin", "main")
    root = primary / ".worktrees/ticket-001--review"
    git(
        primary,
        "worktree",
        "add",
        "--relative-paths",
        "-b",
        "ticket/001-review",
        str(root),
    )
    (root / "candidate.txt").write_text("material candidate\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "[ticket-001] feat(hub): prepare candidate")
    lease = primary / ".subactor/leases/ticket-001--review.json"
    lease.parent.mkdir(parents=True)
    lease.write_text(
        json.dumps(
            {
                "ownerActor": "agent:test",
                "ownerSession": "test-review",
                "leaseRevision": 2,
                "fencingToken": 7,
                "headSha": git(root, "rev-parse", "HEAD"),
            }
        )
    )
    for key, value in {
        "WRITER_ACTOR": "agent:test",
        "WRITER_SESSION": "test-review",
        "LEASE_REVISION": "2",
        "FENCING_TOKEN": "7",
    }.items():
        monkeypatch.setenv("NEW_PROJECT_" + key, value)
    monkeypatch.chdir(root)
    policy = delivery.DeliveryPolicy(
        "pull-request", True, ("pull-request",), "origin", "main", True
    )
    return root, primary, remote, policy, lease


def test_pending_preflight_preserves_complete_local_failure_and_cache_isolation(
    hub, monkeypatch
):
    root, _, _, policy, _ = hub
    original = delivery._run
    monkeypatch.setattr(
        delivery,
        "_run",
        lambda args, **kw: (
            subprocess.CompletedProcess(args, 0, "", "")
            if args == ["gh", "auth", "status"]
            else original(args, **kw)
        ),
    )
    monkeypatch.setattr(
        delivery.shutil,
        "which",
        lambda name: "/bin/bash" if name == "bash" else "/usr/bin/gh",
    )
    before = set(delivery._DELIVERY_GATE_CACHE)
    assert (
        delivery.validate_delivery_ready(
            policy, ticket="ticket-001", source_hub_verification="protected-ci"
        )
        is None
    )
    assert delivery._DELIVERY_GATE_CACHE == before
    assert not (root / delivery.SOURCE_HUB_CACHE_FILE).exists()
    with pytest.raises(click.ClickException, match="source-hub check failed"):
        delivery.validate_delivery_ready(policy)
    assert not (root / delivery.SOURCE_HUB_CACHE_FILE).exists()
    assert not git(root, "status", "--porcelain")


@pytest.mark.parametrize(
    "fault",
    [
        "dirty",
        "unbound",
        "divergent",
        "json",
        "unwired",
        "required",
        "native",
        "fence",
        "head",
        "missing-native",
        "not-hub",
    ],
)
def test_preparation_refuses_unsafe_candidates_without_push(hub, monkeypatch, fault):
    root, primary, _, policy, lease = hub
    if fault == "dirty":
        (root / "dirty").write_text("uncommitted")
    elif fault == "unbound":
        git(root, "commit", "--amend", "-qm", "unbound subject")
    elif fault == "divergent":
        (primary / "new-base").write_text("remote advanced")
        git(primary, "add", ".")
        git(primary, "commit", "-qm", "new base")
        git(primary, "push", "-q", "origin", "main")
    elif fault in {"json", "unwired", "required", "missing-native", "not-hub"}:
        path, text = {
            "json": ("governance/broken.json", "{"),
            "unwired": (".github/workflows/ci.yml", "jobs: {}\n"),
            "required": ("scripts/check_required_checks.py", "raise SystemExit(9)\n"),
            "missing-native": ("scripts/change_lease_check.py", None),
            "not-hub": ("governance/package-manifest.json", None),
        }[fault]
        if text is None:
            (root / path).unlink()
        else:
            (root / path).write_text(text)
        git(root, "add", ".")
        git(root, "commit", "-qm", "[ticket-001] test(hub): unsafe fixture")
        data = json.loads(lease.read_text())
        data["headSha"] = git(root, "rev-parse", "HEAD")
        lease.write_text(json.dumps(data))
    elif fault == "native":
        monkeypatch.setenv("TEST_NATIVE_REJECTION", "3")
    elif fault == "fence":
        monkeypatch.setenv("NEW_PROJECT_FENCING_TOKEN", "6")
    elif fault == "head":
        data = json.loads(lease.read_text())
        data["headSha"] = "a" * 40
        lease.write_text(json.dumps(data))
    before = git(primary, "ls-remote", "origin", "refs/heads/ticket/001-review")
    with pytest.raises(click.ClickException):
        review.validate_preparation(policy, "ticket-001", root)
    assert (
        git(primary, "ls-remote", "origin", "refs/heads/ticket/001-review")
        == before
        == ""
    )
    assert not (root / delivery.SOURCE_HUB_CACHE_FILE).exists()


@pytest.mark.parametrize("mode", ["direct-main", "publish-only"])
def test_refuses_non_pr_strategy(hub, mode):
    root, _, _, policy, _ = hub
    with pytest.raises(click.ClickException, match="pull-request mode"):
        delivery.validate_delivery_ready(
            replace(policy, mode=mode), cwd=root, source_hub_verification="protected-ci"
        )


def test_requires_canonical_registered_checkout(hub):
    root, primary, _, policy, _ = hub
    with pytest.raises(click.ClickException, match="canonical"):
        review._canonical_writer(primary, policy, "ticket-001")
    git(root, "switch", "-c", "other")
    with pytest.raises(click.ClickException, match="canonical"):
        review.validate_preparation(policy, "ticket-001", root)


def test_pushes_exact_sha_and_marks_pr_pending(hub, monkeypatch):
    root, _, remote, policy, _ = hub
    candidate = review.validate_preparation(policy, "ticket-001", root)
    context = {
        "source_hub_verification": "protected-ci",
        "_source_review_candidate": candidate,
    }
    original = delivery._run
    effects = []
    created = False

    def run(args, **kwargs):
        nonlocal created
        if args[:2] == ["git", "push"]:
            effects.append(args)
        if args[:3] == ["gh", "pr", "list"]:
            queried = args[args.index("--head") + 1]
            rows = (
                [
                    {
                        "url": "https://github.com/example/hub/pull/1",
                        "headRefOid": candidate.head_sha,
                    }
                ]
                if created and queried == "ticket/001-review"
                else []
            )
            return subprocess.CompletedProcess(args, 0, json.dumps(rows), "")
        if args[:3] == ["gh", "pr", "create"]:
            effects.append(args)
            created = True
            return subprocess.CompletedProcess(args, 0, "", "")
        return original(args, **kwargs)

    monkeypatch.setattr(delivery, "_run", run)
    kwargs = review.submission_arguments(context, candidate, "ticket-001")
    from goal.push import core

    tests = Mock()
    monkeypatch.setattr(core, "_run_test_stage_or_exit", tests)
    monkeypatch.setattr("goal.cli.version.get_current_version", lambda: "1.0.0")
    core._resume_pending_pull_request(
        context, ["python"], False, policy, "ticket-001", candidate
    )
    tests.assert_called_once()
    assert tests.call_args.args[3] == list(candidate.files)
    audit = json.loads(delivery._audit_path(root).read_text().splitlines()[-1])
    assert audit["result"] == "pull-request-prepared"
    assert effects[0][-1] == candidate.head_sha + ":refs/heads/ticket/001-review"
    assert (
        git(remote, "rev-parse", "refs/heads/ticket/001-review") == candidate.head_sha
    )
    assert "PENDING" in effects[1][effects[1].index("--body") + 1]
    assert "--draft" not in effects[1]
    assert review.preparation_result(context) == "pull-request-prepared"
    # A retry observes the existing PR and does not create another one.
    delivery.deliver_pull_request(
        policy, ticket="ticket-001", title=candidate.title, cwd=root, **kwargs
    )
    assert sum(args[:3] == ["gh", "pr", "create"] for args in effects) == 1


def test_changed_frozen_head_refused_before_remote_effect(hub, monkeypatch):
    root, _, _, policy, _ = hub
    candidate = review.validate_preparation(policy, "ticket-001", root)
    changed = replace(candidate, head_sha="a" * 40)
    with pytest.raises(click.ClickException, match="changed before push"):
        delivery.deliver_pull_request(
            policy,
            ticket="ticket-001",
            title=candidate.title,
            cwd=root,
            expected_candidate=changed,
        )
    assert git(root, "ls-remote", "origin", "refs/heads/ticket/001-review") == ""
    context = {
        "source_hub_verification": "protected-ci",
        "_source_review_candidate": candidate,
    }
    for unsafe in (None, changed):
        with pytest.raises(click.ClickException, match="frozen candidate"):
            review.require_prepared_candidate(context, unsafe)


def test_rest_recovery_preserves_pending_body(tmp_path, monkeypatch):
    policy = delivery.DeliveryPolicy(
        "pull-request", True, ("pull-request",), "origin", "main", True
    )
    monkeypatch.setattr(delivery, "_rest_open_pull_requests", lambda *_: [])
    monkeypatch.setattr(delivery, "_rest_repository", lambda *_: "example/hub")
    payloads = []

    def run(args, **kwargs):
        payloads.append(json.loads(Path(args[-1]).read_text()))
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(delivery, "_run", run)
    delivery._recover_pull_request_creation(
        policy,
        "ticket/001-review",
        "Title",
        tmp_path,
        body="Ticket: ticket-001\nVerification PENDING",
    )
    assert payloads[0]["body"] == "Ticket: ticket-001\nVerification PENDING"


@pytest.mark.parametrize(
    "context",
    [
        {},
        {"all_flags": True},
        {"all_flags": True, "no_publish": True, "upgrade_deps": True},
    ],
)
def test_explicit_strategy_requires_full_frozen_workflow(context):
    with pytest.raises(click.ClickException):
        review.configure_strategy(context, "protected-ci")


def test_cli_accepts_global_strategy_without_mutating_configuration(monkeypatch):
    from goal import cli
    from goal.cli import push_cmd

    configure = Mock(
        side_effect=lambda ctx, *args, **kw: setattr(
            ctx, "obj", {"all_flags": True, "no_publish": True}
        )
    )
    monkeypatch.setattr(cli, "_configure_main_context", configure)
    monkeypatch.setattr(cli, "_setup_nfo_logging", Mock())
    update = Mock()
    monkeypatch.setattr(cli, "_maybe_self_update", update)
    execute = Mock()
    monkeypatch.setattr(push_cmd, "execute_push_workflow", execute)
    result = CliRunner().invoke(
        cli.main,
        [
            "-a",
            "--no-publish",
            "--source-hub-verification",
            "protected-ci",
            "--delivery-mode",
            "pull-request",
            "push",
            "--ticket",
            "ticket-001",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (
        execute.call_args.kwargs["ctx_obj"]["source_hub_verification"] == "protected-ci"
    )
    update.assert_not_called()
