# Ticket 215: Align runtime banner with 2.2.5 release

- **ID**: ticket-215
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

Application-owned runtime banner bump: goal/__init__.py __version__
2.2.4 -> 2.2.5, completing the version projection for the 2.2.5 release
(pyproject.toml and VERSION bumped by ticket-214).

## Acceptance criteria

- [ ] AC-01: goal.__version__ == "2.2.5" with no other source delta.
- [ ] AC-02: Test suite passes; governance check passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
