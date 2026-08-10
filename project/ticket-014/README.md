# Ticket 014: Fetch legacy governance base during upgrade

- **ID**: ticket-014
- **Owner**: session user (identity unresolved)
- **Status**: CANCELLED
- **Workflow state**: CANCELLED
- **Created**: 2026-08-10
- **Work classification**: `BUG / application`

## Goal and scope

Make `goal governance adopt` fetch the previously installed immutable standard
revision into its temporary checkout before running an upgrade generator.  A
depth-one checkout of only the requested revision cannot reconstruct the
trusted legacy manifest base and currently makes 0.11.0→0.14.0 upgrades fail.

This initial hypothesis was disproved before any implementation commit.  The
prior revision is fetchable, but the 0.14.0 standard migrator incorrectly uses
the published default as the base instead of the exact legacy target manifest
already authenticated by its lock hash.  The repair belongs in
`wellmanifest/new-project`, not in Goal's transport adapter.

## Acceptance criteria

- [x] AC-01: The user authorized the dependency/governance update that exposed
  this deterministic blocker.
- [x] AC-02: A focused experiment proved that fetching the old object does not
  resolve the migration because the wrong legacy base is selected.
- [x] AC-03: No Goal implementation commit was created and the experimental
  worktree was removed.
- [x] AC-04: Ownership of the correction was routed to the standard source.
- [x] AC-05: This ticket was cancelled without modifying runtime code.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

The failure was discovered while executing the user's approved instruction to
update dependencies, test and publish.  Investigation was authorized, but the
proposed Goal-side correction was rejected once evidence located the defect in
the upstream standard.

## Boundary

Only the adoption command and its regression tests may change outside ticket
evidence.  Fetching is restricted to a full lowercase commit SHA read from the
target's installed governance lock and uses the already configured standard
remote; it must not weaken exact requested-revision verification.
