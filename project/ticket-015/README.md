# Ticket 015: Add required Python 3.12 Docker entrypoint

- **ID**: ticket-015
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10

## Goal and scope

Add the required root Docker entrypoint that the published governance standard
expects for a repository declaring the Docker stack. The image must use Python
3.12, matching `requires-python >=3.12`, install the local Goal package and
provide `goal` as its entrypoint. This is a narrow prerequisite for ticket 013;
the eight-project integration matrix remains ticket 012. The published v0.14.1
target contract also requires a Compose declaration when Docker is required,
so the root CLI service must run without allocating a Docker network pool.

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
- [x] AC-05: `compose.yml` validates, runs the Goal entrypoint, and uses
  `network_mode: none` so it cannot consume a host address pool.

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
- `docker compose config --quiet`: PASS.
- `docker compose build goal`: PASS.
- `docker compose run --rm goal --version`: PASS; Goal 2.1.289.
- Post-run inspection found no Compose container or project network; the
  resolved service has `network_mode: none`.

## Safety boundary

No long-running service, secret, port, registry push, dependency refresh or
application-source change belongs to this ticket. The Compose service is only
a network-isolated CLI entrypoint. Session authorization is not trusted merge
approval.

## Publication

- Goal created [PR #21](https://github.com/semcod/goal/pull/21).
- GitHub CI passed on Python 3.12 and 3.13.
- `ifuri-validator-agent` approved exact head
  `105c297fecaa5adcedc24219f7c5404c5fe907d0`.
- The protected PR merged as
  `bd9d6076c24f1a9297eb4dce073c43236dac9b43`.
- Compose follow-up [PR #22](https://github.com/semcod/goal/pull/22) passed both
  CI jobs, was approved by the trusted validator at
  `61b018dcd37127ca13173de7295a8ac34204d3f5`, and merged as `9ef73d2`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
