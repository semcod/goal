# Ticket 193: Keep clean governed main separate from unfinished branches

- **ID**: ticket-193
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-23

## Authorization and scope

SESSION_EXECUTION_AUTHORIZATION: user requests repair of Goal-a and continued
backlog tests and protected merge. PLF-023 now records the distinct governed
checkout-selection defect. Blocked192 covers a separate legacy CLI provenance
proposal; preserve it. The native allocator assigned193 after free-scope
preflight, then its scaffold was moved only into the managed canonical relative
checkout from independently merged origin/main. Primary dirty operational files
are preserved. Own delivery.py and its existing regression suite only.

## Acceptance criteria

- [x] AC-01: Clean synchronized default checkout is a no-op even with pending
  foreign branch tickets. Validate registry integrity, preserve all registry
  bytes/foreign refs, and retain explicit and undelivered-work behavior.
- [ ] AC-02: Native checks and original protected matrix pass; exact-head
  independent review and merge precede runtime installation.
- [ ] AC-03: Exact merged local immutable runtime is installed reversibly;
  actual clean Heyasa main returns no-change with033 still preserved.

## Evidence

Receipt namespace: receipt:goal193/clean-base-resolution.
No historical approval or terminal receipt is fabricated.

## Native validation

1000 tests pass,6 are skipped. Focused resolver coverage preserves foreign
branch refs and registry bytes, validates corrupt registry failure, explicit
tickets, dirty/ahead/nondefault state and unavailable remote transport. The
workflow-order regression prohibits bootstrap, commit, tag and publish effects
with a pending foreign ticket. Managed governance and Ruff0.15.11 pass.
The original protected matrix and exact-head Validator remain required before
merge and reversible local runtime installation.
