# Ticket Changelog (ticket-027)

## [0.1.0] - 2026-08-10

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Recorded the production Koru reproduction where Goal returned a merged PR
  after pushing a different commit to the reused branch.
- Bounded the repair to open/exact-head PR resolution and focused tests.
- Query only open PRs for the governed base/head pair and require their
  `headRefOid` to equal the current pushed commit.
- Re-verify newly created PRs through the same lookup and fail closed on
  ambiguity, malformed output, a stale head or a missing created PR.
- Passed focused/full Python, Ruff, governance and production Docker gates.
- Recorded Goal's registry-aware 2.1.294 release decision without crossing
  the application ticket's version-carrier boundary.
