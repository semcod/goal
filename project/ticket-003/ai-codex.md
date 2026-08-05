---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-003
---
# Participant: Codex (AI agent)

## Understanding

Governance should decide whether Goal may deliver directly to `main`, publish
without a Git remote push, or take ownership of branch push and PR creation.
The decision belongs at the start of `goal -a`, while the local hook prevents
accidental raw pushes and server protection supplies the real trust boundary.

## Execution plan

1. Wait for completion of ticket-002 and approval of this scope.
2. Add and validate the delivery policy model.
3. Thread the resolved mode through the existing push workflow.
4. Add transaction authorization, audit events, and managed hook commands.
5. Implement the three delivery adapters without implicit fallback.
6. Add isolated tests and operator documentation.
7. Run the adopted governance gate and ticket-scoped tests only after explicit
   authorization to validate.

## Actual changes

- Ticket plan and intent only; application code remains unchanged.

## Blockers

- Ticket-002 remains `WAIT_FOR_APPROVAL`; its intent currently forbids edits to
  `goal/**`, `tests/**`, and documentation.

## Response routing

- responseRequiredFrom: `unresolved:human`
