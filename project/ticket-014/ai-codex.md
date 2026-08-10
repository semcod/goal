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

1. Reproduce the upgrade failure without writes.
2. Test the shallow-history hypothesis in an isolated worktree.
3. Cancel Goal-side implementation when the experiment disproves it and route
   the fix to `wellmanifest/new-project`.

## Actual changes

- Built a focused experimental adapter/test diff in an isolated worktree.
- Proved that making the previous commit available advances the generator but
  then fails because it compares Goal with the wrong historical base.
- Removed the uncommitted experimental worktree and branch; Goal source and
  tests remain unchanged.

## Blockers

- Correct repair depends on a new published `wellmanifest/new-project` patch.
