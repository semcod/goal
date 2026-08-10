# Ticket 015: Add required Python 3.12 Docker entrypoint

- **ID**: ticket-015
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10

## Goal and scope

Add the required root Docker entrypoint that the published governance standard
expects for a repository declaring the Docker stack. The image must use Python
3.12, matching `requires-python >=3.12`, install the local Goal package and
provide `goal` as its entrypoint. This is a narrow prerequisite for ticket 013;
the eight-project integration matrix remains ticket 012.

## Acceptance criteria

- [x] AC-01: The user's explicit request to update Docker, test and publish
  authorizes this bounded infrastructure prerequisite without another prompt.
- [ ] AC-02: Root `Dockerfile` uses Python 3.12 and contains no floating local
  dependency source outside the build context.
- [ ] AC-03: The image builds and `docker run --rm IMAGE --version` reports the
  repository Goal version.
- [ ] AC-04: Existing host tests remain green and ticket 013's adopted
  governance no longer reports missing Docker markers.

## Safety boundary

No Compose services, secrets, ports, registry push, dependency refresh or
application-source changes belong to this ticket. Session authorization is not
trusted merge approval.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
