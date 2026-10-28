"""Release-only policy applies independently of package metadata discovery."""
import json
from types import SimpleNamespace
from unittest.mock import patch

import click
import pytest

from goal.config import GoalConfig
from goal.cli.version_state import VersionDecision
from goal.push.core import _mirror_github_release, _recover_existing_generic_release_decision


def configuration(tmp_path, loaded):
    config = {"project": {"name": "standard"}, "publishing": {"enabled": False,
        "fallback": {"github_release": {"enabled": True, "owner": "example",
            "repo": "standard", "create_on_tag": True}}}}
    if loaded:
        path = tmp_path / "goal.yaml"
        path.write_text(json.dumps(config))
        return GoalConfig(str(path))
    return config


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize("success", [False, True])
def test_disabled_registry_mirrors_without_assets_and_retains_terminal_failure(tmp_path, loaded, success):
    config = configuration(tmp_path, loaded)
    with patch("goal.publish.github_fallback.try_github_release_on_tag", return_value=success) as mirror:
        def run():
            _mirror_github_release(tag_name="v1.0.0", effective_no_tag=False,
                delivery=SimpleNamespace(mode="direct-main"), project_types=["python"],
                new_version="1.0.0", publish_config=config)
        if success:
            run()
        else:
            with pytest.raises(click.ClickException, match="GitHub Release creation failed"):
                run()
    assert mirror.call_args.kwargs["artifacts"] == []
    assert mirror.call_args.kwargs["allow_empty_assets"] is True
    assert mirror.call_args.kwargs["package_name"] == "standard"


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize("valid_tag", [False, True])
def test_release_only_repair_still_requires_exact_annotated_tag(tmp_path, loaded, valid_tag):
    config = configuration(tmp_path, loaded)
    decision = VersionDecision(current_version="1.0.0", target_version="1.0.1",
        reason="normal-bump", sources=(), baseline_version="1.0.0",
        baseline_evidence=("git-tag:v1.0.0",), registry_versions=(),
        unavailable_registries=(), derived_paths=())
    with patch("goal.push.core.reuse_exact_annotated_tag", return_value="v1.0.0",
            side_effect=None if valid_tag else click.ClickException("tag is not at exact HEAD")) as reuse:
        def run():
            return _recover_existing_generic_release_decision("1.0.0", decision,
                clean_force_publish=True, delivery=SimpleNamespace(mode="direct-main"),
                project_types=["python"], publish_config=config)
        if valid_tag:
            resolved, repaired = run()
            assert repaired and resolved.target_version == "1.0.0"
            assert resolved.reason == "existing-tag-release-repair"
        else:
            with pytest.raises(click.ClickException, match="exact HEAD"):
                run()
    reuse.assert_called_once_with("1.0.0")


def _git(cwd, *args):
    import subprocess
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_canonical_lease(
    primary,
    *,
    ticket="ticket-001",
    slug="release",
    repository_ref="github:semcod/goal",
    target_branch="main",
    branch_ref=None,
    phase="approved",
    head_sha=None,
    expires_at="2099-01-01T00:00:00Z",
    fencing_seq=1,
    revision=1,
):
    worktree_id = f"{ticket}--{slug}"
    ticket_num = ticket.removeprefix("ticket-")
    resolved_branch = branch_ref or f"refs/heads/ticket/{ticket_num}-{slug}"
    frozen = phase in {"publication_frozen", "dispatching", "approved"}
    lease_dir = primary / ".subactor" / "leases"
    lease_dir.mkdir(parents=True, exist_ok=True)
    lease_path = lease_dir / f"{worktree_id}.json"
    payload = {
        "schema": "wellmanifest.change-lease/v1",
        "leaseId": f"lease:semcod/goal:{worktree_id}",
        "repositoryRef": repository_ref,
        "targetBranch": target_branch,
        "ticketId": ticket,
        "workstream": "application",
        "scopeHash": "a" * 64,
        "branchRef": resolved_branch,
        "worktreeId": worktree_id,
        "ownerActor": "agent:test",
        "ownerSession": "session:test",
        "phase": phase,
        "leaseRevision": revision,
        "fencingToken": fencing_seq,
        "issuedAt": "2026-10-28T10:00:00Z",
        "expiresAt": expires_at,
        "heartbeatAt": "2026-10-28T10:05:00Z",
        "headSha": head_sha,
        "pullRequest": 10,
        "validatorRunId": "run-1",
        "publicationFrozen": frozen,
        "planHash": "b" * 64,
        "previousReceiptRef": None,
        "eventSequence": revision,
    }
    lease_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return lease_path


