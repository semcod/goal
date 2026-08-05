# Ticket changelog (ticket-003)

## [0.1.0] - 2026-08-05

- Defined governed `direct-main`, `publish-only`, and `pull-request` delivery
  modes.
- Defined local hook, transaction authorization, audit, and server-protection
  boundaries.
- Recorded dependency on ticket-002; no application code was changed.

## [0.2.0] - 2026-08-05

- Added governed direct-main, publish-only, and pull-request delivery.
- Added managed pre-push enforcement with a short-lived file-backed
  capability, audit events, and explicit server-security guidance.
- Preserved legacy behavior when no delivery policy is configured.
- Passed 55 regression tests, 6 focused retry tests, and governance validation.
