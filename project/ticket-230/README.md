# Ticket 230: Preserve dynamic package versions in doctor diagnostics

- **ID**: ticket-230
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01
- **maxActiveMinutes**: 30

SESSION_EXECUTION_AUTHORIZATION: execute, test and request protected publication within the existing Goal publication repair. Fixos 2.2.59 publication reports PY011 because an indented exception fallback assigns unknown, despite its actual runtime VERSION/metadata contract. PY011 also rewrites nested fallbacks while synchronizing an unrelated VERSION mismatch. Reuse Goal's existing anchored module-level version convention; never execute the observed package. This application slice owns no release/version projections.

- [ ] AC-01: Dynamic and nested fallback assignments produce no false version mismatch and remain byte-identical in report and auto-fix modes.
- [ ] AC-02: Real VERSION and static module-level literal mismatches still report and synchronize forward; affected tests and Goal-a governed delivery pass.
- [ ] AC-03: Exact-head/current-base protected checks and independent Validator merge pass.
