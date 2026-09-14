# Ticket 107: Resumable adoption transaction integration

- **ID**: ticket-107
- **Owner**: agent:codex-adoption-pilot
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-14

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-09-14 the user requested execution
and protected publication of the adoption automation pilot, explicitly approved
the exact integration ownership mapping, and then requested continuation.

Goal PR151 independently accepted the two exact ownership entries at
fabdc0c143c012f56e0f2ec1d009a07fadf7ff16. This existing integration ticket now
receives the unchanged controller and tests preserved from ticket-106, plus
their documentation and explicit local journal contract. Original handoff
materials remain in private external state. No wellmanifest policy is changed.

## Acceptance criteria

- [ ] AC-01: Durable phase execution and restart readback reuse one transaction and stable effect keys.
- [ ] AC-02: Changed subject, stale CAS, missing authority and uncertain outcomes fail closed.
- [ ] AC-03: The managed gate and whitespace checks pass for the declared source, tests and documentation.
- [ ] AC-04: Existing pinned-planner and governance-delivery regressions retain their results.

## Delivery boundary

The module is a single-host pilot with trusted adapter interfaces and isolated
fixtures, not a production updater or a deployed scheduler. Publish through
Goal and independent exact-head Validator review. Only the protected controller
may record terminal closure; this README is not approval or a merge receipt.
