---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-046
---
# Participant: codex (AI agent)

## Understanding

Ticket-041 correctly prevented the maintained source hub from being mistaken
for an adopted target, but both the headless check command and governed
delivery now stop at that distinction.  This makes `new-project`'s own rule to
publish through Goal impossible to satisfy.  The repair is a Goal-owned,
read-only source-hub runner over the hub's authoritative files and suites.

## Execution plan

1. Commit the bounded ticket plan on current `origin/main` before source edits.
2. Add one shared source-hub health runner with deterministic discovery,
   coverage and fail-closed execution semantics.
3. Route both `goal governance check` and the delivery governance gate through
   that runner while preserving adopted-target behavior.
4. Add focused regression tests for success, malformed input, unwired/failed
   suites and the target/source-hub distinction.
5. Run focused/full tests, Ruff, governance, package and Docker checks; publish
   through the required exact-head PR and Validator App boundary.
6. Publish a patch release, verify it from a fresh public install, use it for
   the live `new-project` candidate delivery, then remove all ticket resources.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Confirmed public Goal 2.1.296 rejects both the headless source-hub check and
  dry-run governed source-hub delivery before executing any health suite.
- Implemented one shared source-hub health runner in the existing delivery
  module and routed both headless check and delivery through it.
- Made the runner validate every canonical top-level governance JSON document,
  require every shell suite to be declared by CI, execute the required-check
  comparator and each suite without shell interpolation, and fail if a
  successful run changes Git state.
- Passed 54 focused tests, focused Ruff and adopted governance.  The real
  ticket-065 source hub passed 15 JSON documents and 9 shell suites without a
  status change; governed delivery dry-run reached normal Goal processing.
- Passed the full 581-test suite with 2 existing skips plus wheel, sdist and
  Docker builds, then removed every generated build artifact and image.
- Committed the validated implementation as `fec3d73` and moved the owning
  ticket to `PUBLICATION` for governed exact-head pull-request delivery.

## Blockers

- None inside the recorded intent; external validation and release remain
  later publication gates.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
