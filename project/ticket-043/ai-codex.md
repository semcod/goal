---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-043
---
# Participant: codex (AI agent)

## Understanding

Goal 2.1.295 lacks the fixes already integrated on `main`: source hub layout
diagnostics from ticket-041 and the help/commit-only coherence repair from
ticket-042. `new-project` must use the Goal package for health and delivery, so
continuing with only an editable checkout would reproduce the exact gap the
user asked to remove.

## Execution plan

1. Commit the bounded release plan before touching carriers.
2. Use Goal's high-level pull-request workflow to select and synchronize
   2.1.296 without registry/tag side effects.
3. Validate locally, in protected CI and by exact-head Validator App review.
4. Merge only that head; retest clean merge and publish via governed
   publish-only plus separately verified immutable GitHub release evidence.
5. Verify a fresh public install and remove all release worktree/image files.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Confirmed `main@3fb66ab` is clean, equals `origin/main`, has only remote
  `main`, zero open PRs, and contains the clean-merge-validated ticket-041/042
  implementation.
- Confirmed the 2.1.296 registry/tag/Release namespace is unused before
  entering `PUBLICATION`; the release plan remains a separate prior commit.
- Used the real Goal PR workflow to synchronize the five carriers, run all 573
  passing tests (2 existing skips), skip premature release side effects and
  create PR #68.
- Passed deterministic governance, exact carrier checks, wheel/sdist and
  Docker builds; recorded artifact/image hashes and removed the temporary
  validation image.
- Obtained trusted Validator App approval for exact head `b99fdd1`, merged PR
  #68 as `main@c5f3684`, and repeated the complete clean-merge validation.
- Published exactly one wheel and one sdist through governed `publish-only`,
  then created annotated `v2.1.296` and the final GitHub Release from the
  verified merge SHA. PyPI and Release downloads match the recorded hashes.
- Installed 2.1.296 without cache from the public PyPI index and proved that
  public `goal push --help` is read-only in a fresh empty directory.

## Blockers

- None. The bounded release is complete.
