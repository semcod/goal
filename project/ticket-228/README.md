# Ticket 228: Stop direct fallback after delegated publication failure

- **ID**: ticket-228
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01
- **maxActiveMinutes**: 30

SESSION_EXECUTION_AUTHORIZATION: execute, test and request protected publication for the existing Goal publication migration. A mocked canary on accepted Goal 2.2.7 proves make exit 37 triggers a direct upload and returns success. This masks failed Goal admission/repair when make publish delegates to Goal. Stop after a delegated publication failure; preserve direct publication when make/target is unavailable or explicitly disabled and preserve previews. This application change owns no version or integration carrier; registry release projections require their declared owner.

- [x] AC-01: Failed make publication returns a nonzero CLI result and never triggers direct upload, including when direct upload would succeed.
- [x] AC-02: Delegated success avoids duplicate upload; direct fallback without a target and dry-run remain compatible; affected regressions and governed Goal delivery pass.
- [ ] AC-03: Required exact-head/current-base checks and independent Validator merge pass.
