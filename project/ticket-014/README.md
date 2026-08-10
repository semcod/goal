# Ticket 014: Fetch legacy governance base during upgrade

- **ID**: ticket-014
- **Owner**: session user (identity unresolved)
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10
- **Work classification**: `BUG / application`

## Goal and scope

Make `goal governance adopt` fetch the previously installed immutable standard
revision into its temporary checkout before running an upgrade generator.  A
depth-one checkout of only the requested revision cannot reconstruct the
trusted legacy manifest base and currently makes 0.11.0→0.14.0 upgrades fail.

## Acceptance criteria

- [x] AC-01: The user authorized the dependency/governance update that exposed
  this deterministic blocker.
- [ ] AC-02: A valid prior `sourceRevision` is fetched from the same configured
  standard repository before generator execution.
- [ ] AC-03: Invalid or missing target lock metadata cannot inject arbitrary Git
  arguments and preserves the existing fresh-adoption behavior.
- [ ] AC-04: Regression tests cover fresh adoption, check mode and a legacy
  upgrade requiring the prior revision.
- [ ] AC-05: Full tests and governance pass; the real 0.11.0→0.14.0 check
  proceeds past legacy-base resolution.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

The failure was discovered while executing the user's approved instruction to
update dependencies, test and publish.  The correction is the narrowest safe
way to complete that request and is approved for `IN_PROGRESS / EDIT`.

## Boundary

Only the adoption command and its regression tests may change outside ticket
evidence.  Fetching is restricted to a full lowercase commit SHA read from the
target's installed governance lock and uses the already configured standard
remote; it must not weaken exact requested-revision verification.
