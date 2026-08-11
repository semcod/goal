# Ticket 033: Migrate legacy development dependency markers

- **ID**: ticket-033
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-11

## Goal and scope

Upgrade dependency specifications previously injected by Goal before Python
markers were introduced. Existing unmarked `goal`, `costs` and `pfix` entries
must gain the same interpreter guards as newly generated entries, without
duplicating dependencies or changing unrelated project metadata.

## Acceptance criteria

- [x] AC-01: The user's instruction to continue repairing Goal supplies
  bounded local execution authorization.
- [ ] AC-02: Legacy unmarked Goal tool requirements are migrated to their
  supported Python floors.
- [ ] AC-03: Already marked files remain byte-for-byte idempotent.
- [ ] AC-04: Focused/full tests, Ruff, governance, build and Docker pass.

## Session authorization

The request to continue and fix the live Goal regressions is
`SESSION_EXECUTION_AUTHORIZATION` for this local ticket. Push, merge,
publication, dependency release and global installation remain excluded.

## Boundary

This ticket owns only the dependency-text migration helper and its focused
tests. It does not change dependency versions, package metadata, version
selection, delivery code or the canonical governance standard.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
