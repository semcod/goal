# Ticket 066: Adopt new-project v0.20.4 automatic updates

- **ID**: ticket-066
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Adopt the exact published `wellmanifest/new-project` v0.20.4 package so Goal
itself installs the managed pre-commit standard-update controller, diagnostic
catalog and update policy required for fleet rollout.

## Acceptance criteria

- [x] AC-01: The staged intent binds the current and target immutable standard
  revisions in the governance workstream.
- [ ] AC-02: The published adoption generator updates only its managed payload
  and the ticket-owned governance records.
- [ ] AC-03: Governance, standard drift, Python tests and Docker validation
  pass on the adopted result.

## Authorization

`SESSION_EXECUTION_AUTHORIZATION`: the user explicitly requested autonomous
implementation, deployment and testing of automatic Wellmanifest updates in
all repositories that use the standards.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
