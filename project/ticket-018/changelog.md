# Ticket Changelog (ticket-018)

## [0.1.0] - 2026-08-10

- Initialized a bounded regression ticket from the reproduced post-release
  duplicate-bump evidence.
- No human participant identity or content was generated.
- Added a conservative synchronized-version transition detector and used it as
  the lower bound for committed-source release analysis.
- Added regressions for released source before the transition and new source
  after it; focused tests passed 27/27.
- Full Python validation passed with 510 tests and 2 expected skips; fresh-base
  governance passed with zero errors and warnings.
