# Ticket 029: Keep publish-only artifacts on exact merged source

- **ID**: ticket-029
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-10

## Goal and scope

Make governed `publish-only` fail closed unless it starts from the exact clean
remote base commit, suppress Goal's own cost-badge mutation during bootstrap,
and re-check cleanliness after bootstrap so published artifacts are built from
the validator-approved Git tree without an intermediate local commit.

## Acceptance criteria

- [x] AC-01: The autonomous release run reproduced the defect from clean merged
  `main`: bootstrap changed README and created local commit `cf038b8`.
- [x] AC-02: `publish-only` rejects dirty input and a local HEAD different from
  the authoritative remote base before tests, build or publication.
- [x] AC-03: `publish-only` suppresses Goal's bootstrap badge mutation without
  leaking the Goal-only environment switch into project tests.
- [x] AC-04: A post-bootstrap mutation fails closed before staging or commit.
- [x] AC-05: Focused, full, governance and Docker validation pass, followed by
  target CI and exact-head validator approval.

## Validation evidence

- 23 focused delivery-integrity tests and the full suite of 528 tests with 2
  skips pass; Ruff reports no issues in the four implementation/test files.
- Package build and governance pass with zero errors and warnings.
- The production Docker image builds and reports Goal 2.1.294 offline.
- Goal correctly selects `normal-bump -> 2.1.295`; version carriers remain
  outside this application ticket and are deferred to integration.
- PR #60 passed Python 3.12 and 3.13 CI, received exact-head approval for
  `0db32811a8c54d79f5c086d7c09e016882e1d1cc`, and merged as
  `17b421b78acaa1fb526d5571c8071005eafe8508`.
- The merged ticket branch was removed from the remote.

## Session authorization

The user requested autonomous Goal refactoring, tests and publication. The
observed release-integrity regression is within that scope; no redundant
confirmation is required, while exact-head approval remains independent.

## Boundary

This application slice owns the publish-only guards, delivery validation and
their regression tests. Release metadata, dependencies, CI and registry
publication are excluded and remain integration work.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
