# Ticket 092: Published github-script v9 governance

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Owner**: codex

SESSION_EXECUTION_AUTHORIZATION: The user requested continued Semcod publication and implementation. Adopt the published HOME standard package to supersede PR 125, then publish through independent exact-head review.

## Acceptance criteria
- [x] AC-01: Adopt immutable new-project 0.20.13, preserving target settings and package bindings.
- [ ] AC-02: Managed governance, Compose and Python CI pass before trusted publication; supersede PR 125 after merge.

Validation: The managed updater verified the published immutable source. Docker engine and Compose checks pass. Governance and required Python CI are publication gates; trusted merge remains pending.
