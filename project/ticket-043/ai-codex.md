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

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
