# Ticket 036: Run adopted workspace lifecycle audit through Goal

- **ID**: ticket-036
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Expose the workspace lifecycle checker supplied by the pinned
`wellmanifest/new-project` package as `goal governance workspace-check`.
Goal only locates and executes adopted policy code; it does not duplicate the
policy and never deletes a worktree, clone or branch.

## Acceptance criteria

- [x] AC-01: The user's request authorizes this bounded local Goal adapter.
- [x] AC-02: The command requires an adopted checker and fails closed when it
  is missing.
- [x] AC-03: Workspace root, exact allowlisted paths and output format are
  forwarded without entering mutable interactive Goal setup.
- [x] AC-04: Checker stdout/stderr and exit status are preserved.
- [x] AC-05: Focused/full tests, Ruff and governance pass.

## Validation evidence

- 12 focused governance CLI tests pass, including exact forwarding, nonzero
  status preservation and missing-checker failure.
- The full suite reports 547 passed and 2 skipped.
- Changed-file Ruff and the deterministic governance gate pass.
- No cleanup, adoption, version change or external publication was performed.
- Local validation is complete; the ticket remains active until the reviewed
  branch is integrated and a governance-only closure is recorded on `main`.
- PR #61 passed Python 3.12/3.13 CI and was merged as
  `main@61f34b7400358247e56a7940336e5e43104b9d55`; its remote head branch was
  deleted automatically.

## Boundary

No deletion, adoption, publication, version change or policy implementation is
performed by this command. The adopted immutable package stays the source of
truth.
