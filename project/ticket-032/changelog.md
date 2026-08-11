# Ticket Changelog (ticket-032)

## [0.1.0] - 2026-08-11

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Bounded the change to a thin Goal CLI adapter over the target's pinned
  governance package and one focused test module.
- Added `goal governance check` with canonical package-path ownership,
  argument/output/exit forwarding and fail-closed adoption diagnostics.
- Added four focused CLI regressions and passed the full test, governance,
  package and production-container validation matrix.
