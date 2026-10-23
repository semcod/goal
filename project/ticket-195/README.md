# Ticket 195: Align Goal runtime version with released metadata

- **ID**: ticket-195
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-23

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requests continued tested backlog merges. Follow-up STARTER-027 / GitHub issue196 reproduces the stale2.2.0 module version while the existing release metadata is2.2.1. Correct only this declared runtime version projection; retain updater behavior.

## Acceptance criteria

- [x] AC-01: Runtime, package metadata and VERSION agree; existing CLI/update checks pass.
- [ ] AC-02: Protected checks and independent merge pass; exact merged local runtime runs plain goal-a without a redundant update, preserving checkout state.

## Local validation

50 existing CLI/update tests pass; governance and isolated fatal-error lint pass. Real imported module equals VERSION and pyproject2.2.1; same-version updater is not called, newer-version updater remains called. Independent protected checks and actual merged-runtime canary remain required.
