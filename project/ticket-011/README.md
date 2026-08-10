# Ticket 011: Eliminate duplicate docs-only commit attempt

- **ID**: ticket-011
- **Owner**: session user (identity unresolved)
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / delivery`

## Goal and scope

Make docs/metadata-only delivery perform exactly one commit attempt, never let
the test suite commit into the repository executing the tests, and stop before
publish/tag/push when the real commit fails.  Preserve the `no-release`
decision: no version bump, release tag or registry publication is introduced.

## Acceptance criteria

- [x] AC-01: The user approved continuation after the duplicate commit symptom
  was reported.
- [ ] AC-02: The metadata-only workflow test cannot execute a real Git commit
  in its caller's repository.
- [ ] AC-03: A successful docs-only workflow requests exactly one plain commit,
  skips version bump/publication/tag and can continue to push.
- [ ] AC-04: A failed docs-only commit aborts before publish, tag or push and
  cannot be reported as a successful workflow.
- [ ] AC-05: Focused tests, the full suite and governance validation pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

After the completed ticket-010 delivery explicitly identified the remaining
duplicate empty-commit report, the user instructed the agent to continue.  This
authorizes this narrowly scoped correction and transition to
`IN_PROGRESS / EDIT`.

## Boundary

This ticket does not change version selection, release publication, registry
credentials, delivery policies or GitHub configuration.
