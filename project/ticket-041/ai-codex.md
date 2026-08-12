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
- Moved the adopted-package file contract into the delivery adapter and made
  both delivery and `governance check` distinguish target packages from the
  maintained source hub before executing any target wrapper.
- Added compatible diagnostics v1/v2 parsing. V2 failure codes now emit their
  canonical remediation and only link a runbook that resolves inside the
  adopted `.governance` directory and exists on disk.
- Replaced callback-level `ensure_config()` calls with the already loaded
  read-only governance context. A missing or policy-free pre-push
  authorization now fails closed instead of creating a default config and
  allowing the push.
- Proved the real prior hub command now reports the layout contract and leaves
  its already-dirty status and file hashes unchanged.
- Passed 46 focused tests, 570 full tests (2 skipped), scoped Ruff, governance,
  wheel/sdist and the final Docker build.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
- Protected CI, exact-head review and merge remain delivery-stage work.
