---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-039
---
# Participant: codex (AI agent)

## Understanding

The migration added in ticket-033 uses global text replacement before locating
the development dependency list. A runtime `costs` requirement therefore gains
a tool-only marker during `goal -a`. The migration belongs inside the dev-list
slice, while the missing-tool decision may still consider the whole project.

## Execution plan

1. Move legacy replacement into the selected optional/Hatch dependency slice.
2. Preserve whole-project detection that avoids duplicate Goal tooling.
3. Prove runtime requirements remain unchanged and dev migration is idempotent.
4. Run the complete validation chain before protected exact-head delivery.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Reproduced the mutation on Goal's own `pyproject.toml`: bootstrap proposed a
  runtime `costs` marker and a dev `pfix` marker.
- Scoped legacy replacement to the selected development list and retained
  missing-tool detection across the project document.
- Added a runtime-preservation regression test; three focused tests and Ruff
  pass.
- Passed 560 full tests (2 skipped), governance, package and Docker builds.
- Confirmed the real Goal transform now preserves runtime `costs` and proposes
  only the expected dev `pfix` marker.
- Removed temporary build output and generated `goal.egg-info`.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
