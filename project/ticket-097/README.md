# Ticket 097: Contributor verification and real local matrix canary

- **ID**: ticket-097
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-08

SESSION_EXECUTION_AUTHORIZATION: The user requested continued implementation, testing and publication ("kontynuuj, wypchnij, przttestuj").

## Goal and scope

Publish the canonical [contributor verification runbook](../../docs/information/contributor-verification.md) and its documentation index entry. Use this material PR to observe the deployed Goal OneDev matrix on a new candidate while retaining every existing server gate.

## Acceptance criteria

- [ ] AC-01: The indexed runbook explains repository checks, independent publication, stale-base recovery and remaining migration requirements; documentation and repository checks pass.
- [ ] AC-02: Publish the exact head, observe the deployed local matrix and retained hosted checks, then use the independent Validator for protected merge. Retain external publication receipts.

## Tracking boundary

Raw logs and receipts stay in ignored recovery storage. This ticket remains IN_PROGRESS / PUBLICATION until the trusted external controller closes delivery.
