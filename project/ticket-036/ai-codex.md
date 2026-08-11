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

- Planned the immutable-package adapter.

## Blockers

- None.

