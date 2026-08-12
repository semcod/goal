---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-053
---
# Participant: codex (AI agent)

## Understanding

Goal still pins new-project 0.14.1, which explains the missing adopted
workspace checker and remediation-intent DSL despite Goal already exposing a
workspace-check command. A single adoption initially crossed ownership because
the standard also manages a `.github` workflow. Tickets 051 and 052 integrated
that checker/workflow dependency pair first. The fresh adoption check now
reports 23 remaining paths, all owned by governance.

## Execution plan

1. Bind adoption to the annotated published new-project v0.16.1 exact commit.
2. Record and approve the read-only 23-path adoption plan before mutation.
3. Apply the upgrade using the public Goal 2.1.298 CLI and inspect every path.
4. Verify the pinned lock, deterministic governance, workspace lifecycle and
   remediation-intent/todo2code/LLM projection contracts.
5. Run the full Goal suite and publish through a protected PR.
6. Require Python 3.12/3.13 CI, live remote lifecycle and exact-head trusted
   Validator App approval before merge; close evidence separately.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
