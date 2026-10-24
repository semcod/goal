# Ticket 206: Release 2.2.3 integration version files

- **ID**: ticket-206
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

Integration-owned release projection for goal 2.2.3: VERSION and
pyproject.toml move 2.2.2 -> 2.2.3, carrying the governed-autonomy chain
(tickets 196, 199-205: publish completion on a synchronized base, registry
baseline fallback, cache-safe discovery, dynamic __version__ contracts,
epilogue guard and marker, clear unreleased-sources boundary). After merge,
the governed publish-completion path publishes the release (dogfood).

## Acceptance criteria

- [ ] AC-01: VERSION contains 2.2.3 and pyproject.toml declares version 2.2.3 with no other manifest delta.
- [ ] AC-02: Test suite passes; packaging metadata parses.
- [ ] AC-03: Governance check passes for this ticket scope.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
