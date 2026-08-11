# Ticket 034: Recover adjacent registry-ahead versions in auto mode

- **ID**: ticket-034
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-11

## Goal and scope

Allow autonomous `goal -a` recovery when the package registry is exactly one
patch ahead of a uniform local version, as happened after an interrupted glon
release. Manual and non-adjacent regressions must continue to fail closed, and
the auto-mode permission must be forwarded through the real push workflow.

## Acceptance criteria

- [x] AC-01: The user's instruction to continue repairing the live Goal/glon
  failure supplies bounded local execution authorization.
- [x] AC-02: Auto mode advances from an adjacent registry baseline for release
  and synchronizes to it when no release is required.
- [x] AC-03: Manual mode, non-adjacent gaps and inconsistent local carriers
  remain rejected.
- [x] AC-04: The real push workflow enables the repair only for `goal -a`.
- [ ] AC-05: Focused/full tests, Ruff, governance, build and Docker pass.

## Validation evidence

- 63 focused resolver and push-workflow tests pass.
- The push regression runs both `all_flags=False` and `all_flags=True` and
  observes the exact resolver permission in both cases.
- Changed-file Ruff and deterministic governance pass.

## Session authorization

The request to continue and repair Goal is `SESSION_EXECUTION_AUTHORIZATION`
for this bounded local change. Push, merge, publication and release metadata
remain outside authorization.

## Boundary

This ticket owns the conservative adjacent-version decision and propagation of
the auto-mode flag. It does not weaken manual checks, accept minor/major gaps,
publish a package or change target repository metadata.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
