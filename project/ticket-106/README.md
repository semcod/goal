# Ticket 106: Register adoption controller integration ownership

- **ID**: ticket-106
- **Owner**: agent:codex-adoption-pilot
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-14

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-09-14 the user authorized executing
and publishing the resumable adoption pilot. The subsequent explicit approval
permits assigning only goal/governance/adoption_transaction.py and
 tests/test_adoption_transaction.py to integration in Goal's local manifest.
It does not authorize changes to wellmanifest standards or broader ownership.

This delivery registers initial integration ownership for these two new,
unpublished paths. It does not move an existing runtime component, implement
persistent data changes, or broaden ownership wildcards.

The original controller implementation, tests, intent and ticket description
are preserved in the private integration-handoff under the external state
record adoption-transaction-pilot-106-20260914. Their original implementation
criteria transfer to existing integration ticket-107 after this mapping is
independently accepted. Documentation is already held by ticket-107.
No controller test success or live adoption is claimed by this ticket.

## Acceptance criteria

- [ ] AC-01: Only the two approved exact paths are added to integration ownership; the managed governance gate passes.
- [ ] AC-02: Existing governance delivery tests pass without weakening their assertions or policy.
- [ ] AC-03: The diff passes whitespace checks and is published through independent exact-head review and protected merge.

## Tracking boundary

This README and intent track the manifest change. They are not approval
receipts and do not close the ticket. The protected delivery controller owns
terminal reconciliation. Raw logs and preserved source remain outside Git.
