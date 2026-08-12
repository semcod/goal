# Ticket 044: Retry exact PR head after governed push

- **ID**: ticket-044
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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
  `sha256:9bb5fae62a211e56792d3bc36b169c30b939a85b244520b7d9497e300bc97b0e`.
  The temporary Docker image was removed immediately after its immutable ID
  was recorded.
- Local build artifacts were
  `goal-2.1.296-py3-none-any.whl@876ce54dcf1e979be48bcc46aee9953c078ab78d1168c3c3f5c70af47ed6e3c7`
  and
  `goal-2.1.296.tar.gz@c383ee3b99f430493e1f9936838fb8fccf7260bdff1fd2b00b142164890982d8`;
  they are validation-only and are not published by this ticket.
- After terminal Goal 2.1.296 closure, the branch was refreshed to exact
  `main@ff4064321427f8b3d8c1c150d86b4532535545a7`. Governance passes and the
  resulting PR diff contains no ticket-043 release carrier or README change.
  The focused and full suites, Ruff, governance, two-artifact build and Docker
  validation above were repeated on that final base at head `90023bf`.
- The real governed delivery pushed final head `6837dd2`, reused existing PR
  #69 without creating a duplicate, and again passed 574 tests with 2 existing
  skips. Python 3.12/3.13 CI and trusted Validator App review `4915244880`
  approved that exact head before it merged as
  `main@000da3cd4250f56cf205594facad19cb42c78218`.
- The clean merge tree is byte-identical to the approved head; all 18 focused
  delivery tests and deterministic governance pass on authoritative `main`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
