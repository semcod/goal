# Ticket 233: Release Goal 2.2.10 with safe Python doctor cleanup

- **ID**: ticket-233
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested continued implementation, tests, protected merge and package publication. Ticket-232 was independently merged and repairs destructive PY012 cleanup. Release its accepted source as Goal 2.2.10 and validate the repair from an installed wheel. Preserve all non-root dependency lock records. Independently accept the exact OneDev verifier input pins before requiring its full matrix; source merge and registry publication remain distinct.

## Acceptance criteria

- [x] AC-01: An installed Goal wheel preserves normalized project distributions and unrelated files while removing a recognizable foreign distribution.
- [ ] AC-02: Release versions and lock agree; affected tests, governance and exact verifier inputs pass.
- [ ] AC-03: Current-base protected CI and independent Validator merge precede Goal-a publication; read back public artifacts against accepted source.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose and raw command logs are not required delivery output.
