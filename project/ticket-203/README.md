# Ticket 203: Publish-completion runs must not attempt a pull-request epilogue

- **ID**: ticket-203
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

Live defect from goal's own 2.2.2 completion run: after the registry upload
succeeded, the governed pull-request dispatch still attempted
`deliver_pull_request`, pushing an empty synthetic branch (`goal/<sha>`) and
failing PR creation ("No commits between main and ..."). The orphaned branch
then tripped GOV-BRANCH-LIFECYCLE-002 in the protected workflow. The
completion run now terminates the delivery dispatch with a terminal
`published` event and an explicit summary; ordinary pull-request runs are
unchanged.

## Acceptance criteria

- [ ] AC-01: The pull-request dispatch guards on `_publish_completion`; ordinary runs keep delivering PRs.
- [ ] AC-02: Existing completion/boundary tests still pass; full suite green.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
