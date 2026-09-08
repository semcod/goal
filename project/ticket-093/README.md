# Ticket 093: Preserve repository boundaries in automatic version scanning

- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

SESSION_EXECUTION_AUTHORIZATION: the user requests continuation, fixes, tests and GitHub publication. This implements the version-discovery boundary gap identified during MaskFleet publication.

## Acceptance criteria

- [x] AC-01: Automatic discovery and synchronization preserve nested Git repositories, worktrees and symlink targets while still updating ordinary lockstep subpackages.
- [ ] AC-02: Focused and full tests, governance and stack checks pass; publish through independent exact-head review.

## Scope

Explicitly configured version sources retain their existing semantics. No package release, hardware commands or changes to other agents' workspaces. Preserve the primary ticket index and remove only this verified integrated worktree at completion.

## Validation

All 12 regression cases failed before the implementation and pass afterward. Focused version checks: 86 passed, 1 existing skip. Full suite: 735 passed, 2 existing skips. Ruff, managed governance (0 errors, 0 warnings), installed host contract and Docker Compose configuration pass. Protected review and merge are pending.
