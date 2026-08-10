---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-013
---
# Participant: codex (AI agent)

## Understanding

Goal still carries immutable governance 0.11.0. Its manifest has no owner for
the checked-in integration container or Python lockfile. Published standard
0.14.0 supports target-owned manifest extensions, but the Goal adapter must
first learn to fetch the prior pinned base revision.

## Execution plan

1. Wait for ticket 014 and verify its upgrade regression.
2. Adopt published new-project 0.14.0 by full SHA using Goal.
3. Extend the integration workstream with `integration/**`, `uv.lock` and
   standard Python lockfile names without removing managed values.
4. Re-run adoption check and governance validation, then release ticket 012.

## Actual changes

- Scope and immutable source revision recorded; no implementation yet.

## Blockers

- Blocked on ticket 014's legacy-base fetch correction.
