# Ticket 180: Recover governed PR delivery from GraphQL rate limits

- **ID**: ticket-180
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-03

## Outcome and scope
Recover exact-repository PR queries and creation through REST only after explicit GraphQL rate exhaustion. Preserve canonical branch ownership, exact-head checks, non-forced push and independent approval. Session execution authorization covers this two-file material bug fix and protected publication. Dependency ticket-181 has been protected-merged; this continuation uses its owned-project discovery and bounded governed test stage.

## Acceptance criteria
- [x] AC-01: Rate-exhaustion recovery works without duplicate PRs or wrong repository/base/head.
- [ ] AC-02: Existing delivery tests, governance, OneDev and independent protected merge pass.

## Boundaries
No new dependencies, version/release changes, review bypass or ordinary-error retry. Raw receipts remain private.
