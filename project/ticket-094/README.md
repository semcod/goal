# Ticket 094: Adopt published integration-base validation

- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

SESSION_EXECUTION_AUTHORIZATION: the user requests continuation, fixes, tests and GitHub publication. Wait for the independently approved immutable standard release 0.20.16, then adopt it through Goal and verify the post-merge CI result. This does not wait for another chat approval.

## Acceptance criteria

- [x] AC-01: Adopt published standard 0.20.16 while preserving target extensions and immutable provenance.
- [ ] AC-02: Full tests and required checks pass, protected publication succeeds, and the main-branch CI verifies the integrated result without GOV-BASE-002.

Existing primary metadata and other agents' workspaces remain preserved.

Published dependency: wellmanifest/new-project v0.20.16, immutable source `6d2da011088b69ebe1636f3bf681e5ec21a062ab`, approved and merged in PR #309.

Validation before publication: 735 tests passed, 2 pre-existing skips; all 10 published integration-base regression cases passed against digest-verified adopted code. Governance passed with 0 errors and 0 warnings; immutable adoption, active host hooks, local pin and Compose validation passed. Package standard/revision declarations were regenerated from the lock; product package version and dependencies remain unchanged. AC-02 remains pending protected merge and the main-branch CI run.
