# Ticket 238: Prepare frozen source-hub PRs for protected CI verification

- **ID**: ticket-238
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-12

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: continue and request protected merge under
https://github.com/semcod/goal/issues/241. Five source/test paths in intent.json.
Frozen standard430 is a consumer, not this ticket's writer scope.

## Acceptance criteria

- [x] AC-01: Explicit strategy refuses unsafe candidates, preserves defaults and pending semantics; meaningful regression tests pass.
- [x] AC-02: Full Goal tests and managed governance pass without source-health cache fabrication. Actual admitted run: 1303 passed, 2 skipped; governance 0 errors/warnings; source content unchanged.
- [ ] AC-03: Frozen Goal source is published through OneDev and independently approved/merged by the Validator.
