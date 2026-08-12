---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-056
---
# Participant: codex (AI agent)

## Understanding

`goal -a` is the documented governed workflow, but Click rewrites it to the
`push` subcommand without supplying that subcommand's optional `--ticket`.
`execute_push_workflow` only classifies an already committed PR candidate when
the parameter is present. The workflow therefore falls through to mutating
bootstrap even though one active ticket and one immutable candidate already
exist. The explicit-ticket path has a second self-mutation: its first local
delivery audit event is stored under tracked-worktree namespace before the
post-test candidate comparison.

The safe boundary is prior to project discovery/bootstrap: explicit ticket
wins; otherwise exactly one active governance ticket is deterministic. Audit
events are local operational evidence and belong below Git's common directory,
not in the candidate checkout.

## Execution plan

1. Add a fail-closed resolver for omitted pull-request ticket identity.
2. Invoke it before project bootstrap and prove bare `goal -a` reaches resume.
3. Move credential-free delivery events to the Git common directory and prove
   primary/linked checkout status remains unchanged.
4. Run focused, full, Ruff, governance, package and Docker validation.
5. Deliver through protected PR, exact-head Validator, closure and cleanup.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Captured the real todo2code delivery reproduction and bounded the repair to
  four implementation files in two existing components.
- Added deterministic ticket inference before project detection/bootstrap:
  explicit `--ticket` wins, exactly one `IN_PROGRESS` ticket is inferred, and
  zero/multiple candidates fail closed before mutation.
- Moved credential-free delivery events to
  `<git-common-dir>/goal-delivery/delivery-events.jsonl`, keeping primary and
  linked worktrees clean while preserving clone-local audit history.
- Added focused regressions for resolution, linked-worktree audit placement,
  unchanged candidate revalidation and the bare `goal -a` resume path.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
