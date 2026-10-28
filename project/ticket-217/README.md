# Ticket 217: Validate exact source-hub candidate governance before publication

- **ID**: ticket-217
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-28

## Goal and scope

Validate the exact source-hub candidate against `governance/manifest.hub.json` with accepted base, exact head, and `--actor ci` before running expensive source-hub suites or publishing a PR, route `goal governance workspace-check` to `scripts/workspace_lifecycle_check.py` in the source hub, reject non-canonical `--ticket` values before expensive preflight suites, and include preflight duration in total reported workflow time (closes #145).

- `SESSION_EXECUTION_AUTHORIZATION`: autonomous session execution requested by user.

## Acceptance criteria

- [x] AC-01: In the recognized source hub (with or without an incidental `.governance` tree), run `scripts/governance_check.py` with `governance/manifest.hub.json`, `governance/stack-profiles.json`, accepted base, exact head, and `--actor ci` before expensive source-hub suites and before push/PR.
- [x] AC-02: Route `goal governance workspace-check` to `scripts/workspace_lifecycle_check.py` when the target root is the source hub.
- [x] AC-03: Reject non-canonical `--ticket` identifiers before expensive preflight/test suites and record preflight/total elapsed time across `execute_push_workflow`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
