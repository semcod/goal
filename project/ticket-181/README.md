# Ticket 181: Keep governed test-stage inside owned project and ticket boundaries

- **ID**: ticket-181
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-03

## Outcome and scope
Detect only owned bounded projects and retain slow-test observations without generating out-of-scope Planfile tasks during governed delivery. Four material files in the existing test-stage and regression components; no version or dependencies. Reuse native allocation ticket-181. Original PR #179 closed after a genuine scope failure; commit, remote branch, recovery ref and secret-scanned snapshots are preserved. New canonical branch publishes without rewriting the prior remote branch.

## Acceptance criteria
- [x] AC-01: Discovery boundaries and governed test-stage side-effect regressions pass.
- [ ] AC-02: Full Python suite, governance, current-head CI and independent protected merge pass.

## Boundaries
No review bypass, force-push, deleted history, version or dependency changes.
