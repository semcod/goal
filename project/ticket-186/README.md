# Ticket 186: Source hub health preflight progress and deterministic cache

- **ID**: ticket-186
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-10-14

## Goal and scope

Add proportional progress reporting, bounded execution timeout (default 300s, exit code 124), deterministic caching under `.subactor/cache/source-hub-health.json`, and in-process delivery validation deduplication in `goal/governance/delivery.py` and `goal/push/core.py`.
Parent operational request: `maskservice/c2004#452` (PLF-2962).

## Acceptance criteria

- [x] AC-01: Proportional progress reporting and bounded timeout in `run_source_hub_health`.
- [x] AC-02: Deterministic cache keyed on tree, documents, workflow, suites, tool, and environment; false-green invalidation verified and failures are never cached.
- [x] AC-03: In-process delivery gate deduplication and cheap fast-fail validation in `validate_delivery_ready`.
- [x] AC-04: Full governance gate and unit tests pass with zero errors.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
