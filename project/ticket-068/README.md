# Ticket 068: Emit actionable standard-update diagnostics

- **ID**: ticket-068
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-02

## Goal and scope

Make Goal's fail-closed pre-commit standard-adoption refusals machine-routable
by emitting the target-published `GOV-STANDARD-UPDATE-001` diagnostic. Preserve
the current-pin no-op and the exact staged ticket/intent authorization checks.

## Acceptance criteria

- [x] AC-01: Every staged-pin or adoption-intent refusal emits
  `GOV-STANDARD-UPDATE-001`.
- [x] AC-02: A current staged pin remains a successful no-op without a false
  diagnostic.
- [x] AC-03: Focused tests, Ruff, governance, full tests and Docker pass.

## Authorization

`SESSION_EXECUTION_AUTHORIZATION`: the user explicitly requested continued
implementation, testing and deployment of automatic Wellmanifest updates and
repairs to Goal and Koru.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
