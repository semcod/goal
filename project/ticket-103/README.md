# Ticket 103: Adopt git-ancestry ticket activity override

- **ID**: ticket-103
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-14

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: on 2026-09-14 the user asked to find what
blocks and slows code delivery to Git, decide whether Wellmanifest standards
or something else is the cause, create a plan and implement it.

Merged tickets stay `IN_PROGRESS` in their tracked README because closure is
recorded outside the repository. In a clone without the terminal-receipt
registry (every CI run) the managed resolver falls back to the status
projection and treats them as active: gates report stale bases and adoption
preconditions, and allocation reaches the workstream limit. The pinned
resolver already supports the target-owned `git-ancestry` policy: a ticket is
inactive when its directory is on `main` and no unmerged branch for it exists.

Measured in a fresh clone of `origin/main` on 2026-09-14: 36 tickets are
projected active without the override and 0 with it.

Non-goals: no managed payload, lock or manifest change; no ticket README
rewrite; open ticket branches stay active.

## Acceptance criteria

- [ ] AC-01: `.governance/ticket-activity.override.json` selects
  `missingPolicy: git-ancestry` and validates against the pinned schema.
- [ ] AC-02: In a fresh clone the resolver reports no active ticket whose
  delivery is on `main`; tickets with an unmerged branch remain active.
- [ ] AC-03: The governance gate passes on the exact head.

Plan and fleet evidence:
`subactor/docs/architecture/refactoring/delivery-flow-unblocking.md`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
