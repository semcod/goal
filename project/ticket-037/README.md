# Ticket 037: Fetch immutable new-project release evidence during adoption

- **ID**: ticket-037
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Make `goal governance adopt` fail closed before it executes a pinned standard
generator unless the requested commit is the exact commit behind the
version-matched annotated tag. Keep candidate testing possible only through an
explicit test-only option which is never represented as production
publication evidence. GitHub Release metadata verification is a dependent
follow-up slice after this bounded repair merges.

## Acceptance criteria

- [x] AC-01: Normal adoption rejects a fetchable full SHA when no exact
  annotated `v<VERSION>` tag proves it is an immutable release.
- [x] AC-02: A published release SHA fetches and verifies its exact annotated
  tag, then preserves existing `--check` and `--upgrade` behavior.
- [x] AC-03: Candidate testing requires an explicit
  `--allow-unpublished-for-testing` option and forwards that boundary to the
  pinned generator.
- [x] AC-04: Focused tests, the full Python suite, Ruff, governance and package
  build pass without network access in the test suite.

## Risks and controls

- A matching annotated tag is necessary but GitHub Release metadata remains a
  separate proof; the dependent ticket must add it before the next Goal
  publication.
- The test-only option is explicit, produces no production claim and is not a
  merge or release bypass.

## Validation evidence

- 16 focused governance command tests pass.
- 551 full tests pass; 2 are skipped by the existing suite.
- Scoped Ruff, deterministic governance, package build and Docker build pass.
- A live local-mirror pilot accepts released `v0.14.1@63a3d56` and rejects
  unpublished `main@e88a6d2` because the tag resolves to a different commit.
- PR #62 passed Python 3.12/3.13 CI, received deterministic Validator Agent
  approval for exact head `4032e04d706f75c0ce8f3ab2c9129d78d6c2b7f7`, and
  merged as `main@069b678d056a9b4ace9b731fd62716fc4aa7172d`.
- GitHub automatically deleted the merged remote head; the clean local
  worktree and its disposable branch were removed after ancestry verification.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
