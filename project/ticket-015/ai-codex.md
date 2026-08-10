---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-015
---
# Participant: codex (AI agent)

## Understanding

The v0.14.1 adoption correctly requires a root Docker marker because Goal
declares the Docker stack. The repository only has an integration image on
unsupported Python 3.11. A minimal root CLI image on Python 3.12 removes the
bootstrap blocker without mixing the later dependency/matrix work into the
governance-adoption PR.

## Execution plan

1. Record the bounded autonomous infrastructure intent.
2. Add a minimal Python 3.12 slim image that installs the checked-in package.
3. Build it, run `goal --version`, and run the relevant host tests.
4. Publish one protected PR and merge only after CI and independent exact-head
   approval, then resume ticket 013 from the new main SHA.

## Actual changes

- Added a digest-pinned Python 3.12 slim image that copies and installs the
  checked-in Goal package, exposes `goal` as its entrypoint and defaults to
  `--help`.
- Built the image and verified Goal 2.1.289 plus Python 3.12.13 with runtime
  networking disabled.
- Passed the complete host suite: 506 tests passed and 2 optional tests skipped.
- Verified that v0.14.1 declares root `Dockerfile` as the required Docker stack
  marker needed by the pending adoption.

## Blockers

- None inside this intent. The old installed checker passes after ticket 013's
  planning intent was kept at v2 until the atomic standard migration. Trusted
  exact-head merge approval remains external.
