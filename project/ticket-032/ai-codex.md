---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-032
---
# Participant: codex (AI agent)

## Understanding

`new-project` currently publishes shell and batch wrappers that invoke the
adopted Python validator directly. Goal already owns governance adoption and
delivery, but its CLI has no standalone validator entrypoint. A thin command
adapter closes that gap without moving policy ownership into Goal.

## Execution plan

1. Resolve and validate the target's adopted governance package.
2. Run its deterministic validator with canonical paths and forwarded options.
3. Preserve process output and exit status, including fail-closed setup errors.
4. Add CLI regressions and run the full Goal validation contract.
5. Leave `new-project` wrapper migration to its own governed ticket.
6. Ensure this gate bypasses Goal's interactive user bootstrap, mutable project
   configuration and network-facing version update path.
7. Extend the read-only dispatcher boundary to the governance group so
   `adopt`, its help path and target-root execution cannot create `goal.yaml`
   in the caller; retain explicit config opt-in in delivery callbacks.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Added `goal governance check` as a thin process adapter over the target's
  adopted `.governance` package.
- Reserved manifest, lock, root and stack-profile options to prevent callers
  from escaping the pinned package, while forwarding ordinary validator flags,
  output and exact exit status.
- Added success, nonzero, missing-package, override and read-only-context
  regressions; passed 9 focused, 20 governance/delivery and 532 full tests,
  Ruff, governance, build and Docker validation.
- Verified the real Goal package passes and `glon` reports a precise missing
  adoption error before any mutation.
- Made the exact `governance check` dispatch path read-only and headless: it
  skips interactive user setup, config creation, binary warnings, the version
  banner and update lookup. A clean offline container now reaches only the
  expected fail-closed adoption result.
- Removed unused imports exposed by changed-file Ruff while preserving the
  existing public `sync_all_versions` re-export.
- Reproduced a remaining dispatcher side effect during exact-SHA downstream
  validation: `governance adopt` created `goal.yaml` in the caller even though
  `--target-root` named another repository. Reopened this same-scope ticket and
  recorded the bounded read-only group repair before editing code.

## Blockers

- None inside the recorded intent; proceed with the same bounded session
  authorization and no second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
