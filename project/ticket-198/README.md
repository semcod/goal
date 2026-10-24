# Ticket 198: Release 2.2.2 integration version files

- **ID**: ticket-198
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-23

## Goal and scope

Integration-owned release projection for goal 2.2.2: `VERSION` and
`pyproject.toml` move 2.2.1 -> 2.2.2, carrying the autonomous publication
completion and frozen-config protection (ticket-196) plus its documentation
(ticket-197). After this merges, the governed `goal -a` publish-completion
path publishes the release (dogfood of the new behavior).

## Acceptance criteria

- [ ] AC-01: `VERSION` contains `2.2.2` and `pyproject.toml` `version = "2.2.2"` with no other manifest delta.
- [ ] AC-02: Test suite passes; packaging metadata parses.
- [ ] AC-03: `./project/governance-check.sh` passes for this ticket scope.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
