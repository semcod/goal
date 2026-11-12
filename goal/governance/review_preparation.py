"""Explicit source-hub PR preparation; pending verification grants no approval."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import click

from goal.governance import delivery
from goal.governance.source_hub_process import run_check


def configure_strategy(context: dict, strategy: str) -> None:
    """Require an explicit full workflow with registry publication disabled."""
    if strategy != "protected-ci":
        raise click.ClickException("unknown source-hub verification strategy")
    if not context.get("all_flags") or not context.get("no_publish"):
        raise click.ClickException("protected-ci requires explicit -a --no-publish")
    if any(
        context.get(key)
        for key in (
            "upgrade_deps",
            "version",
            "todo",
            "recursive",
            "force_publish_explicit",
            "koru",
            "dry_run",
        )
    ):
        raise click.ClickException(
            "protected-ci only prepares an already committed candidate"
        )
    context["source_hub_verification"] = strategy


def preflight_arguments(context: dict, policy, ticket: str | None) -> dict:
    if context.get("source_hub_verification", "local") == "local":
        return {}
    configure_strategy(context, context["source_hub_verification"])
    validate_strategy(policy)
    if not ticket:
        raise click.ClickException("protected-ci requires explicit --ticket ticket-NNN")
    context["_source_review_candidate"] = delivery.pending_pull_request_delivery(
        policy, ticket=ticket
    )
    require_prepared_candidate(context, context["_source_review_candidate"])
    return {"source_hub_verification": "protected-ci", "ticket": ticket}


def validate_strategy(policy) -> None:
    if (
        policy is None
        or policy.mode != "pull-request"
        or not policy.require_goal_a
        or not policy.require_clean_governance
    ):
        raise click.ClickException(
            "protected-ci requires governed pull-request mode with all local safety checks"
        )


def _bounded_check(command: list[str], *, cwd: Path):
    try:
        result = run_check(command, cwd=cwd, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise click.ClickException(
            f"protected-ci preparation check failed: {error}"
        ) from error
    if result.returncode:
        raise click.ClickException(
            (result.stdout + "\n" + result.stderr).strip()
            or "protected-ci preparation check failed"
        )
    return result


def _canonical_writer(root: Path, policy, ticket: str) -> None:
    records = delivery._registered_worktrees(root)
    primary = Path(records[0]["path"])
    branch = delivery._git_value("branch", "--show-current", cwd=root)
    match = re.fullmatch(r"ticket/([0-9]{3,})-([a-z0-9]+(?:-[a-z0-9]+)*)", branch)
    if match is None or ticket != "ticket-" + match[1]:
        raise click.ClickException("protected-ci requires a canonical ticket branch")
    worktree_id = f"{ticket}--{match[2]}"
    expected = primary / ".worktrees" / worktree_id
    lease_path = primary / ".subactor/leases" / (worktree_id + ".json")
    delivery._reject_worktree_symlinks(primary, Path.cwd(), root, lease_path)
    if root != expected or expected.resolve() != expected:
        raise click.ClickException(
            "protected-ci requires the canonical registered ticket worktree"
        )
    if sum(row.get("branch") == "refs/heads/" + branch for row in records) != 1:
        raise click.ClickException("protected-ci refuses duplicate ticket worktrees")
    dot_git = root / ".git"
    text = dot_git.read_text(encoding="utf-8").strip() if dot_git.is_file() else ""
    target = text.removeprefix("gitdir: ")
    if not text.startswith("gitdir: ") or not target or Path(target).is_absolute():
        raise click.ClickException("protected-ci requires relative Worktrees v5 links")
    backlink = (root / target).resolve() / "gitdir"
    if not backlink.is_file() or Path(backlink.read_text().strip()).is_absolute():
        raise click.ClickException(
            "protected-ci requires relative Worktrees v5 backlinks"
        )
    checker = root / "scripts/change_lease_check.py"
    if not checker.is_file():
        raise click.ClickException(
            "protected-ci requires the native controller writer checker"
        )
    _bounded_check(
        [
            sys.executable,
            str(checker),
            "--format",
            "json",
            "writer-check",
            "--root",
            str(root),
            "--ref",
            "refs/heads/" + branch,
            "--operation",
            "commit",
        ],
        cwd=root,
    )
    try:
        lease = json.loads(lease_path.read_text(encoding="utf-8"))
        identity = {
            "NEW_PROJECT_WRITER_ACTOR": lease["ownerActor"],
            "NEW_PROJECT_WRITER_SESSION": lease["ownerSession"],
            "NEW_PROJECT_LEASE_REVISION": str(lease["leaseRevision"]),
            "NEW_PROJECT_FENCING_TOKEN": str(lease["fencingToken"]),
        }
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise click.ClickException(
            "protected-ci cannot read the controller lease"
        ) from error
    if any(os.environ.get(key) != value for key, value in identity.items()):
        raise click.ClickException(
            "protected-ci writer identity/fencing differs from the controller"
        )
    if lease.get("headSha") not in {
        None,
        delivery._git_value("rev-parse", "HEAD", cwd=root),
    }:
        raise click.ClickException("protected-ci controller lease head changed")


def validate_preparation(policy, ticket: str | None, root: Path, *, base=None):
    """Run bounded safety checks, leaving every shell suite pending in CI.

    This deliberately returns a candidate, never SourceHubHealthResult or PASS,
    and never reads or writes the local source-health success cache.
    """
    validate_strategy(policy)
    if not delivery.is_new_project_source_hub(root):
        raise click.ClickException("protected-ci preparation requires a source hub")
    candidate = delivery.pending_pull_request_delivery(policy, ticket=ticket, cwd=root)
    if candidate is None:
        raise click.ClickException(
            "protected-ci requires a clean, already committed ticket candidate"
        )
    if base is not None and candidate.base_sha != base:
        raise click.ClickException(
            "protected-ci authoritative base changed during preparation"
        )
    _canonical_writer(root, policy, ticket)
    contract = delivery._source_hub_contract(root)
    if isinstance(contract, delivery.SourceHubHealthResult):
        raise click.ClickException(contract.stderr)
    documents, commands = contract
    for document in documents:
        try:
            json.loads(document.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise click.ClickException(
                f"invalid canonical JSON {document.relative_to(root)}: {error}"
            ) from error
    _bounded_check(commands[0], cwd=root)
    delivery._source_hub_candidate_gate(
        root,
        base=candidate.base_sha,
        head=candidate.head_sha,
        runner=_bounded_check,
    )
    assert_candidate(policy, ticket, root, candidate)
    return candidate


def assert_candidate(policy, ticket, root, candidate) -> None:
    if (
        delivery.pending_pull_request_delivery(policy, ticket=ticket, cwd=root)
        != candidate
    ):
        raise click.ClickException(
            "protected-ci frozen candidate changed; reconcile before publication"
        )
    _canonical_writer(root, policy, ticket)


def submission_arguments(context: dict, candidate, ticket: str) -> dict:
    if context.get("source_hub_verification", "local") == "local":
        return {}
    require_prepared_candidate(context, candidate)
    return {
        "expected_candidate": candidate,
        "body": (
            f"Ticket: {ticket}\n\n"
            "Prepared by Goal; complete source-hub verification is PENDING in protected CI.\n"
            f"Frozen head: {candidate.head_sha}\nBase observed: {candidate.base_sha}\n\n"
            "Local candidate governance, canonical JSON, suite wiring and required-check comparison ran. "
            "Every source-hub shell suite, required Linux/Windows check, current-base verification "
            "and independent Validator approval remains mandatory before merge. "
            "This PR is not a health PASS, approval, merge or deployment."
        ),
    }


def require_prepared_candidate(context: dict, candidate) -> None:
    if context.get("source_hub_verification") != "protected-ci":
        return
    if candidate is None or candidate != context.get("_source_review_candidate"):
        raise click.ClickException(
            "protected-ci frozen candidate changed or is not a committed candidate"
        )


def preparation_result(context: dict) -> str:
    return (
        "pull-request-prepared"
        if context.get("source_hub_verification") == "protected-ci"
        else "pull-request"
    )
