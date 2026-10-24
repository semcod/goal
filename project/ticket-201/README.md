# Ticket 201: Skip governed runtime state in version-spec discovery

- **ID**: ticket-201
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

Companion to ticket-196 for the second discovery walker: `discover_version_specs`
(goal/cli/version_state.py) kept scanning `.subactor` and `.worktrees`, so
release-evidence snapshots of past sources were picked up as inferred-lockstep
version carriers. On the goal repository's own 2.2.2 publication this made the
decision "partial-bump" (snapshots still at 2.2.1) and refused the clean
publish-only completion. Adds the governed runtime state and delivery worktree
directories to the discovery skip set.

## Acceptance criteria

- [ ] AC-01: `discover_version_specs()` ignores version carriers under `.subactor` and `.worktrees`.
- [ ] AC-02: Existing completion/no-change/boundary tests still pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
