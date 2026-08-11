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

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
