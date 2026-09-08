# Ticket 091: Immutable pin and main import fix

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Owner**: codex

SESSION_EXECUTION_AUTHORIZATION: User requested continued Semcod publication. The existing hook blocks PR 124 pending standard freshness; its runbook requires a separate managed adoption ticket. Adopt the already published fix without bypassing the hook.

## Acceptance criteria
- [x] AC-01: Adopt immutable bf3099667babd14ee778917d911d6c6bad45dcab, retaining target settings and package bindings.
- [ ] AC-02: Managed checks and Python CI matrix pass before independent protected publication.

Validation: 723 tests passed, 2 skipped; managed governance and Docker Compose passed. Required Python matrix and independent publication remain pending.
