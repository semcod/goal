# Ticket 032: Expose packaged governance check through Goal

- **ID**: ticket-032
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-11

## Goal and scope

Expose the deterministic validator adopted from `wellmanifest/new-project`
through a stable `goal governance check` command. Goal owns invocation,
argument forwarding and failure behavior; the pinned target repository package
remains the source of validator code and policy data.

## Acceptance criteria

- [x] AC-01: The user's instruction that `new-project` use Goal supplies
  bounded execution authorization for this adapter.
- [ ] AC-02: `goal governance check` invokes the target's adopted validator
  with its manifest, lock and stack profiles.
- [ ] AC-03: Validator arguments, stdout, stderr and nonzero exit status are
  preserved without Goal reimplementing policy decisions.
- [ ] AC-04: Missing or incomplete adopted governance fails closed with an
  actionable diagnostic.
- [ ] AC-05: Focused and full tests, changed-file Ruff, governance, package
  build and Docker validation pass.

## Boundary

This ticket adds only the Goal-side runtime adapter and its regression tests.
It does not edit the canonical standard, adoption payload, validator rules,
delivery policy, dependency manifests or release metadata. The subsequent
`new-project` wrapper migration is a separate repository-local ticket.

## Session authorization

The user's direct instruction to continue and route `new-project` through Goal
creates `SESSION_EXECUTION_AUTHORIZATION` for this bounded local change. Push,
pull-request creation, merge and publication remain outside this authorization.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
