"""Single-host adoption orchestration; trusted adapters retain all authority.

This pilot does not implement a migrator, publisher, lease backend or verifier.
Every adapter observation must revalidate the exact subject and its evidence.
NOT_APPLIED means authoritative absence, not an empty eventually consistent list.
"""

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


PHASES = ("adoption", "validation", "publication", "merge")
MAX_ATTEMPTS = 2
MAX_STATE_BYTES = 65536
SCHEMA = "goal.adoption-transaction/v1"


class TransactionError(RuntimeError):
    """Stable diagnostic; never contains raw adapter output or credentials."""


def _matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


@dataclass(frozen=True)
class AdoptionPlan:
    repository: str
    ticket: str
    base_sha: str
    from_revision: str
    to_revision: str
    profile_digest: str
    scope_digest: str

    def __post_init__(self):
        if not _matches(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repository):
            raise TransactionError("INVALID_REPOSITORY")
        if not _matches(r"ticket-[0-9]{3,}", self.ticket):
            raise TransactionError("INVALID_TICKET")
        if not all(_matches(r"[0-9a-f]{40}", value) for value in (
            self.base_sha, self.from_revision, self.to_revision
        )):
            raise TransactionError("IMMUTABLE_REVISION_REQUIRED")
        if not all(_matches(r"[0-9a-f]{64}", value) for value in (
            self.profile_digest, self.scope_digest
        )):
            raise TransactionError("INVALID_DIGEST")
        if self.from_revision == self.to_revision:
            raise TransactionError("NO_MIGRATION_REQUIRED")

    @property
    def digest(self):
        return hashlib.sha256(_encoded(asdict(self))).hexdigest()

    def key(self, phase):
        if phase not in PHASES:
            raise TransactionError("INVALID_PHASE")
        return hashlib.sha256(f"{self.digest}:{phase}".encode()).hexdigest()


@dataclass(frozen=True)
class Observation:
    status: str
    plan_digest: str
    idempotency_key: str
    receipt: str | None = None


class AdoptionAdapter(Protocol):
    """Installed trusted code, never commands supplied by a plan or log.

    observe verifies receipt provenance, exact subject and freshness. Completed
    earlier phases must remain valid for the current downstream subject.
    authorize rechecks lease/fencing, scope, freeze and protected permissions.
    apply must honor the stable key at the actual effect boundary. Merge always
    delegates to the existing independent protected Validator, never Git merge.
    """

    def observe(self, plan: AdoptionPlan, phase: str, key: str) -> Observation: ...
    def authorize(self, plan: AdoptionPlan, phase: str, key: str) -> bool: ...
    def apply(self, plan: AdoptionPlan, phase: str, key: str) -> None: ...


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TransactionError("INVALID_STATE")
        result[key] = value
    return result


