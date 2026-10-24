# Ticket 205: Report unreleased sources distinctly from pre-bumped completion

- **ID**: ticket-205
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

Observed live on heyasa after its 0.3.0 release: three further PRs merged, so
`goal -a --dry-run` on the clean synchronized base entered the completion
branch and failed later with the confusing
"clean --force-publish requires an already synchronized, pre-bumped release
version (decision: normal-bump)". Ordinary unreleased work after the last tag
is not a pre-bumped release awaiting its publish. The completion branch now
requires that the tree version actually be ahead of the registry; otherwise it
fails immediately with an actionable governed message naming the release-ticket
route.

## Acceptance criteria

- [ ] AC-01: Unreleased sources without a pre-bumped version raise a clear "requires a release ticket" error and record no delivery event.
- [ ] AC-02: True pre-bumped completion and no-change boundary behavior are unchanged; full suite passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
