# Ticket 184: Keep governed publication bootstrap read only

- **ID**: ticket-184
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-07

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user asks repair dependencies, push, protected merge and publish via `goal -a`. Actual SDK publish-only attempts mutate source then fail guard; preserve trusted source while preparing environments. Own four-file scope in intent, canonical relative checkout and bounded fenced lease. Parent operational request: Willman PLF-112/GH172.

## Acceptance criteria

- [x] AC-01: Governed Python bootstrap leaves configuration, lockfiles and missing test paths unchanged; installer and marker regression checks pass.
- [ ] AC-02: Managed gate and full tests pass; OneDev and independent Validator approve exact HEAD and protected controller merges.
