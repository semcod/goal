# Ticket 211: Release 2.2.4 integration version files

- **ID**: ticket-211
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

Integration-owned release projection for goal 2.2.4: VERSION and
pyproject.toml move 2.2.3 -> 2.2.4, shipping ticket-210 (automatic annotated
release tag on publish completion) with its documentation (tickets 208/209).
After merge the governed publish-completion path publishes the release and
creates/pushes the tag itself (dogfood).

## Acceptance criteria

- [ ] AC-01: VERSION contains 2.2.4 and pyproject.toml declares version 2.2.4 with no other manifest delta.
- [ ] AC-02: Test suite passes; packaging metadata parses.
- [ ] AC-03: Governance check passes for this ticket scope.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
