# Ticket Changelog (ticket-048)

## [0.1.0] - 2026-08-12

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Bounded the real generic-release failure, exact-tag recovery and fail-closed
  direct-main semantics without weakening package artifact requirements.
- Added explicit assetless GitHub Release support for generic create-on-tag,
  exact annotated-tag recovery and terminal governed direct-main failure.
- Passed 30 focused and 588 full tests (2 existing skips), Ruff, governance,
  wheel/sdist and Docker checks without changing dependencies or version.
- Entered active `IN_PROGRESS / PUBLICATION` for exact-head protected
  validation and trusted merge.
- Removed Goal-generated root README badge drift before final PR validation;
  the corrected branch has no README diff from `main`.
- PR #72 merged after exact-head CI and Validator approval, but the real
  new-project retry exposed an earlier normal-bump guard before tag recovery.
- Returned ticket 048 to `EDIT`; no mutation occurred during the failed real
  attempt and v0.16.0 remains the immutable repair target.
- Bound the normal-bump decision back to the current version only for exact
  generic create-on-tag repair, with full-workflow and negative regressions.
- Passed 34 focused and 592 full tests (2 skipped), Ruff, governance,
  wheel/sdist and Docker validation, then re-entered `PUBLICATION`.
