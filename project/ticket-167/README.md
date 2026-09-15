# Ticket 167: Make `goal -a` force publication by default

- **ID**: ticket-167
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-09-15

## Goal and scope

Make the `goal -a` / `goal --all` workflow carry the same force-publication
intent as `--force-publish`, so a clean tree with already-committed package
changes still reaches the configured publisher. Keep explicit `--no-publish`
as an opt-out and preserve the governed pull-request boundary that waits for
PR merge before registry publication.

## Acceptance criteria

- [x] `-a/--all` sets force-publication intent in the main CLI context.
- [x] Compatibility command and workflow callers infer the same intent from
      `all_flags`.
- [x] `--no-publish` still suppresses publication.
- [x] Regression tests cover the CLI and workflow boundary.

## Tracking boundary

The implementation is limited to the Goal CLI/workflow and its regression
tests. Documentation changes are intentionally deferred to a follow-up
integration ticket because this ticket uses the application workstream.

SESSION_EXECUTION_AUTHORIZATION: the user requested that every `goal -a`
invocation force publication. This ticket is the implementation authorization;
protected review and publication remain required. No self-approval or direct
merge.

## Validation evidence

- Managed governance gate: `GOV-PASS: passed (0 errors, 0 warnings)`.
- Focused workflow and delivery tests: `108 passed`.
- Full Goal suite: `899 passed, 2 skipped`.
- Ruff: all changed Python files pass.
