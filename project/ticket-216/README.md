# Ticket 216: Diagnose disagreeing managed version sources explicitly

- **ID**: ticket-216
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

A coordinated governed release lands its version projection across workstream
tickets (integration owns VERSION/pyproject, application owns the runtime
banner). Between those merges the managed declarations disagree; `goal -a`
answered with a generic "requires a release ticket" or the confusing clean
force-publish error. The pull-request boundary now names the exact state and
the remaining action.

## Acceptance criteria

- [ ] AC-01: Disagreeing managed versions raise "Managed version sources disagree (...)" naming the values and the remaining tickets.
- [ ] AC-02: Single-version behavior (pending completion, unreleased sources, no-change) is unchanged.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
