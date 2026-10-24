# Ticket 200: Treat registry-lagging tree version as pending publication

- **ID**: ticket-200
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

Follow-up to ticket-196 observed live on the goal repository itself: when a
publish-only release leaves no tag on the base branch, the version transition
commit becomes its own boundary and the diff-vs-boundary check returns empty,
so `goal -a` reported "No changes to deliver" even though the registry never
received the release. `_has_committed_unreleased_sources` now falls back to a
registry comparison: a synchronized tree version newer than the published
registry baseline is pending publication.

## Acceptance criteria

- [ ] AC-01: Tree 2.2.2 vs registry 2.2.1 reports pending (completion fires).
- [ ] AC-02: Registry caught up (2.2.2) reports not pending; mixed version sources report not pending (fail-closed).
- [ ] AC-03: Existing completion/no-change boundary tests still pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
