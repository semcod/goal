# Ticket 069: Check adopted governance before legacy push side effects

- **ID**: ticket-069
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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

## Continued preflight repair

Resolve historical IN_PROGRESS projections through the managed activity resolver.
A clean base matching the authoritative remote with no active ticket exits without
bootstrap or publication. Dirty or unpublished work still requires ticket authority.

- [ ] AC-05: Terminal receipts govern ticket selection; invalid receipts fail closed.
- [ ] AC-06: Clean synchronized base exits successfully before workflow mutations.
