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


class _CommandBoundary:
    def __init__(self):
        self.permitted = True
        self.observation = object()
        self.authorizations = []
        self.effects = []

    def observe(self, plan, phase, key):
        return self.observation

    def authorize(self, plan, phase, key):
        self.authorizations.append((plan, phase, key))
        return self.permitted

    def apply(self, plan, phase, key):
        self.effects.append((plan, phase, key))


def _command_adapter(tmp_path, **overrides):
    from goal.governance.adoption_transaction import GoalAdoptionAdapter

    root, catalog, digest = _binding_checkout(tmp_path)
    executable = tmp_path / "goal-fixture"
    executable.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    executable.chmod(0o700)
    boundary = _CommandBoundary()
    arguments = {
        "target_root": root, "catalog_path": catalog,
        "catalog_sha256": digest, "repository": "semcod/fixture",
        "ticket": "ticket-001", "profile_digest": "c" * 64,
        "scope_digest": "d" * 64, "goal_executable": executable,
        "timeout_seconds": 2, "delegate": boundary,
    }
    arguments.update(overrides)
    adapter = GoalAdoptionAdapter(**arguments)
    return adapter, boundary, root, catalog, executable


def _command_process(monkeypatch, executable, *, returncode=0, failure=None):
    import subprocess
    from types import SimpleNamespace

    original = subprocess.Popen
    calls = []
    waits = []

    def communicate(*, timeout):
        waits.append(timeout)
        if failure is not None:
            raise failure
        return None, None

    process = SimpleNamespace(
        pid=123456789, returncode=returncode, communicate=communicate,
        wait=lambda: waits.append("reaped"),
    )

    def spawn(argv, *args, **kwargs):
        if argv[0] != str(executable):
            return original(argv, *args, **kwargs)
        calls.append((argv, kwargs))
        return process

    monkeypatch.setattr(subprocess, "Popen", spawn)
    return calls, waits


def test_command_adapter_fixed_immutable_invocation_and_no_receipt(tmp_path, monkeypatch):
    import subprocess

    adapter, boundary, root, _, executable = _command_adapter(tmp_path)
    calls, waits = _command_process(monkeypatch, executable)
    key = adapter.plan.key("adoption")
    assert adapter.apply(adapter.plan, "adoption", key) is None
    assert calls == [([
        str(executable), "governance", "adopt", "--standard-repository",
        "https://github.com/wellmanifest/new-project.git", "--source-revision",
        adapter.plan.to_revision, "--target-root", str(root), "--upgrade",
    ], {
        "cwd": root, "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
        "start_new_session": True,
    })]
    assert waits == [2]
    assert len(boundary.authorizations) == 1
    assert boundary.effects == []
    assert adapter.observe(adapter.plan, "adoption", key) is boundary.observation


@pytest.mark.parametrize("phase", ["validation", "publication", "merge"])
def test_command_adapter_delegates_other_phases(tmp_path, monkeypatch, phase):
    adapter, boundary, _, _, executable = _command_adapter(tmp_path)
    calls, _ = _command_process(monkeypatch, executable)
    key = adapter.plan.key(phase)
    adapter.apply(adapter.plan, phase, key)
    assert boundary.effects == [(adapter.plan, phase, key)]
    assert len(boundary.authorizations) == 1
    assert calls == []


@pytest.mark.parametrize("mismatch", ["subject", "key", "phase"])
def test_command_adapter_rejects_mismatched_call(tmp_path, monkeypatch, mismatch):
    from dataclasses import replace

    adapter, boundary, _, _, executable = _command_adapter(tmp_path)
    calls, _ = _command_process(monkeypatch, executable)
    plan = replace(adapter.plan, ticket="ticket-002") if mismatch == "subject" else adapter.plan
    phase = "unknown" if mismatch == "phase" else "adoption"
    key = "foreign" if mismatch == "key" else adapter.plan.key("adoption")
    with pytest.raises(ValueError, match="mismatch"):
        adapter.apply(plan, phase, key)
    assert boundary.authorizations == []
    assert calls == []


@pytest.mark.parametrize("permission", [False, None, 1, "approved"])
def test_command_adapter_requires_explicit_fresh_authority(tmp_path, monkeypatch, permission):
    adapter, boundary, _, _, executable = _command_adapter(tmp_path)
    calls, _ = _command_process(monkeypatch, executable)
    key = adapter.plan.key("adoption")
    assert adapter.authorize(adapter.plan, "adoption", key) is True
    boundary.permitted = permission
    with pytest.raises(PermissionError, match="fresh"):
        adapter.apply(adapter.plan, "adoption", key)
    assert len(boundary.authorizations) == 2
    assert calls == []


