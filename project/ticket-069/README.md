# Ticket 069: Check adopted governance before legacy push side effects

- **ID**: ticket-069
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-05

## Goal and scope

Run the adopted governance gate before push side effects when goal.yaml has no
explicit delivery policy. Surface canonical diagnostics directly, before pytest.
Publish the validated fix through Goal and protected review.

## Acceptance criteria

- [x] AC-01: Invalid adopted governance blocks bootstrap and version/test work.
- [x] AC-02: Ordinary repositories preserve their existing workflow.
- [x] AC-03: Valid adopted repositories pass and malformed adoption fails closed.
- [ ] AC-04: Focused/full tests, governance, Docker and protected publication pass.
