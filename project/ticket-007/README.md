# Ticket 007: Repair OpenRouter environment validation

- **ID**: ticket-007
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-05
- **Work classification**: `SERVICE / health`

## Goal and scope

Repair the current-main `NameError` in `_validate_pfix_env` by validating the
already resolved `credential` value instead of the undefined legacy
`api_key` name. Preserve parent `.env` discovery and all credential boundaries.

## Acceptance criteria

- [x] AC-01: Human approves this two-file SERVICE repair.
- [x] AC-02: `_validate_pfix_env` checks the resolved credential without logging
  or copying its value.
- [x] AC-03: Existing parent/blank-local environment tests pass on Python
  3.12 and 3.13.
- [x] AC-04: Full Goal tests have no `api_key` NameError regression.

## Validation evidence

- Focused `tests/test_project_bootstrap.py`: 71 passed.
- Full local suite: 477 passed, 2 skipped, 0 failed.
- `git diff --check`: PASS.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md).

## Boundary

This ticket does not change OpenRouter models, secret storage, provider calls,
governance adoption or delivery policy. It is the minimal prerequisite for the
already open governance adoption PR #16 to obtain a green baseline.

## Session authorization

The user approved ticket-007 and autonomous continuation on 2026-08-05. Merge
still requires exact-head publication evidence.
