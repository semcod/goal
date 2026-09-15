# Ticket 114: Prevent post-merge CI governance failures on integrated ticket history

- **ID**: ticket-114
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-15

## Goal and scope

The post-merge `push` run of Goal's CI must validate the already integrated
tree without treating the merged ticket as a new active implementation. The
pull-request run keeps comparing the candidate against its PR base and keeps
the active-ticket governance gate. Only the CI base-selection expression is
changed; required checks, branch protection and PR validation remain intact.

The regression was observed after ticket-113: PR checks passed, but the
post-merge run compared `main` with the pre-merge SHA and failed with
`GOV-TICKET-001` because the ticket was terminal by ancestry. A push run uses
the current commit as its governance base, so it still validates the complete
integrated tree without requiring a ticket reservation that has already been
released.

## Acceptance criteria

- [x] AC-01: Scope is approved by the user's continuation request and recorded
  as `SESSION_EXECUTION_AUTHORIZATION` below.
- [x] AC-02: Pull-request CI continues to pass the PR base SHA, while push CI
  uses the current commit as its governance base.
- [x] AC-03: The merged-tree governance regression is covered by an automated
  test, and the managed governance, full test and Compose checks pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

SESSION_EXECUTION_AUTHORIZATION: the user requested continuation of the
unfinished delivery work, including fixing the observed post-merge CI failure
through the declared review and merge process. No self-approval or direct
merge.

## Validation evidence

- Reproduced the post-merge failure in CI run `34946118375`: the old
  `github.event.before` base caused `GOV-TICKET-001` after ticket-113 was
  terminal by ancestry.
- The static CI regression tests pass (`16 passed`), including the exact
  pull-request and push base expression.
- Push-mode simulation with `WELLMANIFEST_BASE_SHA=HEAD` passes `898 tests`
  with `2 skipped`; managed governance passes with zero errors and warnings.
- `docker compose config --quiet` and workflow YAML parsing pass.
