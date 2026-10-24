# Ticket 204: Set the publish-completion marker for the epilogue guard

- **ID**: ticket-204
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

One-line follow-up to ticket-203, caught live on heyasa's 0.3.0 completion:
ticket-203's delivery-dispatch guard reads `ctx_obj["_publish_completion"]`,
but the completion branch never set that marker, so the epilogue still pushed
an empty synthetic branch after the registry upload. The completion branch now
sets the marker the guard already expects.

## Acceptance criteria

- [ ] AC-01: The completion test asserts the `_publish_completion` context marker.
- [ ] AC-02: Existing completion/boundary tests still pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
