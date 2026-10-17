# Ticket 185: skip detected setup.py with computed version as a version source

- **ID**: ticket-185
- **Owner**: claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-13

## Goal and scope

`goal -a --bump patch` in semcod/fixos (2026-10-13) stopped with
`Version sources are unreadable or unsupported - setup.py:version: selector
version was not found`. fixos's `setup.py` reads its version from `VERSION`
(single source of truth), but every root-level detected file was treated as a
primary source. `collect_version_sources` now skips a detected `setup.py`
without a version literal; a configured `setup.py:version` still fails closed.

SESSION_EXECUTION_AUTHORIZATION: user requested publishing fixos through `goal -a` and verifying it works.

## Acceptance criteria

- [x] AC-01: `tests/test_version_state.py` covers the computed (skipped) and configured (still failing) cases.
- [x] AC-02: `./project/governance-check.sh` passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
