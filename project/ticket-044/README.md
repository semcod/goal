# Ticket 044: Retry exact PR head after governed push

- **ID**: ticket-044
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Make governed pull-request delivery tolerate the bounded GitHub API
eventual-consistency window observed immediately after a successful branch
push. When exactly one open PR still reports the previous head SHA, Goal must
retry the exact-head query briefly, reuse the PR only after it reports the
current local/pushed SHA, and retain the existing fail-closed result when the
authoritative value never converges.

## Acceptance criteria

- [x] AC-01: A single open PR that first reports a stale head and then the
  current pushed head is reused after a bounded retry.
- [x] AC-02: A persistently stale PR still fails closed with the existing
  exact-head diagnostic after the retry budget is exhausted.
- [x] AC-03: Missing, duplicate, malformed and failed PR queries retain their
  current behavior; Goal does not create another PR merely because an existing
  PR view is briefly stale.
- [x] AC-04: Focused/full tests, Ruff, governance, package and Docker checks
  pass before exact-head protected delivery.

## Boundary

- No release carrier, registry publication, tag or GitHub Release change
  belongs to this application ticket.
- The retry applies only to one open PR whose head is stale after a successful
  controlled push. It does not weaken the exact-head binding or retry ambiguous
  and invalid results.
- The user's instruction to repair and continue is bounded
  `SESSION_EXECUTION_AUTHORIZATION`; trusted merge still requires external
  exact-head evidence from the configured Validator App.

## Validation evidence

- The live ticket-043 update provided the production-shaped regression: Git
  push succeeded, the first open-PR query returned the previous head, and the
  next read exposed the new head without another write.
- 18 focused delivery tests pass. The new convergence test observes two exact
  PR queries and one injected one-second wait; the persistent-stale test
  observes all four attempts and three waits without incurring wall-clock
  delay.
- Full validation passes: 574 tests with 2 existing skips, scoped Ruff,
  `GOV-PASS`, wheel/sdist build and Docker image
  `sha256:a74fbd23c2dacd225b4c28ffe03a2cc823442a264a3de4d6bd6615b8960fffe0`.
  The temporary Docker image was removed immediately after its immutable ID
  was recorded.
- Local build artifacts were
  `goal-2.1.295-py3-none-any.whl@da34f53045f1cff7217b3b6b94e3c3db282a591afd9e289f684059df4fac01b0`
  and
  `goal-2.1.295.tar.gz@3c912763d437edb83dbaab0089aad2b096d42617f2560930fcc831d50361addc`;
  they are validation-only and are not published by this ticket.
- After terminal Goal 2.1.296 closure, the branch was refreshed to exact
  `main@ff4064321427f8b3d8c1c150d86b4532535545a7`. Governance passes and the
  resulting PR diff contains no ticket-043 release carrier or README change.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
