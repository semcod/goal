# Ticket 059: Align built-in Python publish commands

- **ID**: ticket-059
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Align every built-in Goal configuration producer with the retry-safe Twine
contract delivered by ticket-058. Fresh default configurations and the legacy
`pip` / `pipenv` package-manager descriptors must include exactly one
`--skip-existing`, so newly generated projects are safe before doctor or the
runtime boundary needs to repair them.

## Acceptance criteria

- [x] AC-01: The user's instruction to repair and continue records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded regression fix.
- [ ] AC-02: The default Python strategy emits the canonical retry-safe Twine
  command.
- [ ] AC-03: The `pip` and `pipenv` package-manager descriptors emit
  retry-safe Twine commands without changing non-Twine managers.
- [ ] AC-04: Focused/full tests, Ruff and governance pass before protected
  exact-head delivery.

## Non-goals

- Do not change runtime normalization or doctor migration from ticket-058.
- Do not edit governance-owned `goal.yaml`; that is a dependent ticket.
- Do not change versions, dependencies or public interfaces.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
