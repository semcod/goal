---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-019
---
# Participant: codex (AI agent)

## Understanding

Ticket-018 is merged and PyPI still exposes 2.1.290. Goal now correctly sees
the two post-transition package-source files and selects one patch release.

## Execution plan

1. Record the version decision and synchronize the 2.1.291 release carriers.
2. Run the full suite, build wheel/sdist, and pass fresh-base governance.
3. Deliver through a PR with Python 3.12/3.13 CI and exact-head validation.
4. Publish from clean merged main and verify a fresh public-index install.

## Blockers

- None inside the recorded intent; proceed autonomously.
- A registry or immutable-version conflict aborts publication rather than
  replacing an existing artifact.
