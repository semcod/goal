# Ticket 213: Confirm exact registry version before treating tree as unpublished

- **ID**: ticket-213
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

Observed live on heyasa right after the 0.4.0 completion: the registry's
"latest" JSON is CDN-cached, so a second `goal -a` in that window saw the tree
version as newer than the registry, re-entered the completion branch and failed
with the confusing clean force-publish error. The pending check now confirms
the exact version through the version-specific PyPI document before claiming
that publication is pending.

## Acceptance criteria

- [ ] AC-01: A CDN-lagged latest with the exact version published reports not pending; a genuinely unpublished version stays pending.
- [ ] AC-02: Existing completion/boundary tests still pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
