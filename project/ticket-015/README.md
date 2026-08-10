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
- [x] AC-02: Root `Dockerfile` uses Python 3.12 and contains no floating local
  dependency source outside the build context.
- [x] AC-03: The image builds and `docker run --rm IMAGE --version` reports the
  repository Goal version.
- [x] AC-04: Existing host tests remain green and the published v0.14.1 Docker
  stack profile recognizes the new root `Dockerfile` marker required by ticket
  013's adoption.

## Validation evidence

- `docker build -t goal-ticket015:verify .`: PASS; image
  `sha256:9ed9f1b4c7b55e98675c764e6e1bdb108922b16b21a1c6d8f4d2f13792191e31`.
- `docker run --rm --network none goal-ticket015:verify --version`: PASS;
  `goal, version 2.1.289`.
- `docker run --rm --network none --entrypoint python
  goal-ticket015:verify --version`: PASS; Python 3.12.13.
- `.venv/bin/python -m pytest tests -q`: PASS; 506 passed, 2 skipped.
- `./project/governance-check.sh`: PASS; 0 errors, 0 warnings. Ticket 013 now
  keeps its planning intent at v2 until schema v3 arrives atomically with the
  v0.14.1 adoption, so there is no mixed-schema delivery gap.

## Safety boundary

No Compose services, secrets, ports, registry push, dependency refresh or
application-source changes belong to this ticket. Session authorization is not
trusted merge approval.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
