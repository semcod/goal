# Ticket 177: Harden koru auto-repair and released lease filtering

- **ID**: ticket-177
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-29

## Goal and scope

Harden Koru auto-repair runner with headless environment and compact summary; filter released leases from clone evidence.

## Acceptance criteria

- [x] AC-01: Filter released leases from governed clone evidence in `goal/governance/delivery.py`.
- [x] AC-02: Run Koru repair with headless/no-reexec environment and provide compact summary formatter in `goal/governance/remediation.py`.
- [x] AC-03: Use compact summary in push workflow in `goal/push/core.py`.

## Validation evidence

- `pytest -q tests/test_governance_delivery.py`: passes.
- `./project/governance-check.sh`: passed.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
