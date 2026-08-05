# Ticket 004: Governance scanner compatibility cleanup

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-05
- **Workstream**: application
- **Depends on**: ticket-001
- **Response required from**: none

## Goal and scope

Remove false-positive secret assignments caused by local variable names in the
OpenRouter bootstrap path. Preserve behavior and public interfaces.

## Planned changes

1. Rename three local result variables without changing values or control flow.
2. Validate the application-owned path explicitly through the governance gate.

## Acceptance criteria

- [x] AC-01: The scanner no longer treats function-return assignments as
  embedded credentials.
- [x] AC-02: OpenRouter lookup and validation behavior is unchanged.
- [x] AC-03: No credential value is logged or added to the repository.

## Participants

- Human participant: scope approved through the 2026-08-05 continuation.
- Agent participant: [`ai-codex.md`](ai-codex.md).
