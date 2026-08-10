---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-014
---
# Participant: codex (AI agent)

## Understanding

The adoption generator intentionally derives an upgrade base from the
previously pinned standard SHA. Goal checks out only the new SHA with depth one,
so that trusted prior object is absent and the upgrade fails before any write.

## Execution plan

1. Commit this approved plan before source changes.
2. Add defensive prior-revision discovery from the target lock.
3. Fetch the validated prior SHA from the same standard remote and test the
   exact Git interaction plus end-to-end fake upgrade behavior.
4. Run focused and full suites, governance and the real 0.14.0 adoption check.

## Actual changes

- Approved plan recorded; implementation follows in an isolated worktree.

## Blockers

- None.
