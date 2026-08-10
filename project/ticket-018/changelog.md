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
- CI passed on Python 3.12 and 3.13; the validator approved exact head
  `a96e79f86d7c3194a0a14c5bfca41777e6d4466a` and PR #34 merged as
  `114d62a3f2b37ff89f2ee05bcd2d142cd06d6609`.
