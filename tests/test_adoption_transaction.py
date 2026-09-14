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


def _binding_checkout(tmp_path, *, supported=None, migrations=None):
    import hashlib
    import json
    import subprocess

    root = tmp_path / "consumer"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    lock = root / ".governance" / "manifest.lock.json"
    lock.parent.mkdir()
    lock.write_text(json.dumps({
        "schema": "new-project.lock/v1",
        "standard": {"id": "wellmanifest/new-project", "sourceRepository": "wellmanifest/new-project",
                     "publicationStatus": "published", "sourceRevision": "a" * 40},
    }), encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    _binding_commit(root)
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({
        "schema": "goal.adoption-catalog/v1",
        "standardRepository": "wellmanifest/new-project",
        "supportedRevisions": ["b" * 40] if supported is None else supported,
        "migrations": [{"fromRevision": "a" * 40, "toRevision": "b" * 40,
                        "recipe": "goal-governance-adopt/v1"}] if migrations is None else migrations,
    }), encoding="utf-8")
    return root, catalog, hashlib.sha256(catalog.read_bytes()).hexdigest()


def _binding_commit(root):
    import subprocess

    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
                    "commit", "-qam", "fixture"], check=True)


def _prepare_binding(root, catalog, digest, **overrides):
    from goal.governance.adoption_transaction import prepare_adoption_transaction

    options = dict(repository="semcod/fixture", ticket="ticket-001",
                   profile_digest="c" * 64, scope_digest="d" * 64)
    options.update(overrides)
    return prepare_adoption_transaction(root, catalog, digest, **options)


def test_planner_binding_single_step_is_stable_and_read_only(tmp_path, monkeypatch):
    import subprocess

    root, catalog, digest = _binding_checkout(tmp_path)
    lock = root / ".governance" / "manifest.lock.json"
    before = lock.read_bytes()
    run = subprocess.run
    calls = []

    def observed_run(argv, *args, **kwargs):
        calls.append(argv)
        return run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", observed_run)
    plan = _prepare_binding(root, catalog, digest)
    assert plan == _prepare_binding(root, catalog, digest)
    assert plan.from_revision == "a" * 40
    assert plan.to_revision == "b" * 40
    assert plan.profile_digest == "c" * 64
    assert plan.scope_digest != "d" * 64
    assert lock.read_bytes() == before
    assert calls and all(argv[0] == "git" for argv in calls)
    assert run(["git", "-C", str(root), "status", "--porcelain"],
               check=True, capture_output=True).stdout == b""


def test_planner_binding_retains_supported_pin_even_with_dirty_product(tmp_path):
    root, catalog, digest = _binding_checkout(tmp_path, supported=["a" * 40, "b" * 40])
    (root / "product.txt").write_text("unrelated local work", encoding="utf-8")
    assert _prepare_binding(root, catalog, digest) is None


def test_planner_binding_honors_explicit_supported_destination(tmp_path):
    root, catalog, digest = _binding_checkout(tmp_path, supported=["a" * 40, "b" * 40])
    assert _prepare_binding(root, catalog, digest) is None
    assert _prepare_binding(root, catalog, digest, target_revision="b" * 40).to_revision == "b" * 40


def test_planner_binding_rejects_dirty_migration(tmp_path):
    import pytest
    from goal.governance.adoption_plan import AdoptionPlanError

    root, catalog, digest = _binding_checkout(tmp_path)
    (root / "product.txt").write_text("local work", encoding="utf-8")
    with pytest.raises(AdoptionPlanError, match="dirty_worktree"):
        _prepare_binding(root, catalog, digest)


def test_planner_binding_rejects_changed_working_lock(tmp_path):
    import pytest
    from goal.governance.adoption_plan import AdoptionPlanError

    root, catalog, digest = _binding_checkout(tmp_path)
    lock = root / ".governance" / "manifest.lock.json"
    lock.write_bytes(lock.read_bytes() + b"\n")
    with pytest.raises(AdoptionPlanError, match="observation_changed"):
        _prepare_binding(root, catalog, digest)


def test_planner_binding_does_not_collapse_multiple_steps(tmp_path):
    import pytest
    from goal.governance.adoption_plan import AdoptionPlanError

    root, catalog, digest = _binding_checkout(tmp_path, supported=["c" * 40], migrations=[
        {"fromRevision": "a" * 40, "toRevision": "b" * 40, "recipe": "goal-governance-adopt/v1"},
        {"fromRevision": "b" * 40, "toRevision": "c" * 40, "recipe": "goal-governance-adopt/v1"},
    ])
    with pytest.raises(AdoptionPlanError, match="exactly one migration step"):
        _prepare_binding(root, catalog, digest)


def test_planner_binding_catalog_bytes_invalidate_subject(tmp_path):
    import hashlib
    import pytest
    from goal.governance.adoption_plan import AdoptionPlanError

    root, catalog, digest = _binding_checkout(tmp_path)
    before = _prepare_binding(root, catalog, digest)
    catalog.write_bytes(catalog.read_bytes() + b"\n")
    with pytest.raises(AdoptionPlanError, match="SHA-256 mismatch"):
        _prepare_binding(root, catalog, digest)
    after = _prepare_binding(root, catalog, hashlib.sha256(catalog.read_bytes()).hexdigest())
    assert before.scope_digest != after.scope_digest
    assert before.from_revision == after.from_revision
    assert before.to_revision == after.to_revision


def test_planner_binding_committed_lock_invalidates_subject(tmp_path):
    root, catalog, digest = _binding_checkout(tmp_path)
    before = _prepare_binding(root, catalog, digest)
    lock = root / ".governance" / "manifest.lock.json"
    lock.write_bytes(lock.read_bytes() + b"\n")
    _binding_commit(root)
    after = _prepare_binding(root, catalog, digest)
    assert before.base_sha != after.base_sha
    assert before.scope_digest != after.scope_digest


def test_planner_binding_declared_subject_changes_are_preserved(tmp_path):
    root, catalog, digest = _binding_checkout(tmp_path)
    before = _prepare_binding(root, catalog, digest)
    for change in ({"repository": "semcod/another"}, {"ticket": "ticket-002"},
                   {"profile_digest": "e" * 64}, {"scope_digest": "f" * 64}):
        assert _prepare_binding(root, catalog, digest, **change) != before


def test_planner_binding_rejects_invalid_raw_scope(tmp_path):
    import pytest
    from goal.governance.adoption_plan import AdoptionPlanError

    root, catalog, digest = _binding_checkout(tmp_path)
    for scope in (None, True, "", "d" * 63, "D" * 64):
        with pytest.raises(AdoptionPlanError, match="scope SHA-256"):
            _prepare_binding(root, catalog, digest, scope_digest=scope)


def test_planner_binding_rejects_missing_route(tmp_path):
    import pytest
    from goal.governance.adoption_plan import AdoptionPlanError

    root, catalog, digest = _binding_checkout(tmp_path, migrations=[])
    with pytest.raises(AdoptionPlanError, match="migration_recipe_missing"):
        _prepare_binding(root, catalog, digest)
