---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-048
---
# Participant: codex (AI agent)

## Understanding

The real `new-project` 0.16.0 direct-main run proved a delivery gap in Goal
2.1.297. The non-registry generic project published no package artifacts, which
is correct, and Goal created the exact annotated tag. Its `create_on_tag`
helper nevertheless reused the PyPI fallback rule requiring `dist/*`, skipped
the GitHub Release and returned overall success. A second run would see the
existing tag and skip the release hook entirely.

The fix must preserve artifact-strict registry fallback, allow no-asset GitHub
Releases only when the caller knows the project is generic, validate recovery
tags as annotated and exact-HEAD, and make governed direct-main fail if its
configured Release side effect fails.

## Execution plan

1. Commit this bounded plan at exact clean `origin/main` before source edits.
2. Add explicit internal assetless handling to GitHub Release creation without
   changing the package fallback default.
3. Add exact-HEAD annotated-tag recovery for clean direct-main retries.
4. Require configured create-on-tag success in governed direct-main mode.
5. Run focused/full tests, Ruff, adopted governance and Docker.
6. Deliver one protected PR, obtain exact-head approval and merge only that
   SHA; then use the merged code to complete new-project v0.16.0.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Captured the real failure: new-project annotated `v0.16.0` peels to clean
  merge `6800f013...`, while GitHub Release is absent because Goal logged
  `no dist artifacts for version 0.16.0` and still returned success.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