def _write_terminal_receipts(
    primary,
    *,
    repository_ref,
    terminal_sha,
    head_sha=None,
    ticket="ticket-001",
    outcome="merged",
    target_branch="main",
):
    registry_path = primary / ".git" / "new-project" / "terminal-receipts.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "new-project.terminal-receipt-registry/v1",
        "repositoryRef": repository_ref,
        "receipts": [
            {
                "receiptRef": f"receipt:github-pr:semcod/goal:{ticket}",
                "ticket": ticket,
                "outcome": outcome,
                "headSha": head_sha or terminal_sha,
                "terminalSha": terminal_sha,
                "targetBranch": target_branch,
                "occurredAt": "2026-10-28T10:00:00Z",
            }
        ],
    }
    registry_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return registry_path


def _setup_canonical_release_workflow_repo(tmp_path):

    remote = tmp_path / "remotes" / "semcod" / "goal.git"
    remote.parent.mkdir(parents=True, exist_ok=True)
    _git(tmp_path, "init", "--bare", "--quiet", str(remote))

    primary = tmp_path / "goal"
    primary.mkdir()
    _git(primary, "init", "--quiet", "-b", "main")
    _git(primary, "config", "user.email", "goal-release@example.invalid")
    _git(primary, "config", "user.name", "goal-release-test")
    (primary / ".gitignore").write_text("/.worktrees/\n/.subactor/\n", encoding="utf-8")
    (primary / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (primary / "pyproject.toml").write_text(
        '[project]\nname = "goal-release-fixture"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    _git(primary, "add", ".gitignore", "VERSION", "pyproject.toml")
    _git(primary, "commit", "--quiet", "-m", "v1.0.0 baseline")
    _git(primary, "tag", "-a", "v1.0.0", "-m", "Release 1.0.0")
    _git(primary, "remote", "add", "origin", str(remote))
    _git(primary, "push", "--quiet", "-u", "origin", "main", "--tags")

    # Land merged version bump 1.1.0 on main
    (primary / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    (primary / "pyproject.toml").write_text(
        '[project]\nname = "goal-release-fixture"\nversion = "1.1.0"\n',
        encoding="utf-8",
    )
    _git(primary, "commit", "--quiet", "-am", "chore(release): bump to 1.1.0")
    _git(primary, "push", "--quiet", "origin", "main")
    head_sha = _git(primary, "rev-parse", "HEAD").stdout.strip()

    worktree = primary / ".worktrees" / "ticket-001--release"
    _git(
        primary,
        "worktree",
        "add",
        "--relative-paths",
        "-b",
        "ticket/001-release",
        str(worktree),
        "origin/main",
    )
    repo_ref = str(remote).removesuffix(".git").lower()
    _write_canonical_lease(
        primary,
        ticket="ticket-001",
        slug="release",
        repository_ref="github:semcod/goal",
        head_sha=head_sha,
    )
    _write_terminal_receipts(
        primary,
        repository_ref=repo_ref,
        terminal_sha=head_sha,
    )
    return primary, worktree, remote, head_sha


def test_canonical_release_workflow_pushes_only_tag_and_preserves_dirty_primary(
    tmp_path, monkeypatch
):
    from goal.cli.version_state import VersionDecision, VersionSource
    from goal.push.core import execute_push_workflow

    primary, worktree, remote, head_sha = _setup_canonical_release_workflow_repo(tmp_path)
    # Leave primary checkout dirty on a foreign branch
    _git(primary, "checkout", "-b", "wip/unrelated")
    (primary / "dirty-primary.txt").write_text("do not touch\n", encoding="utf-8")

    monkeypatch.chdir(worktree)
    monkeypatch.setenv("PWD", str(worktree))

    config = {
        "project": {"name": "goal-release-fixture"},
        "governance": {
            "delivery": {
                "default_mode": "direct-main",
                "allowed_modes": ["direct-main", "pull-request"],
                "require_goal_a": True,
                "require_clean_governance": False,
            }
        },
    }
    source = VersionSource(
        spec="VERSION",
        path="VERSION",
        selector="",
        value="1.1.0",
        origin="configured",
    )
    decision = VersionDecision(
        current_version="1.1.0",
        target_version="1.1.0",
        reason="already-bumped",
        sources=(source,),
        baseline_version="1.0.0",
        baseline_evidence=("git-tag:v1.0.0",),
        registry_versions=(),
        unavailable_registries=(),
        derived_paths=(),
    )
    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": config,
        "user_config": {},
        "delivery_mode": "direct-main",
        "all_flags": True,
        "force_publish": True,
        "force_publish_explicit": True,
    }

    with (
        patch("goal.push.core._detect_project_types", return_value=["python"]),
        patch("goal.push.core._bootstrap_projects"),
        patch("goal.push.core.handle_todo_stage", return_value=True),
        patch(
            "goal.push.core.get_version_info",
            return_value=("1.0.0", "1.1.0", decision),
        ),
        patch("goal.cli.version_state.validate_version_sources"),
        patch("goal.push.core.run_test_stage", return_value=("Tests passed", 0)),
        patch("goal.push.core.handle_publish", return_value=(True, None)),
        patch("goal.push.core.output_final_summary"),
    ):
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket="ticket-001",
            abstraction=None,
            todo=False,
            force_publish=True,
        )

    # Verify v1.1.0 tag was pushed to remote and points to exact head_sha
    remote_tags = _git(worktree, "ls-remote", "--tags", "origin", "refs/tags/v1.1.0^{}").stdout
    assert head_sha in remote_tags
    # Verify ticket branch was NOT pushed to remote and main was unchanged
    remote_heads = _git(worktree, "ls-remote", "--heads", "origin").stdout
    assert "refs/heads/ticket/001-release" not in remote_heads
    assert f"{head_sha}\trefs/heads/main" in remote_heads
    # Verify primary checkout remains untouched on wip/unrelated with dirty file intact
    assert _git(primary, "branch", "--show-current").stdout.strip() == "wip/unrelated"
    assert (primary / "dirty-primary.txt").read_text(encoding="utf-8") == "do not touch\n"

    audit_path = primary / ".git" / "goal-delivery" / "delivery-events.jsonl"
    events = [
        json.loads(line)["result"]
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert "release-preflight" in events
    assert "release-tests-qualified" in events
    assert "release-tag" in events
    assert "pushed" in events


def test_canonical_release_workflow_aborts_when_state_changes_during_tests(
    tmp_path, monkeypatch
):
    from goal.cli.version_state import VersionDecision, VersionSource
    from goal.push.core import execute_push_workflow

    primary, worktree, _remote, head_sha = _setup_canonical_release_workflow_repo(tmp_path)
    monkeypatch.chdir(worktree)
    monkeypatch.setenv("PWD", str(worktree))

    config = {
        "project": {"name": "goal-release-fixture"},
        "governance": {
            "delivery": {
                "default_mode": "direct-main",
                "allowed_modes": ["direct-main"],
                "require_goal_a": True,
                "require_clean_governance": False,
            }
        },
    }
    source = VersionSource(
        spec="VERSION",
        path="VERSION",
        selector="",
        value="1.1.0",
        origin="configured",
    )
    decision = VersionDecision(
        current_version="1.1.0",
        target_version="1.1.0",
        reason="already-bumped",
        sources=(source,),
        baseline_version="1.0.0",
        baseline_evidence=("git-tag:v1.0.0",),
        registry_versions=(),
        unavailable_registries=(),
        derived_paths=(),
    )
    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": config,
        "user_config": {},
        "delivery_mode": "direct-main",
        "all_flags": True,
        "force_publish": True,
        "force_publish_explicit": True,
    }

    def mutate_lease_during_tests(*_args, **_kwargs):
        _write_canonical_lease(
            primary,
            ticket="ticket-001",
            slug="release",
            head_sha=head_sha,
            fencing_seq=2,
            revision=2,
        )
        return ("Tests passed", 0)

    with (
        patch("goal.push.core._detect_project_types", return_value=["python"]),
        patch("goal.push.core._bootstrap_projects"),
        patch("goal.push.core.handle_todo_stage", return_value=True),
        patch(
            "goal.push.core.get_version_info",
            return_value=("1.0.0", "1.1.0", decision),
        ),
        patch("goal.cli.version_state.validate_version_sources"),
        patch("goal.push.core.run_test_stage", side_effect=mutate_lease_during_tests),
        patch("goal.push.core.handle_publish") as publish_mock,
        pytest.raises(
            click.ClickException,
            match="canonical direct-main release state changed during test execution",
        ),
    ):
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket="ticket-001",
            abstraction=None,
            todo=False,
            force_publish=True,
        )

    publish_mock.assert_not_called()
    assert _git(worktree, "ls-remote", "--tags", "origin", "refs/tags/v1.1.0").stdout == ""


