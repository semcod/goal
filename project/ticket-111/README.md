# Ticket 111: Emit governance remediation proposals for Koru

- **ID**: ticket-111
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-14

## Goal and scope

When a governed `goal -a` run fails, publish a strict Planfile ticket proposal
for the diagnostic codes present in the target-owned diagnostics catalog. Store
the proposal under the target's ignored Koru runtime area and hand it to the
explicit `koru goal-remediation` CLI boundary when that executable is
available. Preserve the original non-zero Goal result and never let delegation
weaken the governance gate.

## Acceptance criteria

- [x] AC-01: A published governance diagnostic produces a canonical,
  deduplicated `planfile.ticket-proposal.v1` JSON artifact.
- [x] AC-02: Goal invokes Koru without a shell, reports delegation evidence,
  and keeps the original governance failure as the command result.
- [x] AC-03: Unknown or unpublished diagnostics do not create proposals;
  existing user files and governance output remain untouched.
- [x] AC-04: Focused tests, Ruff, the managed governance check, stack checks
  and Docker Compose validation pass.

## Authorization

`SESSION_EXECUTION_AUTHORIZATION`: the user explicitly requested autonomous
implementation and testing of Goal-to-Planfile-to-Koru remediation.

## Validation evidence

Goal full suite: 778 passed, 2 skipped. Focused producer and delivery suite:
73 passed. Ruff, `./project/governance-check.sh`, Docker Compose configuration,
compileall and `git diff --check` pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
