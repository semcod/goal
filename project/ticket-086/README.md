# Ticket 086: Fetch complete history for governed CI

- **ID**: ticket-086
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

SESSION_EXECUTION_AUTHORIZATION: user requested pushing all changes. Resolve the observed CI publication blocker without changing accepted intent or weakening governance.

## Acceptance criteria

- [x] AC-01: CI checkout fetches complete history before running tests, preserving accepted-base resolution.
- [ ] AC-02: Managed governance and hosted Python 3.12/3.13 jobs pass before protected merge.
