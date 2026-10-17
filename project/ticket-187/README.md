# Ticket 187: Fix PERF-AUDIT findings and populate standard-adoption.json

- **ID**: ticket-187
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-10-17

## Goal and scope

Fix `PERF-AUDIT-SQLITE-001`, all `PERF-AUDIT-SUBPROC-001` subprocess-in-loop findings across `goal`, and `PERF-AUDIT-KWARG-001` unused optional parameters across the 15-file `L` ticket budget, and populate `.governance/standard-adoption.json` so `standard_pack_check.py` passes with `findings=0`.

SESSION_EXECUTION_AUTHORIZATION: user requested fixing all PERF-AUDIT findings and adopting Wellmanifest standards across Semcod repositories.

## Acceptance criteria

- [x] AC-01: Fix `PERF-AUDIT-SQLITE-001` in `goal/postcommit/manager.py` and all `PERF-AUDIT-SUBPROC-001` findings across `goal/bootstrap/costs_badge.py`, `goal/bootstrap/installer.py`, `goal/cli/tests.py`, `goal/cli/tests_pytest_setup.py`, `goal/cli/version_sync.py`, `goal/deep_analyzer_aggregate.py`, `goal/project_bootstrap.py`, `goal/recovery/corrupted.py`, and `goal/recovery/manager.py`.
- [x] AC-02: Fix `PERF-AUDIT-KWARG-001` findings in `goal/bootstrap/costs_badge.py`, `goal/changelog.py`, `goal/cli/tests.py`, `goal/git_ops.py`, `goal/project_bootstrap.py`, `goal/push/core.py`, `goal/recovery/large_file.py`, and `goal/summary/generator.py`.
- [x] AC-03: Populate `.governance/standard-adoption.json` so `python3 .governance/standard_pack_check.py --root .` reports `findings=0`.
- [x] AC-04: Unit tests and `./project/governance-check.sh` pass (`GOV-PASS`).

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
