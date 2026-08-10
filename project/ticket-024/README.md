# Ticket 024: Preserve dry-run state and fail closed on delivery errors

- **ID**: ticket-024
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10

## Goal and scope

Make dry-run observably read-only, make every failed Git push terminate the
delivery with a non-zero result, and preserve every declared Python test tool
set when Goal synchronizes an UV-managed environment.

## Acceptance criteria

- [x] AC-01: The user instructed the agent to continue the autonomous work.
- [ ] AC-02: A dry-run neither creates nor rewrites `goal.yaml`.
- [ ] AC-03: A failed non-governed push exits non-zero and cannot emit a
  successful workflow summary.
- [ ] AC-04: UV bootstrap/synchronization includes whichever of `dev` and
  `test` are declared, preventing removal of their verification tools.
- [ ] AC-05: Focused tests, full tests, governance and Docker checks pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

The user explicitly said to continue after these three Goal defects were
reported. This is `SESSION_EXECUTION_AUTHORIZATION` for the bounded paths in
`intent.json`; no additional implementation confirmation is required.

## Boundary

This ticket does not change version selection, registry credentials, release
ordering, GitHub protection, governance policy or public CLI syntax.
