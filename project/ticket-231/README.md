# Ticket 231: Verify dynamic version diagnostics at the package boundary

- **ID**: ticket-231
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01
- **maxActiveMinutes**: 45

SESSION_EXECUTION_AUTHORIZATION: execute, test and request protected merge/publication for the Goal publication repair. Application ticket-230 independently fixes PY011 false alarms and nested fallback rewrites observed on Fixos. This material integration exercises the full diagnostic API in fresh child processes and proves the repaired module is packaged byte-for-byte. Public installed Goal 2.2.8 fails this contract; the accepted application passes four report/fix cases. Release 2.2.9 projections join this implementation; preserve all non-root dependency records and independently accept exact CI input pins before publication. No package fixture is imported or executed.

- [ ] AC-01: Fresh process diagnostics preserve dynamic initializer bytes and distinguish real VERSION mismatches in report and fix modes.
- [ ] AC-02: Built-wheel diagnostic byte parity, version/lock consistency, affected tests and governed Goal-a delivery pass.
- [ ] AC-03: Independently accepted exact verifier inputs, full current-base checks and independent merge pass; Goal publishes 2.2.9 with public artifact/source verification.