@pytest.mark.parametrize("change", ["untracked", "catalog", "head"])
def test_command_adapter_reobserves_planning_inputs(tmp_path, monkeypatch, change):
    adapter, boundary, root, catalog, executable = _command_adapter(tmp_path)
    calls, _ = _command_process(monkeypatch, executable)
    if change == "catalog":
        catalog.write_bytes(catalog.read_bytes() + b"\n")
    elif change == "head":
        lock = root / ".governance" / "manifest.lock.json"
        lock.write_bytes(lock.read_bytes() + b"\n")
        _binding_commit(root)
    else:
        (root / "untracked-input").write_text("changed\n", encoding="utf-8")
    with pytest.raises(PermissionError):
        adapter.apply(adapter.plan, "adoption", adapter.plan.key("adoption"))
    assert boundary.authorizations == []
    assert calls == []


def test_command_adapter_reobserves_after_authority_wait(tmp_path, monkeypatch):
    adapter, boundary, root, _, executable = _command_adapter(tmp_path)
    calls, _ = _command_process(monkeypatch, executable)

    def authorize(*args):
        (root / "concurrent-input").write_text("changed\n", encoding="utf-8")
        return True

    monkeypatch.setattr(boundary, "authorize", authorize)
    with pytest.raises(PermissionError, match="changed during"):
        adapter.apply(adapter.plan, "adoption", adapter.plan.key("adoption"))
    assert calls == []


@pytest.mark.parametrize("deadline", [True, 0, -1, float("nan"), float("inf"), "2", None])
def test_command_adapter_rejects_invalid_deadline(tmp_path, deadline):
    with pytest.raises(ValueError, match="deadline"):
        _command_adapter(tmp_path, timeout_seconds=deadline)


def test_command_adapter_rejects_relative_executable(tmp_path):
    with pytest.raises(ValueError, match="absolute"):
        _command_adapter(tmp_path, goal_executable="goal")


def test_command_adapter_nonzero_requires_external_readback(tmp_path, monkeypatch):
    adapter, boundary, _, _, executable = _command_adapter(tmp_path)
    _command_process(monkeypatch, executable, returncode=7)
    key = adapter.plan.key("adoption")
    with pytest.raises(RuntimeError, match="exited 7; external readback"):
        adapter.apply(adapter.plan, "adoption", key)
    assert adapter.observe(adapter.plan, "adoption", key) is boundary.observation


@pytest.mark.parametrize("interrupted", [False, True])
def test_command_adapter_timeout_or_interrupt_kills_group(tmp_path, monkeypatch, interrupted):
    import os
    import signal
    import subprocess

    adapter, boundary, _, _, executable = _command_adapter(tmp_path)
    failure = KeyboardInterrupt() if interrupted else subprocess.TimeoutExpired("fixture", 2)
    _, waits = _command_process(monkeypatch, executable, failure=failure)
    killed = []
    monkeypatch.setattr(os, "killpg", lambda pid, sig: killed.append((pid, sig)))
    key = adapter.plan.key("adoption")
    with pytest.raises(type(failure)):
        adapter.apply(adapter.plan, "adoption", key)
    assert killed == [(123456789, signal.SIGKILL)]
    assert waits == [2, "reaped"]
    assert adapter.observe(adapter.plan, "adoption", key) is boundary.observation


def test_command_adapter_reuses_real_adopt_generator_path(tmp_path, monkeypatch):
    import json
    import subprocess
    from pathlib import Path
    from click.testing import CliRunner
    from goal.cli import governance_cmd

    adapter, boundary, root, _, executable = _command_adapter(tmp_path)
    original = subprocess.Popen
    invocations = []

    def checkout(repository, revision, destination, allow_unpublished_for_testing=False):
        assert repository == "https://github.com/wellmanifest/new-project.git"
        assert revision == adapter.plan.to_revision
        assert allow_unpublished_for_testing is False
        scripts = Path(destination) / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "create_adoption_lock.py").write_text(
            "import argparse, json\nfrom pathlib import Path\n"
            "p=argparse.ArgumentParser()\n"
            "p.add_argument('--target-root', required=True)\n"
            "p.add_argument('--source-revision', required=True)\n"
            "p.add_argument('--upgrade', action='store_true')\n"
            "a=p.parse_args()\n"
            "(Path(a.target_root)/'adapter-effect.json').write_text(json.dumps(vars(a)))\n",
            encoding="utf-8",
        )

    class InlineCommand:
        returncode = None

        def __init__(self, argv):
            self.argv = argv

        def communicate(self, *, timeout):
            assert timeout == 2
            result = CliRunner().invoke(governance_cmd.adopt, self.argv[3:])
            assert result.exception is None, result.output
            self.returncode = result.exit_code
            return None, None

    def spawn(argv, *args, **kwargs):
        if argv[0] == str(executable):
            invocations.append(argv)
            return InlineCommand(argv)
        return original(argv, *args, **kwargs)

    monkeypatch.setattr(governance_cmd, "_checkout_standard", checkout)
    monkeypatch.setattr(subprocess, "Popen", spawn)
    key = adapter.plan.key("adoption")
    adapter.apply(adapter.plan, "adoption", key)
    assert len(invocations) == 1
    assert json.loads((root / "adapter-effect.json").read_text()) == {
        "target_root": str(root), "source_revision": adapter.plan.to_revision,
        "upgrade": True,
    }
    assert adapter.observe(adapter.plan, "adoption", key) is boundary.observation
