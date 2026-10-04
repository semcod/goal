# Ticket 183: Run discovered module tests at their manifest roots

- **ID**: ticket-183
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-04

## Goal and scope

Fix semcod/goal#183 in the declared CLI/test paths. SESSION_EXECUTION_AUTHORIZATION: user requests to continue, repair, test and merge authorize bounded implementation and protected publication.

## Acceptance criteria

- [ ] AC-01: Required nested module tests use actual manifest directories, appropriate JVM tools, preserve explicit root strategies, exclude external checkouts/dependencies and propagate failures. Focused/full tests, governance, Docker and protected exact-head approval pass before merge.

## Allocation recovery

Native new-ticket.sh allocated this ID and completed its scoped intent; optional index rendering failed due ENOSPC. Preserve that actual allocation and continue in the managed canonical relative worktree. No second ID or foreign data cleanup.
