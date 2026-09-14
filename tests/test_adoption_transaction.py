import hashlib
import json
from dataclasses import replace

import pytest

from goal.governance.adoption_transaction import (
    AdoptionPlan, AdoptionTransaction, Observation, PHASES, TransactionError,
)


@pytest.fixture
def plan():
    return AdoptionPlan("semcod/pilot", "ticket-001", "a" * 40,
                        "b" * 40, "c" * 40, "d" * 64, "e" * 64)


class FixtureAdapter:
    def __init__(self):
        self.applied = set()
        self.calls = []
        self.grant = True
        self.after_effect = None
        self.before_effect = None

    def observe(self, plan, phase, key):
        receipt = "sha256:" + hashlib.sha256(key.encode()).hexdigest()
        return Observation("APPLIED" if key in self.applied else "NOT_APPLIED",
                           plan.digest, key, receipt if key in self.applied else None)

    def authorize(self, plan, phase, key):
        return self.grant

    def apply(self, plan, phase, key):
        self.calls.append((phase, key))
        if self.before_effect:
            self.before_effect()
        self.applied.add(key)
        if self.after_effect:
            self.after_effect()


def advance(transaction, plan, adapter):
    return transaction.advance(plan, adapter, expected_revision=transaction.read(plan)["revision"])


def test_fixture_pipeline_and_terminal_resume_have_one_effect_per_phase(tmp_path, plan):
    adapter = FixtureAdapter()
    for phase in PHASES:
        transaction = AdoptionTransaction(tmp_path / "state.json")
        result = advance(transaction, plan, adapter)
        assert result["phase"] == phase
    assert result["status"] == "COMPLETE"
    assert advance(transaction, plan, adapter)["status"] == "COMPLETE"
    assert [phase for phase, _ in adapter.calls] == list(PHASES)


@pytest.mark.parametrize("phase", PHASES)
def test_restart_after_effect_before_checkpoint_uses_readback(tmp_path, plan, phase):
    class PowerLoss(BaseException):
        pass

    adapter = FixtureAdapter()
    transaction = AdoptionTransaction(tmp_path / "state.json")
    for earlier in PHASES[:PHASES.index(phase)]:
        assert advance(transaction, plan, adapter)["phase"] == earlier

    def interrupt():
        assert transaction.path.exists()
        raise PowerLoss()

    adapter.after_effect = interrupt
    with pytest.raises(PowerLoss):
        advance(transaction, plan, adapter)
    adapter.after_effect = None
    resumed = AdoptionTransaction(transaction.path)
    assert advance(resumed, plan, adapter)["reason"] == "OBSERVED"
    assert [item[0] for item in adapter.calls].count(phase) == 1


def test_unknown_timeout_cannot_blindly_repeat_effect(tmp_path, plan):
    adapter = FixtureAdapter()
    transaction = AdoptionTransaction(tmp_path / "state.json")

    def timeout():
        raise TimeoutError("private transport detail must not enter the journal")

    adapter.after_effect = timeout
    assert advance(transaction, plan, adapter)["reason"] == "OUTCOME_UNKNOWN"
    adapter.observe = lambda p, phase, key: Observation("UNKNOWN", p.digest, key)
    assert advance(transaction, plan, adapter)["reason"] == "OUTCOME_UNKNOWN"
    assert len(adapter.calls) == 1
    assert "private transport" not in transaction.path.read_text()


def test_authoritative_absence_allows_only_bounded_same_key_retry(tmp_path, plan):
    adapter = FixtureAdapter()
    transaction = AdoptionTransaction(tmp_path / "state.json")

    def fail_before_effect():
        raise TimeoutError()

    adapter.before_effect = fail_before_effect
    for _ in range(2):
        assert advance(transaction, plan, adapter)["reason"] == "OUTCOME_UNKNOWN"
    assert advance(transaction, plan, adapter)["reason"] == "RETRY_LIMIT"
    assert len(adapter.calls) == 2
    assert adapter.calls[0] == adapter.calls[1]


