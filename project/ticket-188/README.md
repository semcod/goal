# Ticket 188: Ignore released and missing-worktree leases in governed_clone_evidence

- **ID**: ticket-188
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-10-18

## Goal and scope

Ignore released (`status="released"`, `phase="released"`, `state="released"`, or `released_at` set) and stale `.subactor/leases/*.json` files whose target worktree directory no longer exists when `governed_clone_evidence` checks whether a non-governed checkout belongs to a governed clone.

SESSION_EXECUTION_AUTHORIZATION: user requested fixing publication issues across semcod/* via ticket creation and Willman execution.

## Acceptance criteria

- [x] AC-01: `governed_clone_evidence` in `goal/governance/delivery.py` skips lease records with `phase="released"`, `state="released"`, `released_at`, or a non-existent `worktreePath`/`worktree`/`worktreeId` directory.
- [x] AC-02: Unit tests in `tests/test_governance_delivery.py` and `./project/governance-check.sh` pass (`GOV-PASS`).

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
