# Ticket 044: Retry exact PR head after governed push

- **ID**: ticket-044
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Make governed pull-request delivery tolerate the bounded GitHub API
eventual-consistency window observed immediately after a successful branch
push. When exactly one open PR still reports the previous head SHA, Goal must
retry the exact-head query briefly, reuse the PR only after it reports the
current local/pushed SHA, and retain the existing fail-closed result when the
authoritative value never converges.

## Acceptance criteria

- [ ] AC-01: A single open PR that first reports a stale head and then the
  current pushed head is reused after a bounded retry.
- [ ] AC-02: A persistently stale PR still fails closed with the existing
  exact-head diagnostic after the retry budget is exhausted.
- [ ] AC-03: Missing, duplicate, malformed and failed PR queries retain their
  current behavior; Goal does not create another PR merely because an existing
  PR view is briefly stale.
- [ ] AC-04: Focused/full tests, Ruff, governance, package and Docker checks
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

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