def test_fresh_authority_is_required_for_each_effect(tmp_path, plan):
    transaction = AdoptionTransaction(tmp_path / "state.json")
    adapter = FixtureAdapter()
    advance(transaction, plan, adapter)
    adapter.grant = False
    assert advance(transaction, plan, adapter)["reason"] == "AUTHORITY_REQUIRED"
    assert len(adapter.calls) == 1


def test_old_success_does_not_authorize_changed_evidence(tmp_path, plan):
    transaction = AdoptionTransaction(tmp_path / "state.json")
    adapter = FixtureAdapter()
    advance(transaction, plan, adapter)
    adapter.applied.clear()
    assert advance(transaction, plan, adapter)["reason"] == "EVIDENCE_STALE"
    assert len(adapter.calls) == 1


@pytest.mark.parametrize("field", ["repository", "ticket", "base_sha", "from_revision",
                                  "to_revision", "profile_digest", "scope_digest"])
def test_every_changed_plan_binding_rejects_journal_reuse(tmp_path, plan, field):
    transaction = AdoptionTransaction(tmp_path / "state.json")
    adapter = FixtureAdapter()
    advance(transaction, plan, adapter)
    values = {"repository": "semcod/other", "ticket": "ticket-002",
              "base_sha": "f" * 40, "from_revision": "f" * 40,
              "to_revision": "f" * 40, "profile_digest": "f" * 64,
              "scope_digest": "f" * 64}
    with pytest.raises(TransactionError, match="PLAN_MISMATCH"):
        advance(transaction, replace(plan, **{field: values[field]}), adapter)
    assert len(adapter.calls) == 1


def test_stale_revision_and_concurrent_writer_are_rejected(tmp_path, plan):
    transaction = AdoptionTransaction(tmp_path / "state.json")
    adapter = FixtureAdapter()

    def competing_writer():
        other = AdoptionTransaction(transaction.path)
        with pytest.raises(TransactionError, match="TRANSACTION_BUSY"):
            other.advance(plan, FixtureAdapter(), expected_revision=0)

    adapter.before_effect = competing_writer
    advance(transaction, plan, adapter)
    with pytest.raises(TransactionError, match="STALE_REVISION"):
        transaction.advance(plan, adapter, expected_revision=0)


@pytest.mark.parametrize("raw", ["{", '{"schema":1,"schema":2}', "[]"])
def test_corrupt_state_is_not_reset(tmp_path, plan, raw):
    path = tmp_path / "state.json"
    path.write_text(raw)
    with pytest.raises(TransactionError, match="INVALID_STATE"):
        advance(AdoptionTransaction(path), plan, FixtureAdapter())
    assert path.read_text() == raw


def test_symlink_state_is_rejected(tmp_path, plan):
    actual = tmp_path / "actual.json"
    actual.write_text("{}")
    link = tmp_path / "state.json"
    link.symlink_to(actual)
    with pytest.raises(TransactionError, match="SYMLINK_STATE_PATH"):
        AdoptionTransaction(link).read(plan)


def test_forged_complete_journal_is_not_trusted(tmp_path, plan):
    transaction = AdoptionTransaction(tmp_path / "state.json")
    state = transaction.read(plan)
    for step in state["steps"]:
        step.update(state="complete", receipt="sha256:" + "f" * 64)
    transaction.path.write_text(json.dumps(state))
    adapter = FixtureAdapter()
    assert advance(transaction, plan, adapter)["reason"] == "EVIDENCE_STALE"
    assert not adapter.calls


def test_cross_subject_observation_blocks_effect(tmp_path, plan):
    adapter = FixtureAdapter()
    adapter.observe = lambda p, phase, key: Observation("APPLIED", "f" * 64, key,
                                                       "sha256:" + "f" * 64)
    result = advance(AdoptionTransaction(tmp_path / "state.json"), plan, adapter)
    assert result["reason"] == "READBACK_UNAVAILABLE"
    assert not adapter.calls
