---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-041
---
# Participant: codex (AI agent)

## Understanding

Goal currently treats every checkout containing
`project/governance-check.sh` as an adopted target. In the `new-project` source
hub that wrapper resolves `.governance/governance_check.py`, which deliberately
does not exist, so users receive a raw Python path error. Separately,
`governance verify-delivery` and `authorize-push` call `ensure_config()` even
though governance dispatch is documented as headless; this can create or
rewrite `goal.yaml`. The standard now carries canonical diagnostics v2 entries
and selected managed runbooks, but Goal does not surface them.

## Execution plan

1. Add package-layout preflight to the existing governed delivery adapter.
2. Parse adopted diagnostics v1/v2 without trusting unsafe documentation paths.
3. Make existing governance callbacks use the read-only context configuration.
4. Add focused regressions and run the complete validation chain.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
