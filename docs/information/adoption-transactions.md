---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "adoption-transactions",
  "kind": "information",
  "version": 1,
  "title": "Resumable adoption transactions",
  "status": "proposed",
  "owner": "semcod/goal",
  "created": "2026-09-14",
  "updated": "2026-09-14",
  "review_after": "2026-09-21",
  "source_revision": "fabdc0c143c012f56e0f2ec1d009a07fadf7ff16",
  "affected_repositories": ["semcod/goal"],
  "evidence": ["project/ticket-107/intent.json"]
}
---

# Resumable adoption transactions

<!-- docs:section purpose -->
## Purpose

The Python controller in goal/governance/adoption_transaction.py is a
single-host pilot for resuming adoption, validation, publication and merge
through trusted existing adapters. It does not implement those external
operations or claim that any consumer has been upgraded.

<!-- docs:section scope -->
## Scope and ownership

Integration ticket-107 owns the controller, its fixtures and this document.
Ticket-106 registered the exact new source and test paths in the local
manifest through independently merged Goal PR151. The original unpublished
implementation was preserved and handed over without changing its source.
The private progress journal is an explicit integration data contract.

<!-- docs:section content -->
## Subject and adapter boundary

AdoptionPlan binds the repository, ticket, accepted base SHA, old and new
immutable standard revisions, profile digest and scope digest. Its canonical
digest determines the transaction identity and stable per-phase effect keys.
Changing any binding does not authorize reuse of the previous transaction.

An AdoptionAdapter provides observe, authorize and apply. Installed trusted
adapters, not commands supplied by a plan or log, implement this boundary.
Observe must independently check exact subject bindings, provenance and
freshness. NOT_APPLIED means authoritative absence, not an empty search in
an eventually consistent service. UNKNOWN never permits blind retry.
Authorize checks current scope, lease/fencing, freeze and protected permission
before each effect. Apply must honor the stable idempotency key.
The merge adapter must invoke the independent protected Validator; it must
not approve or directly merge its own candidate.

## Local durability and concurrency

The local goal.adoption-transaction/v1 journal is progress data, not a
registered Wellmanifest receipt, signed attestation or cached authorization.
The controller uses a bounded journal, a nonblocking POSIX file lock,
revision CAS, atomic replacement and file/directory fsync. It rejects invalid
or mismatched state rather than silently replacing it with an empty journal.

An advance performs at most one phase effect. It observes already completed
phases again before progressing, persists a started phase before invoking
an effect and requires subsequent readback. A crash after an effect can
therefore resume by observation rather than duplicate execution. An uncertain
outcome remains uncertain; only authoritative absence permits a bounded retry
with the same key. Stored PASS is never sufficient permission to continue.

## Existing mechanisms to reuse

The accepted ticket-105 planner in goal/governance/adoption_plan.py is the
starting point for immutable adoption planning. Future live integration must
reuse that planner and Goal's existing governance adopt operation, protected
publication and independent Validator instead of creating a second publisher.
The adapter contract alone does not prove these integrations are deployed.

<!-- docs:section evidence -->
## Validation evidence

The controller fixtures are tests/test_adoption_transaction.py. They cover
phase progression, restart and timeout readback, duplicate effects, stale CAS,
changed subjects, missing authority, corrupt journals and local writer
exclusion. Existing planner and delivery regressions remain in scope.
Actual commands, interpreter, results and source SHA belong in the external
validation and publication receipts for ticket-107. This document does not
assert that a pending candidate has passed tests or reached production.

<!-- docs:section limitations -->
## Limits

The pilot is single-host cooperative, not a distributed lock. Its fixture
adapters are not production integrations. No live consumer upgrade, automatic
fleet rollout, production scheduler, platform-wide guarantee or Taskand
runtime deployment is delivered here. Unknown outcomes can require operator
reconciliation. Preserving a journal does not prove recovery of consumer data.

<!-- docs:section next_actions -->
## Next steps and rollback

After independent acceptance, add bounded live adapters in separately scoped
work. Resolve supported immutable pins, current authority, dependency setup,
consumer isolation and rollback before the first live migration. Exercise a
controlled canary before deployment. Do not broaden limits to make it pass.

To stop using this pilot, do not activate the module and retain the previously
accepted Goal runtime. Preserve any private journals for reconciliation; do
not delete uncertain transaction state or replay effects to simulate rollback.
