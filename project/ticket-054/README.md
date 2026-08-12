# Ticket 054: Remove the mutable local Compose image tag

- **ID**: ticket-054
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Remove the redundant mutable `image: goal:local` declaration from the
local-build-only Compose service. The service retains `build.context: .`, so
Compose continues to build and name an ephemeral project image without pulling
or advertising an unpinned external tag. This is the infrastructure-owned
prerequisite for ticket 053's new-project 0.16.1 adoption.

## Acceptance criteria

- [x] AC-01: `compose.yml` contains the local build and no mutable `image` key.
- [x] AC-02: `docker compose config` resolves a valid local-build-only service
      and the adopted 0.16.1 governance Docker rule passes in a bounded probe.
- [ ] AC-03: Full Goal tests and current governance pass before protected PR;
      hosted Python 3.12/3.13 CI, remote lifecycle and exact-head Validator
      approval are required before merge.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Validation evidence

- `docker compose config` resolves the service with the repository Dockerfile,
  isolated network and bind mount, without an `image` key.
- The exact published new-project 0.16.1 validator passes against this bounded
  diff; current deterministic governance also passes.
