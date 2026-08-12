---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-037
---
# Participant: codex (AI agent)

## Understanding

The current command proves only that a full SHA can be fetched, then runs an
executable generator which may label the lock `published`. This permits a
moving `main` commit with no immutable tag to become trusted production
provenance. Goal owns the acquisition boundary, so it must verify the
repository-native publication evidence before executing the generator.

## Execution plan

1. Add deterministic annotated-tag verification bound to `VERSION` and the
   requested full SHA.
2. Add an explicit unpublished-candidate test path which cannot be mistaken
   for normal production adoption.
3. Cover success, missing/lightweight/mismatched tag and test-only forwarding.
4. Run focused/full tests, Ruff, governance, build and Docker validation before
   publishing a one-ticket PR.
5. Add public GitHub Release metadata verification in a dependent bounded
   ticket after this one merges.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Audited the existing checkout: it fetches only the requested commit and does
  not verify a version tag before generator execution.
- The first combined implementation exceeded the S delivery budget; retained
  only the exact annotated-tag slice and deferred Release API proof.
- Added `VERSION`-matched annotated-tag acquisition and exact peeled-commit
  verification before generator execution.
- Added the explicit `--allow-unpublished-for-testing` boundary and forwarded
  it only to candidate-aware pinned generators.
- Added regression coverage for absent, lightweight and mismatched tags plus
  released and explicit-candidate success paths.
- Focused/full tests, scoped Ruff, governance, package and Docker builds pass.
- Delivered exact head `4032e04d` through PR #62, obtained deterministic
  Validator Agent approval, and merged it as `main@069b678`.
- Verified merge ancestry, then removed the remote head, local disposable
  branch and `/tmp/goal-ticket-037` worktree.

## Blockers

- GitHub Release API evidence remains the next dependent bounded ticket; this
  ticket intentionally proves only immutable repository-native tag evidence.
- No blocker remains for this bounded ticket. GitHub Release API evidence is
  owned by the dependent follow-up ticket.
