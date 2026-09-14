# ticket-110: Restore adoption adapter before readback

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- Workstream: integration
- Agent: codex
- Owner: agent:codex-adoption-pilot

## Intent

Fix the constructor's assumption that a resumed transaction still has a clean
pre-adoption checkout. Restore the immutable subject before independent readback;
keep fresh planning and authority mandatory before another adoption write.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: the user explicitly approved this restart fix,
its regression tests and protected publication. Publication uses independent
exact-head review; this note is not approval evidence.

## Acceptance criteria

- AC-01: Interrupt a fixture command after a partial, complete or committed write;
  reopen its durable journal and reconstruct the adapter without duplicate adoption.
- AC-02: UNKNOWN cannot trigger a retry; foreign subjects and invalid bindings
  fail closed, and changed planning inputs cannot authorize a new adoption write.
- AC-03: Managed governance, focused and full stack checks pass before independent
  exact-head review and protected merge.

## Limits

No production migration, new receipt schema, automatic repair, cleanup, package
release or deployment. Saved transaction data never grants execution authority.
