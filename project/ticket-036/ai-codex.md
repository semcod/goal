---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-036
---
# Participant: codex

## Understanding

The standard now packages a deterministic local checker. Goal needs a thin,
headless dispatcher analogous to `governance check`, so agents can run the
terminal audit without embedding policy or destructive behavior in Goal.

## Execution plan

1. Add the workspace-check command and exact option forwarding.
2. Cover pass, failure, missing-package and headless dispatch behavior.
3. Run focused and complete validation without publication.

## Actual changes

- Added the headless `goal governance workspace-check` command.
- Resolved the checker only from the target's adopted `.governance` package.
- Forwarded the exact workspace root, repeated allowlisted paths and output
  format while preserving stdout, stderr and exit status.
- Added fail-closed and dispatch tests; 12 focused and 547 full tests pass,
  with 2 skips. Ruff and governance pass.

## Blockers

- None. PR #61 passed both CI jobs, merged to `main`, and its remote branch was
  removed.
