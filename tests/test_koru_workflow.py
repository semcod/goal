"""Koru must respect Goal's preview, admission and failure boundaries."""
from types import SimpleNamespace
from unittest.mock import Mock

import click
import pytest

from goal.governance import delivery, remediation
from goal.push import core


class ReachedWorkflow(Exception):
    pass


@pytest.fixture
def workflow(monkeypatch):
    events = []
    policy = SimpleNamespace(mode="pull-request")
    monkeypatch.setattr(delivery, "resolve_delivery_policy", lambda *a, **k: policy)
    monkeypatch.setattr(delivery, "resolve_pull_request_ticket", lambda *a: "ticket-219")
    monkeypatch.setattr(delivery, "validate_delivery_ready", lambda *a, **k: events.append("admitted"))
    monkeypatch.setattr(core, "_validate_toml_or_exit", Mock(side_effect=ReachedWorkflow))
    repair = Mock(side_effect=lambda: (events.append("repair") or (True, "")))
    monkeypatch.setattr(remediation, "run_koru_repair", repair)
    args = dict(ctx_obj={}, bump="patch", no_tag=True, no_changelog=True,
                no_version_sync=True, message=None, dry_run=False, yes=True,
                markdown=False, split=False, ticket=None, abstraction=None,
                todo=False, koru=True)
    return args, events, repair, policy


@pytest.mark.parametrize("from_context", [False, True])
def test_dry_run_never_repairs(workflow, from_context):
    args, events, repair, _ = workflow
    if from_context:
        args["ctx_obj"] = {"dry_run": True, "koru": True}
        args["koru"] = False
    else:
        args["dry_run"] = True
    with pytest.raises(ReachedWorkflow):
        core.execute_push_workflow(**args)
    repair.assert_not_called()


def test_admission_precedes_repair(workflow):
    args, events, _, _ = workflow
    with pytest.raises(ReachedWorkflow):
        core.execute_push_workflow(**args)
    assert events == ["admitted", "repair", "admitted"]


def test_denied_admission_never_repairs(workflow, monkeypatch):
    args, _, repair, _ = workflow
    monkeypatch.setattr(delivery, "validate_delivery_ready", Mock(side_effect=click.ClickException("denied")))
    with pytest.raises(click.ClickException, match="denied"):
        core.execute_push_workflow(**args)
    repair.assert_not_called()


@pytest.mark.parametrize("mode,ticket", [("publish-only", "ticket-219"), ("direct-main", "ticket-219"), ("pull-request", None)])
def test_read_only_release_checkout_never_repairs(workflow, monkeypatch, mode, ticket):
    args, _, repair, policy = workflow
    policy.mode = mode
    monkeypatch.setattr(delivery, "resolve_pull_request_ticket", lambda *a: ticket)
    with pytest.raises(click.ClickException, match="ticket worktree"):
        core.execute_push_workflow(**args)
    repair.assert_not_called()


def test_failed_repair_stops_workflow(workflow):
    args, _, repair, _ = workflow
    repair.side_effect = None
    repair.return_value = (False, "repair timed out")
    with pytest.raises(click.ClickException, match="repair timed out"):
        core.execute_push_workflow(**args)


def test_no_koru_flag_does_not_repair(workflow):
    args, _, repair, _ = workflow
    args["koru"] = False
    with pytest.raises(ReachedWorkflow):
        core.execute_push_workflow(**args)
    repair.assert_not_called()


def test_repair_rechecks_legacy_no_change(workflow, monkeypatch):
    args, events, repair, _ = workflow
    monkeypatch.setattr(delivery, "resolve_delivery_policy", lambda *a, **k: None)
    admission = Mock(side_effect=[True, None])
    monkeypatch.setattr(delivery, "validate_legacy_governance", admission)
    with pytest.raises(ReachedWorkflow):
        core.execute_push_workflow(**args)
    repair.assert_called_once()
    assert admission.call_count == 2


def test_repair_mutation_is_rechecked(workflow, monkeypatch):
    args, _, repair, _ = workflow
    monkeypatch.setattr(delivery, "validate_delivery_ready", Mock(side_effect=[None, click.ClickException("scope changed")]))
    with pytest.raises(click.ClickException, match="scope changed"):
        core.execute_push_workflow(**args)
    repair.assert_called_once()