def test_canonical_release_workflow_rejects_existing_remote_tag_and_repairs_idempotently(
    tmp_path, monkeypatch
):
    from goal.cli.version_state import VersionDecision, VersionSource
    from goal.push.core import execute_push_workflow

    primary, worktree, _remote, head_sha = _setup_canonical_release_workflow_repo(tmp_path)
    _git(worktree, "tag", "-a", "v1.1.0", "-m", "Release 1.1.0")
    _git(worktree, "push", "--quiet", "origin", "refs/tags/v1.1.0")

    monkeypatch.chdir(worktree)
    monkeypatch.setenv("PWD", str(worktree))

    # 1. Ordinary already-bumped release fails closed when remote tag v1.1.0 already exists
    config = {
        "project": {"name": "goal-release-fixture"},
        "governance": {
            "delivery": {
                "default_mode": "direct-main",
                "allowed_modes": ["direct-main"],
                "require_goal_a": True,
                "require_clean_governance": False,
            }
        },
    }
    source = VersionSource(
        spec="VERSION",
        path="VERSION",
        selector="",
        value="1.1.0",
        origin="configured",
    )
    already_bumped = VersionDecision(
        current_version="1.1.0",
        target_version="1.1.0",
        reason="already-bumped",
        sources=(source,),
        baseline_version="1.0.0",
        baseline_evidence=("git-tag:v1.0.0",),
        registry_versions=(),
        unavailable_registries=(),
        derived_paths=(),
    )
    ctx_obj = {
        "yes": True,
        "markdown": False,
        "config": config,
        "user_config": {},
        "delivery_mode": "direct-main",
        "all_flags": True,
        "force_publish": True,
        "force_publish_explicit": True,
    }

    with (
        patch("goal.push.core._detect_project_types", return_value=["python"]),
        patch("goal.push.core._bootstrap_projects"),
        patch("goal.push.core.handle_todo_stage", return_value=True),
        patch(
            "goal.push.core.get_version_info",
            return_value=("1.0.0", "1.1.0", already_bumped),
        ),
        patch("goal.cli.version_state.validate_version_sources"),
        patch("goal.push.core.run_test_stage", return_value=("Tests passed", 0)),
        patch("goal.push.core.handle_publish") as publish_mock,
        pytest.raises(
            click.ClickException,
            match="tag v1.1.0 already exists on origin",
        ),
    ):
        execute_push_workflow(
            ctx_obj=ctx_obj,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket="ticket-001",
            abstraction=None,
            todo=False,
            force_publish=True,
        )

    publish_mock.assert_not_called()

    # 2. Generic GitHub release repair reuses existing v1.1.0 tag idempotently
    repair_config = {
        "project": {"name": "goal-release-fixture"},
        "publishing": {
            "enabled": False,
            "fallback": {
                "github_release": {
                    "enabled": True,
                    "owner": "semcod",
                    "repo": "goal",
                    "create_on_tag": True,
                }
            },
        },
        "governance": {
            "delivery": {
                "default_mode": "direct-main",
                "allowed_modes": ["direct-main"],
                "require_goal_a": True,
                "require_clean_governance": False,
            }
        },
    }
    normal_bump_after_tag = VersionDecision(
        current_version="1.1.0",
        target_version="1.1.1",
        reason="normal-bump",
        sources=(source,),
        baseline_version="1.1.0",
        baseline_evidence=("git-tag:v1.1.0",),
        registry_versions=(),
        unavailable_registries=(),
        derived_paths=(),
    )
    repair_ctx = {
        "yes": True,
        "markdown": False,
        "config": repair_config,
        "user_config": {},
        "delivery_mode": "direct-main",
        "all_flags": True,
        "force_publish": True,
        "force_publish_explicit": True,
    }

    with (
        patch("goal.push.core._detect_project_types", return_value=[]),
        patch("goal.push.core._bootstrap_projects"),
        patch("goal.push.core.handle_todo_stage", return_value=True),
        patch(
            "goal.push.core.get_version_info",
            return_value=("1.1.0", "1.1.1", normal_bump_after_tag),
        ),
        patch("goal.cli.version_state.validate_version_sources"),
        patch("goal.push.core.run_test_stage", return_value=("Tests passed", 0)),
        patch("goal.push.core.handle_publish", return_value=(True, None)),
        patch("goal.push.core.create_tag", return_value=None),
        patch(
            "goal.publish.github_fallback.try_github_release_on_tag",
            return_value=True,
        ) as mirror_mock,
        patch("goal.push.core.output_final_summary"),
    ):
        execute_push_workflow(
            ctx_obj=repair_ctx,
            bump="patch",
            no_tag=False,
            no_changelog=False,
            no_version_sync=False,
            message=None,
            dry_run=False,
            yes=True,
            markdown=False,
            split=False,
            ticket="ticket-001",
            abstraction=None,
            todo=False,
            force_publish=True,
        )

    mirror_mock.assert_called_once()
    audit_path = primary / ".git" / "goal-delivery" / "delivery-events.jsonl"
    events = [
        json.loads(line)["result"]
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert "release-tag-reused" in events

