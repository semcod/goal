# Ticket 083: Avoid configuration mutation before governed validation

- **ID**: ticket-083
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

A clean Performance checkout without goal.yaml became dirty before Goal ran governance.

- [x] AC-01: Governed all-flags startup preserves missing and existing configuration; ungoverned bootstrap remains available.
- [x] AC-02: Real goal -a returns no-change without new files.
