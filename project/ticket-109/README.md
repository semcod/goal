# ticket-109: Existing Goal adoption command adapter

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- Workstream: integration
- Agent: codex
- Owner: agent:codex-adoption-pilot

## Intent

Connect the accepted adoption transaction to the existing immutable Goal CLI
without implementing a second adoption engine or treating command output as a
receipt. The protected delegate continues to own authorization, readback and
later validation/publication/merge phases.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: the user's requests to continue Goal automation,
test, publish and merge authorize this bounded implementation and the declared
independent exact-head delivery process. This note is not merge approval.

## Acceptance criteria

- AC-01: The adapter invokes the existing pinned adoption command with fixed
  arguments; an isolated integration fixture exercises its generator path.
- AC-02: Subject/key changes, stale planning inputs and denied authority prevent
  execution. Timeout kills the process group; no command result creates an
  APPLIED receipt or permits blind retry.
- AC-03: Managed governance, focused and stack checks pass before independent
  review and protected merge of the exact head.

## Limits

No live adopter, shared deployment, standard pin, required check or credential
configuration is changed. Production receipt and authority providers remain a
separate integration prerequisite. No package release is claimed.
