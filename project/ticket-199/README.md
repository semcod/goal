# Ticket 199: Align runtime banner with 2.2.2 release

- **ID**: ticket-199
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

Application-owned runtime banner bump: `goal/__init__.py` `__version__`
2.2.1 -> 2.2.2, completing the version projection for the 2.2.2 release
(pyproject.toml and VERSION were bumped by ticket-198). Without this line
the publication stage classifies the release as a partial bump and refuses
the clean publish-only completion.

## Acceptance criteria

- [ ] AC-01: `goal.__version__ == "2.2.2"` with no other source delta.
- [ ] AC-02: Test suite passes; governance check passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
