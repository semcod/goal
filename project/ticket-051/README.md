# Ticket 051: Prepare the managed branch lifecycle checker

- **ID**: ticket-051
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Install the exact branch-lifecycle checker from published `new-project
v0.16.1` as the governance-owned prerequisite for its managed GitHub workflow.
This deliberately separates the governance-owned executable from the later
infrastructure-owned workflow and from the final full package adoption, so
every changed path has exactly one workstream owner.

## Acceptance criteria

- [x] AC-01: `.governance/branch_lifecycle_check.py` is byte-identical to
      `wellmanifest/new-project@4e6ba5ec...` and its SHA-256 is recorded.
- [x] AC-02: Focused positive, orphan-branch and malformed-snapshot probes pass.
- [ ] AC-03: Full Goal tests and deterministic governance pass before a
      protected PR; Python 3.12/3.13 CI and exact-head Validator approval are
      required before merge.

## Boundary

- The managed workflow itself belongs to infrastructure and is not changed by
  this ticket.
- The full 0.16.1 package lock and remaining managed payload belong to a later
  governance ticket after the workflow prerequisite is integrated.
- The source is copied only from published annotated `v0.16.1`, peeled to
  `4e6ba5ec15873346446d67d8787f17f68f57f81e`.

## Validation evidence

- Source and target SHA-256 are both
  `02e80224fb659feccf39ffa6afebd053d68f0f44137e842ea9cff6e7170b8c9d`;
  the target retains executable mode.
- A valid main-only snapshot returns `GOV-BRANCH-PASS`; an orphaned branch
  fails with `GOV-BRANCH-LIFECYCLE-002`; a structurally incomplete snapshot
  fails closed with `GOV-BRANCH-LIFECYCLE-003`.
- Focused Ruff and deterministic governance pass. The full suite and hosted
  boundaries remain required before merge.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
