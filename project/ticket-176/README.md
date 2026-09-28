# Ticket 176: Support -k and --koru flag for koru auto-repair

- **ID**: ticket-176
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-28

## Goal and scope
 
Add `-k` / `--koru` flag to `goal` CLI to automatically run koru auto-repair (`koru --doctor --repair`).

## Acceptance criteria

- [x] AC-01: Support `-k` and `--koru` flag in `goal` main group and push command.
- [x] AC-02: When `-k` / `--koru` is supplied, invoke koru auto-repair before workflow / when repairing.
- [x] AC-03: `goal -k` without subcommand defaults to running koru auto-repair and push / repair.

## Validation evidence

- `pytest tests/test_cli_options.py`: 28 passed.
- `pytest tests/test_governance_delivery.py`: 73 passed.
- `./project/governance-check.sh`: passed (0 errors, 0 warnings).
- `goal -k --dry-run` successfully invoked Koru auto-repair and created governance remediation proposal TWIN-007 for GOV-AGENT-HOST-001.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

