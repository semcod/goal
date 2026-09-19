# Ticket 170: Adopt wellmanifest standard 0.20.32

- **ID**: ticket-170
- **Owner**: codex-fleet-goal170-handoff-20260919
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-19

## Goal and scope

Adopt the verified wellmanifest/new-project 0.20.32 managed package atomically,
including its packaging binding. Preserve the documentation adoption already
merged in PR #170 and validate against main at 969357f9d84402c6fd34c422571a7992886e08bb.

SESSION_EXECUTION_AUTHORIZATION: the user requested autonomous delivery and
explicitly confirmed the previous owner's completion and handoff of tickets
170, 171 and 172 on 2026-09-19. Protected exact-head review still owns merge.

## Acceptance criteria

- [x] AC-01: Managed package and packaging binding pass governance validation on the current accepted base.
- [x] AC-02: Existing Python regression suite passes (899 passed, 2 skipped).
- [ ] AC-03: Protected CI and independent Validator accept the published exact head.

## Reconciliation

The helper ticket 171 packaging delta is identical to this adoption's binding.
Ticket 172's separate integration-ownership policy proposal remains preserved
for later evaluation; it is not needed by the standard's atomic adoption rule.
External recovery receipts retain both helpers' uncommitted material.
