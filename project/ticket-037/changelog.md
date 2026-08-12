# Ticket Changelog (ticket-037)

## [0.1.0] - 2026-08-12

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Recorded the bounded provenance-verification repair and test contract.
- Required production adoption to fetch the version-matched annotated tag and
  prove that it peels to the requested full SHA.
- Added an explicit unpublished-candidate testing option without weakening the
  default production path.
- Added fail-closed regression tests and live released/unreleased pilot
  evidence.
- Merged exact-head PR #62 after CI and deterministic Validator Agent approval,
  then removed its remote head and clean local worktree/branch.
