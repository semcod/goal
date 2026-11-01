# Ticket 229: Verify delegated publication through the real CLI and package boundary

- **ID**: ticket-229
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-01
- **maxActiveMinutes**: 45

SESSION_EXECUTION_AUTHORIZATION: execute, test and request protected merge/publication for the Goal migration. Source ticket-228 owns the failure fix; this declared integration slice adds the actual subprocess boundary and built-wheel CLI byte parity. A qualified external probe shows public 2.2.7 returns success and invokes a harmless fallback marker after delegated exit 37; the patched application returns failure without fallback. Every regression upload command only writes a local fixture marker. Version projections join this material integration at 2.2.8; no separate release-only ticket. Preserve foreign dirty primary state and independently publish exact CI input pins before this candidate can pass verification.

- [x] AC-01: Actual CLI success and failure preserve exact delegated argv/cwd and never invoke the configured fallback publisher.
- [x] AC-02: Built-wheel CLI parity, existing observer integration, version/lock contract and governed local delivery pass.
- [ ] AC-03: Required exact-input/current-base CI and independent merge pass; Goal publishes 2.2.8 and public artifact source/hash readback passes.
