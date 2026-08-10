# Ticket 013: Adopt governance ownership extensions

- **ID**: ticket-013
- **Owner**: session user (identity unresolved)
- **Status**: PLAN
- **Workflow state**: WAIT_FOR_EXTERNAL_RELEASE
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / governance`

## Goal and scope

Upgrade Goal's immutable `wellmanifest/new-project` adoption from published
0.11.0 to published 0.14.0 and install target-local ownership for
`integration/**` and Python lockfiles.  This unlocks ticket 012 without
weakening path enforcement or editing managed files outside the adoption tool.

## Acceptance criteria

- [x] AC-01: The user's dependency/runtime update request authorizes the
  necessary governance adoption identified by the deterministic gate.
- [ ] AC-02: Adoption uses the published full SHA behind `v0.14.0`.
- [ ] AC-03: Managed-file provenance and governance validation pass after the
  upgrade.
- [ ] AC-04: The integration workstream explicitly owns `integration/**` and
  Python lockfiles while all existing owned paths remain intact.
- [ ] AC-05: Ticket 012 can claim its final implementation paths.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Dependency and approval

The user's instruction to update, test and publish covers this prerequisite.
Ticket 014 disproved the Goal-adapter hypothesis; implementation now waits for
an upstream `wellmanifest/new-project` patch that migrates from the authenticated
legacy target manifest. Current published revision:
`a22eb47ca0e7c06ac927d1c0d843eabb798bfadd` (`v0.14.0`).

## Boundary

Only standard-managed governance artifacts, the target-owned manifest
extension, and this ticket's governance evidence may change.  The adoption
must be executed through `goal governance adopt`; no integrity check is
disabled or bypassed.
