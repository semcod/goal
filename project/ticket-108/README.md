# Ticket 108: Bind adoption planner to resumable transaction

- **ID**: ticket-108
- **Owner**: agent:codex-adoption-pilot
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-14

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-09-14 the user requested continued
implementation, testing and protected publication of Goal adoption automation.
This bounded follow-up connects the accepted planner and transaction controller
without live consumer updates, new authority or another publisher.

The existing integration-owned source and test paths are the only material
changes. A derived scope digest binds the declared scope and fresh planner
identity, including catalog, lock and checkout observations. The original
profile digest and journal schema remain unchanged. Multi-step plans require
separate staged integration; supported current pins need no transaction.

## Acceptance criteria

- [ ] AC-01: A single planned migration creates a stable bound subject without effects on the consumer.
- [ ] AC-02: Retain is no-change; blocked and multi-step plans fail closed; changed observations or scope cannot reuse the same subject.
- [ ] AC-03: Focused regressions and managed governance pass before independent exact-head publication.

## Delivery boundary

The factory observes and prepares data only. Trusted adapters still establish
policy provenance, current lease/fencing, permission, idempotent effects and
independent review. No updater deployment or package release is claimed.
