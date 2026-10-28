# Ticket 214: Release 2.2.5 integration version files

- **ID**: ticket-214
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

Integration-owned release projection for goal 2.2.5: VERSION and
pyproject.toml move 2.2.4 -> 2.2.5, shipping ticket-213 (exact registry
version confirmation before treating a tree as unpublished).

## Acceptance criteria

- [ ] AC-01: VERSION contains 2.2.5 and pyproject.toml declares version 2.2.5 with no other manifest delta.
- [ ] AC-02: Test suite passes; packaging metadata parses.
- [ ] AC-03: Governance check passes for this ticket scope.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