class AdoptionTransaction:
    """Durable bounded journal in a caller-owned private directory on POSIX.

    One advance performs at most one effect. This cooperative lock is not a
    distributed lease or an authorization boundary against malicious local users.
    """

    def __init__(self, path):
        self.path = Path(path).absolute()

    @contextmanager
    def _locked(self):
        if os.name != "posix":
            raise TransactionError("UNSUPPORTED_LOCAL_LOCK_BACKEND")
        import fcntl

        for part in (self.path, *self.path.parents):
            if part.is_symlink():
                raise TransactionError("SYMLINK_STATE_PATH")
        if not self.path.parent.is_dir():
            raise TransactionError("PRIVATE_STATE_DIRECTORY_REQUIRED")
        lock = self.path.with_name(self.path.name + ".lock")
        fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise TransactionError("TRANSACTION_BUSY") from error
            yield
        finally:
            os.close(fd)

    def _load(self, plan):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            return {
                "schema": SCHEMA, "plan": asdict(plan), "digest": plan.digest,
                "revision": 0, "last_result": None,
                "steps": [{"phase": phase, "state": "pending", "attempts": 0,
                           "receipt": None} for phase in PHASES],
            }
        try:
            with os.fdopen(fd, "rb") as stream:
                raw = stream.read(MAX_STATE_BYTES + 1)
            if len(raw) > MAX_STATE_BYTES:
                raise TransactionError("STATE_TOO_LARGE")
            state = json.loads(raw, object_pairs_hook=_unique_object)
            if not isinstance(state, dict) or set(state) != {
                "schema", "plan", "digest", "revision", "last_result", "steps"
            } or state["schema"] != SCHEMA:
                raise TransactionError("INVALID_STATE")
            if state["plan"] != asdict(plan) or state["digest"] != plan.digest:
                raise TransactionError("PLAN_MISMATCH")
            if type(state["revision"]) is not int or state["revision"] < 0:
                raise TransactionError("INVALID_STATE")
            if not isinstance(state["steps"], list) or len(state["steps"]) != len(PHASES):
                raise TransactionError("INVALID_STATE")
            incomplete = False
            for phase, step in zip(PHASES, state["steps"]):
                if not isinstance(step, dict) or set(step) != {
                    "phase", "state", "attempts", "receipt"
                } or step["phase"] != phase or step["state"] not in (
                    "pending", "started", "outcome_unknown", "complete"
                ):
                    raise TransactionError("INVALID_STATE")
                if type(step["attempts"]) is not int or not 0 <= step["attempts"] <= MAX_ATTEMPTS:
                    raise TransactionError("INVALID_STATE")
                if step["state"] == "complete":
                    if incomplete or not _matches(r"sha256:[0-9a-f]{64}", step["receipt"]):
                        raise TransactionError("INVALID_STATE")
                else:
                    incomplete = True
                    if step["receipt"] is not None:
                        raise TransactionError("INVALID_STATE")
            result = state["last_result"]
            if result is not None and (
                not isinstance(result, dict) or set(result) != {"status", "phase", "reason"}
                or result["status"] not in ("BLOCKED", "PROGRESSED", "COMPLETE")
                or result["phase"] not in (*PHASES, None)
                or not _matches(r"[A-Z_]{1,64}", result["reason"])
            ):
                raise TransactionError("INVALID_STATE")
            return state
        except (ValueError, TypeError, KeyError) as error:
            raise TransactionError("INVALID_STATE") from error

    def _save(self, state):
        state["revision"] += 1
        raw = _encoded(state)
        if len(raw) > MAX_STATE_BYTES:
            raise TransactionError("STATE_TOO_LARGE")
        fd, temporary = tempfile.mkstemp(prefix=".adoption-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def read(self, plan):
        """Return stored progress only, never current readiness or permission."""
        with self._locked():
            return self._load(plan)

    def _finish(self, state, status, phase, reason):
        state["last_result"] = {"status": status, "phase": phase, "reason": reason}
        self._save(state)
        return {**state["last_result"], "revision": state["revision"],
                "plan_digest": state["digest"]}

    @staticmethod
    def _observe(adapter, plan, phase):
        try:
            observed = adapter.observe(plan, phase, plan.key(phase))
        except Exception:
            return None
        if not isinstance(observed, Observation) or observed.status not in (
            "APPLIED", "NOT_APPLIED", "UNKNOWN", "INVALID"
        ) or observed.plan_digest != plan.digest or observed.idempotency_key != plan.key(phase):
            return None
        if observed.status == "APPLIED" and not _matches(r"sha256:[0-9a-f]{64}", observed.receipt):
            return None
        return observed

    def advance(self, plan, adapter, *, expected_revision):
        with self._locked():
            state = self._load(plan)
            if type(expected_revision) is not int or state["revision"] != expected_revision:
                raise TransactionError("STALE_REVISION")
            for index, step in enumerate(state["steps"]):
                phase = step["phase"]
                observed = self._observe(adapter, plan, phase)
                if observed is None:
                    return self._finish(state, "BLOCKED", phase, "READBACK_UNAVAILABLE")
                if step["state"] == "complete":
                    if observed.status != "APPLIED":
                        return self._finish(state, "BLOCKED", phase, "EVIDENCE_STALE")
                    step["receipt"] = observed.receipt
                    continue
                if observed.status in ("UNKNOWN", "INVALID"):
                    return self._finish(state, "BLOCKED", phase, "OUTCOME_UNKNOWN")
                if observed.status == "NOT_APPLIED":
                    if step["attempts"] >= MAX_ATTEMPTS:
                        return self._finish(state, "BLOCKED", phase, "RETRY_LIMIT")
                    try:
                        authorized = adapter.authorize(plan, phase, plan.key(phase))
                    except Exception:
                        return self._finish(state, "BLOCKED", phase, "AUTHORITY_UNAVAILABLE")
                    if authorized is not True:
                        return self._finish(state, "BLOCKED", phase, "AUTHORITY_REQUIRED")
                    step["state"] = "started"
                    step["attempts"] += 1
                    self._save(state)
                    try:
                        adapter.apply(plan, phase, plan.key(phase))
                    except Exception:
                        step["state"] = "outcome_unknown"
                        return self._finish(state, "BLOCKED", phase, "OUTCOME_UNKNOWN")
                    observed = self._observe(adapter, plan, phase)
                    if observed is None or observed.status != "APPLIED":
                        step["state"] = "outcome_unknown"
                        return self._finish(state, "BLOCKED", phase, "OUTCOME_UNKNOWN")
                step["state"] = "complete"
                step["receipt"] = observed.receipt
                status = "COMPLETE" if index == len(PHASES) - 1 else "PROGRESSED"
                return self._finish(state, status, phase, "OBSERVED")
            return self._finish(state, "COMPLETE", None, "REVALIDATED")


def prepare_adoption_transaction(
    target_root,
    catalog_path,
    catalog_sha256,
    *,
    repository: str,
    ticket: str,
    profile_digest: str,
    scope_digest: str,
    target_revision: str | None = None,
) -> AdoptionPlan | None:
    """Prepare one advisory transaction from a freshly observed pinned plan.

    Return None when the existing pin should be retained. Blocked or multi-step
    plans require explicit remediation/staging, never a shortcut to the final
    revision. No adapter, journal, migration, publication or authority is invoked.

    The returned scope_digest is derived from the caller's declared scope digest
    and the full planner identity (including catalog, lock, HEAD and checkout).
    profile_digest is preserved unchanged. Callers must retain the planning
    inputs for independent adapter verification; neither digest grants trust.
    The existing transaction constructor and journal format remain unchanged.
    """
    from hashlib import sha256
    import json
    import re

    from goal.governance.adoption_plan import AdoptionPlanError, plan_adoption

    if not isinstance(scope_digest, str) or re.fullmatch(r"[0-9a-f]{64}", scope_digest) is None:
        raise AdoptionPlanError("scope SHA-256 must be 64 lowercase hex characters")
    proposal = plan_adoption(target_root, catalog_path, catalog_sha256, target_revision)
    if proposal["state"] == "retain":
        return None
    if proposal["state"] != "migration-planned":
        raise AdoptionPlanError(f"transaction preparation blocked: {proposal['reason']}")
    if len(proposal["steps"]) != 1:
        raise AdoptionPlanError("transaction requires exactly one migration step; staged replanning required")
    binding = {
        "domain": "goal.adoption-transaction-scope/v1",
        "declaredScopeSha256": scope_digest,
        "plannerPlanId": proposal["planId"],
    }
    bound_scope = sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    step = proposal["steps"][0]
    return AdoptionPlan(
        repository=repository,
        ticket=ticket,
        base_sha=proposal["headSha"],
        from_revision=step["fromRevision"],
        to_revision=step["toRevision"],
        profile_digest=profile_digest,
        scope_digest=bound_scope,
    )


class GoalAdoptionAdapter:
    """Run the existing Goal adoption CLI, not a second migration engine.

    The caller must resolve the executable/runtime and deadline from the trusted
    profile bound by ``profile_digest``. The delegate owns authoritative readback,
    fresh execution authority, and all non-adoption phases. Neither a zero exit
    code nor a changed lock is promoted to an APPLIED observation here.
    """

    def __init__(
        self, *, target_root, catalog_path, catalog_sha256, repository, ticket,
        profile_digest, scope_digest, goal_executable, timeout_seconds, delegate,
        target_revision=None,
    ):
        import math
        import os
        from pathlib import Path

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("adoption deadline must be finite and positive")
        executable = Path(goal_executable)
        if not executable.is_absolute():
            raise ValueError("Goal executable must be an absolute trusted path")
        executable = executable.resolve(strict=True)
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError("Goal executable must be an executable file")
        self._inputs = {
            "target_root": Path(target_root).resolve(strict=True),
            "catalog_path": Path(catalog_path).resolve(strict=True),
            "catalog_sha256": catalog_sha256,
            "repository": repository,
            "ticket": ticket,
            "profile_digest": profile_digest,
            "scope_digest": scope_digest,
            "target_revision": target_revision,
        }
        self._plan = prepare_adoption_transaction(**self._inputs)
        if self._plan is None:
            raise ValueError("retained standard requires no adoption adapter")
        self._executable = str(executable)
        self._timeout = timeout_seconds
        self._delegate = delegate

    @property
    def plan(self):
        """The immutable subject that the external boundary must authorize."""
        return self._plan

    def _require_subject(self, plan, phase, key):
        if (
            phase not in ("adoption", "validation", "publication", "merge")
            or plan != self._plan
            or key != self._plan.key(phase)
        ):
            raise ValueError("adoption adapter subject, phase or key mismatch")

    def _current_plan_matches(self):
        try:
            return prepare_adoption_transaction(**self._inputs) == self._plan
        except (ValueError, OSError):
            return False

    def observe(self, plan, phase, key):
        self._require_subject(plan, phase, key)
        return self._delegate.observe(plan, phase, key)

    def authorize(self, plan, phase, key):
        self._require_subject(plan, phase, key)
        if phase == "adoption" and not self._current_plan_matches():
            return False
        return self._delegate.authorize(plan, phase, key) is True

    def apply(self, plan, phase, key):
        import os
        import signal
        import subprocess

        # Keep direct callers fail-closed too; controller authorization is not a
        # reusable grant. The delegate still revalidates the actual writer lease.
        if not self.authorize(plan, phase, key):
            raise PermissionError("fresh adoption phase authority is required")
        if phase != "adoption":
            self._delegate.apply(plan, phase, key)
            return
        if not self._current_plan_matches():
            raise PermissionError("adoption inputs changed during authorization")
        argv = [
            self._executable, "governance", "adopt",
            "--standard-repository",
            "https://github.com/wellmanifest/new-project.git",
            "--source-revision", plan.to_revision,
            "--target-root", str(self._inputs["target_root"]), "--upgrade",
        ]
        process = subprocess.Popen(
            argv, cwd=self._inputs["target_root"], stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            process.communicate(timeout=self._timeout)
        except BaseException:
            # A timeout/interruption may follow a partial write. Kill the whole
            # command group and let the transaction journal require readback.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
        if process.returncode != 0:
            raise RuntimeError(
                f"Goal adoption exited {process.returncode}; external readback required"
            )
