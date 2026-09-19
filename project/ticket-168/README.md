# Ticket 168: Register docs standard integration ownership

- **ID**: ticket-168
- **Owner**: agent:gemini
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-19
- **Authorization**: SESSION_EXECUTION_AUTHORIZATION

## Goal and scope

Register initial integration ownership for `.governance/docs.json` under `workstreams.integration.ownedPaths` and `coordination.integration.requiredForPaths` in Goal's local manifest `.governance/manifest.json`.

This unblocks subsequent integration ticket to adopt `wellmanifest/docs` and normalize documentation metadata.

## Acceptance criteria

- [x] AC-01: `.governance/docs.json` is registered under integration ownership in `.governance/manifest.json`; managed governance passes cleanly.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
