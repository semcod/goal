# Ticket 036: Run adopted workspace lifecycle audit through Goal

- **ID**: ticket-036
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Expose the workspace lifecycle checker supplied by the pinned
`wellmanifest/new-project` package as `goal governance workspace-check`.
Goal only locates and executes adopted policy code; it does not duplicate the
policy and never deletes a worktree, clone or branch.

## Acceptance criteria

- [x] AC-01: The user's request authorizes this bounded local Goal adapter.
- [ ] AC-02: The command requires an adopted checker and fails closed when it
  is missing.
- [ ] AC-03: Workspace root, exact allowlisted paths and output format are
  forwarded without entering mutable interactive Goal setup.
- [ ] AC-04: Checker stdout/stderr and exit status are preserved.
- [ ] AC-05: Focused/full tests, Ruff and governance pass.

## Boundary

No deletion, adoption, publication, version change or policy implementation is
performed by this command. The adopted immutable package stays the source of
truth.

