# Ticket 060: Repair Goal publish strategy configuration

- **ID**: ticket-060
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Repair Goal's own tracked Python publish strategy so it matches the retry-safe
runtime, doctor and producer contract delivered by tickets 058 and 059. The
change is limited to one scalar in `goal.yaml`; the existing Node and Rust
strategies must remain byte-for-byte unchanged.

## Acceptance criteria

- [x] AC-01: The user's instruction to repair and continue records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded configuration fix.
- [x] AC-02: `strategies.python.publish` is the canonical retry-safe Goal
  artifact command.
- [x] AC-03: The Node and Rust publish commands remain `npm publish` and
  `cargo publish` respectively.
- [x] AC-04: Structural parsing, full tests and governance pass before
  protected exact-head delivery.

## Non-goals

- Do not change Goal runtime, doctor or configuration producers.
- Do not change versions, dependencies, Node/Rust behavior or CI.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Validation evidence

- Structural YAML parsing proves the Python command equals
  `twine upload --skip-existing dist/goal-{version}*`, while Node and Rust
  remain `npm publish` and `cargo publish`.
- The implementation diff is exactly one insertion and one deletion in
  `goal.yaml`.
- The full suite passes 618 tests with 2 existing skips; governance reports
  0 errors/0 warnings and whitespace validation passes.
