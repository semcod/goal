---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-032
---
# Participant: codex (AI agent)

## Understanding

`new-project` currently publishes shell and batch wrappers that invoke the
adopted Python validator directly. Goal already owns governance adoption and
delivery, but its CLI has no standalone validator entrypoint. A thin command
adapter closes that gap without moving policy ownership into Goal.

## Execution plan

1. Resolve and validate the target's adopted governance package.
2. Run its deterministic validator with canonical paths and forwarded options.
3. Preserve process output and exit status, including fail-closed setup errors.
4. Add CLI regressions and run the full Goal validation contract.
5. Leave `new-project` wrapper migration to its own governed ticket.
6. Ensure this gate bypasses Goal's interactive user bootstrap, mutable project
   configuration and network-facing version update path.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Added `goal governance check` as a thin process adapter over the target's
  adopted `.governance` package.
- Reserved manifest, lock, root and stack-profile options to prevent callers
  from escaping the pinned package, while forwarding ordinary validator flags,
  output and exact exit status.
- Added success, nonzero, missing-package and override regressions; passed 8
  focused and 531 full tests, Ruff, governance, build and Docker validation.
- Verified the real Goal package passes and `glon` reports a precise missing
  adoption error before any mutation.
- Container validation exposed the first-run Goal wizard before subcommand
  execution; the bounded plan now includes a read-only main-context bypass.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
