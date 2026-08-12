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

The first non-published trial was discarded before review because the newly
adopted gate correctly required the explicit atomic `standardAdoption`
from/to revision binding and repository policy budgets. The revised intent now
uses that managed-payload exemption instead of widening ordinary implementation
limits; all payload hashes still have to match the published lock.

The same gate also surfaced a pre-existing mutable `goal:local` image tag in
`compose.yml`. Ticket 054 fixed that infrastructure-owned prerequisite and is
closed on `main`. Ticket 053 has resumed at `IN_PROGRESS / EDIT`; its atomic
adoption binding is recorded together with the lock-changing payload.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Resumed after ticket 054 closed and rebound the accepted base to its closure
  merge on `main`.
- Adopted the remaining published 0.16.1 managed payload, including the typed
  diagnostic catalog, reusable error runbooks, remediation-intent schema and
  analyzer, and workspace lifecycle checker.
- Verified drift-free adoption, deterministic change validation, explicit
  active-worktree handling, the full upstream DSL/todo2code probes and all 600
  Goal tests (2 existing skips).
- Detected that Goal's committed-candidate resume still ran cost bootstrap
  before recognizing the clean candidate and generated an out-of-scope README
  badge update. Restored README exactly and kept the incident as follow-up
  evidence instead of admitting it into this adoption.

## Blockers

- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
