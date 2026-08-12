# Ticket 038: Require GitHub Release evidence before standard adoption

- **ID**: ticket-038
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Close the remaining publication-proof gap in `goal governance adopt`. After
the exact annotated tag is verified, normal production adoption must also
fetch the canonical `wellmanifest/new-project` GitHub Release for that tag and
require a published, non-draft, non-prerelease record. The explicit candidate
testing path remains network-free and unchanged.

## Acceptance criteria

- [x] AC-01: Normal adoption rejects a missing, draft, prerelease, mismatched or
  otherwise incomplete GitHub Release before generator execution.
- [x] AC-02: A canonical published GitHub Release plus the exact annotated tag
  permits the existing adoption, `--check` and `--upgrade` flows.
- [x] AC-03: `--allow-unpublished-for-testing` bypasses both production proofs
  and remains explicitly forwarded to the candidate-aware generator.
- [x] AC-04: Focused/full tests, scoped Ruff, governance, package and Docker
  builds pass without live network access in the test suite.

## Boundary

- This ticket adds only GitHub Release metadata verification to the existing
  standard-acquisition boundary.
- It does not change package versions, dependencies, generator lock semantics
  or the canonical `new-project` repository.
- Generator-side unpublished provenance is owned by the dependent
  `new-project` ticket.

## Validation evidence

- 24 focused governance command tests pass; every GitHub response is stubbed.
- The full suite passes with 559 tests and 2 existing skips.
- Scoped Ruff and deterministic governance pass.
- A live pilot accepted canonical `v0.14.1@63a3d56` using its annotated tag and
  published GitHub Release, then removed the temporary target.
- Python wheel/sdist and Docker image builds pass; temporary build output and
  generated `goal.egg-info` were removed after verification.
- PR #63 passed Python 3.12/3.13 CI, received deterministic Validator Agent
  approval for exact head `35047d61703859d32667f36c26c88ba5781189e5`, and
  merged as `main@2d9873cdd8d1180b42ab0461c548dbe327b66ee2`.
- GitHub automatically deleted the merged remote head. After ancestry and
  tracked-tree checks, the disposable branch and complete worktree were
  removed together with all ignored test caches and its local delivery log.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
