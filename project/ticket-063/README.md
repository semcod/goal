# Ticket 063: Re-exec CLI after pip self-update

- **ID**: ticket-063
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-16

## Goal and scope

After a successful pip self-update, Goal must re-exec into the refreshed
package so lazy imports cannot mix a new `goal` tree with an old `goal.cli`
module. Keep the behavior guarded and test-covered.

## Acceptance criteria

- [x] AC-01: Session request to finish the unbound push records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded defect.
- [x] AC-02: Successful self-update sets a one-shot guard and re-executes via
  `python -m goal` with the original argv.
- [x] AC-03: Focused CLI tests cover the re-exec path.
- [ ] AC-04: Governed delivery publishes the bound commit without hook bypass.

## Boundary

- Touch only the CLI self-update re-exec path and its tests.
- Do not publish Goal 2.1.300 or modify ticket-061 release carriers.
- Distinct workstream from ticket-061 (`application` vs `integration`).

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
