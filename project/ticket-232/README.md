# Ticket 232: Preserve unrelated dist files during Python doctor cleanup

- **ID**: ticket-232
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested continued fixes, tests and protected merges for Goal publication. Python doctor PY012 currently treats any file not starting with the literal project name as stale: it reports and deletes `dist/.gitignore`, other non-distribution files and the project's normalized wheel. Bound changes to Python doctor and its tests.

## Acceptance criteria

- [x] AC-01: Normalized project distributions, unrelated files and symlinked distribution directories are preserved in report and auto-fix modes.
- [x] AC-02: Clearly named distributions from another project remain discoverable and removable; uncertain filenames are preserved.
- [ ] AC-03: Doctor regressions and governance pass; the exact head receives independent current-base verification and protected review.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose and raw command logs are not required delivery output.
