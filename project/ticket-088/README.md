# Ticket 088: Bind CI governance to the pushed commit range

- **ID**: ticket-088
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-06

## Authorization and diagnosis

SESSION_EXECUTION_AUTHORIZATION: continue repairs and publish all changes. Main CI run 34028157956 fails before collecting tests with GOV-SYNC-001, including on retry. Without a PR event base, the pytest plugin compares HEAD to origin/main (the same SHA), so no changed ticket restricts historical adoption records. The PR suite passed because its event included a real base SHA.

## Acceptance criteria

- [x] AC-01: PR and push CI use the event's real base through the existing plugin interface, preserving all governance and test gates.
- [ ] AC-02: Exact-head protected review merges the workflow repair and main CI succeeds.

## Validation

The existing plugin honors the explicit push base and identifies the delivered ticket. Local managed governance and Docker Compose configuration pass. Full tests and exact-head CI validate this unchanged suite; post-merge CI is the acceptance readback.
