# Ticket 007: Repair OpenRouter environment validation

- **ID**: ticket-007
- **Owner**: unresolved:human
- **Status**: PLAN
- **Workflow state**: WAIT_FOR_APPROVAL
- **Created**: 2026-08-05
- **Work classification**: `SERVICE / health`

## Goal and scope

Repair the current-main `NameError` in `_validate_pfix_env` by validating the
already resolved `credential` value instead of the undefined legacy
`api_key` name. Preserve parent `.env` discovery and all credential boundaries.

## Acceptance criteria

- [ ] AC-01: Human approves this two-file SERVICE repair.
- [ ] AC-02: `_validate_pfix_env` checks the resolved credential without logging
  or copying its value.
- [ ] AC-03: Existing parent/blank-local environment tests pass on Python
  3.12 and 3.13.
- [ ] AC-04: Full Goal tests have no `api_key` NameError regression.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md).

## Boundary

This ticket does not change OpenRouter models, secret storage, provider calls,
governance adoption or delivery policy. It is the minimal prerequisite for the
already open governance adoption PR #16 to obtain a green baseline.
