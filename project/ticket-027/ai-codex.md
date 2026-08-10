---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-027
---
# Participant: codex (AI agent)

## Understanding

`gh pr view <branch>` selects a historical PR even when it is already merged.
The real Koru run proved the consequence: Goal successfully pushed a new
commit, reported success with the old PR URL and never created an open review
boundary for that commit. PR lookup is part of the delivery integrity
contract, so both state and exact HEAD must be checked.

## Execution plan

1. Replace unbounded PR lookup with an open base/head query.
2. Bind any reusable PR to the currently pushed commit and reject ambiguous
   or malformed responses.
3. Re-resolve a created PR instead of trusting command output alone.
4. Add regression tests for historical, reusable and stale-head cases.
5. Run focused/full tests, governance and Docker before governed delivery.

## Actual changes

- Initialized the bounded regression ticket and recorded the Koru #28/#29
  reproduction as evidence.
- Replaced unbounded `gh pr view <branch>` lookup with a filtered open
  base/head query that rejects ambiguity and malformed responses.
- Bound every reused PR to the current local/pushed commit through
  `headRefOid`; stale PR state now fails closed.
- Re-resolve and verify a newly created PR rather than trusting the create
  command's display output.
- Added three regression scenarios and passed 525 full-suite tests plus the
  production Docker smoke.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
