# Ticket 017: Assign release metadata to integration

- **ID**: ticket-017
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10

## Goal and scope

Extend Goal's target-owned integration workstream with the exact release
metadata paths updated atomically by `goal -a`: `VERSION`, `CHANGELOG.md`,
`README.md`, and `goal/__init__.py`. The integration workstream already owns
`pyproject.toml` and `uv.lock`; without the remaining paths, a valid version
sync is rejected as a cross-workstream diff.

## Acceptance criteria

- [x] AC-01: The user's autonomous test/publish request authorizes this narrow
  prerequisite without another confirmation.
- [ ] AC-02: Integration ownership includes the four missing release metadata
  paths and preserves all existing ownership.
- [ ] AC-03: Ticket 012 can validate one atomic Goal version-sync diff without
  a workstream ownership violation.
- [ ] AC-04: Managed provenance and governance validation pass with zero
  findings.

## Session authorization

This is a direct prerequisite of the already authorized ticket-012 publication
outcome. The agent may proceed in `EDIT`; exact-head merge approval remains an
independent protected action.

## Boundary

Only the target-owned manifest extension and ticket evidence may change. This
ticket does not edit source, version values, dependency manifests, lockfiles,
standard-managed base content, or GitHub policy.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
