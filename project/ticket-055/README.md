# Ticket 055: Make governed pull-request resume mutation-free and collision-safe

- **ID**: ticket-055
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Make governed pull-request delivery idempotent after a commit has already been
created. Resume must be classified and revalidated before bootstrap can mutate
the tree; ordinary PR bootstrap must not refresh unrelated cost badges; and
publication of the canonical remote head must not depend on creating a local
branch name that may legitimately remain from a merged attempt.

## Acceptance criteria

- [ ] AC-01: A clean exact-ticket committed candidate resumes before bootstrap,
      TODO generation, staging or any Goal-owned metadata mutation, while still
      rerunning tests and revalidating the immutable candidate before delivery.
- [ ] AC-02: Pull-request bootstrap and commit phases suppress Goal-owned cost
      badge refreshes without leaking that private control into project tests.
- [ ] AC-03: Delivery pushes the current reviewed HEAD to the canonical remote
      `goal/ticket-NNN` ref without deleting, overwriting or checking out a
      colliding local branch; remote non-fast-forward safety remains intact.
- [ ] AC-04: Focused tests, full tests, scoped Ruff, governance and Docker
      validation pass with no release/version/dependency changes.

## Reproduced incidents

- Ticket 053 PR #87 resume ran cost bootstrap before candidate recognition and
  generated an out-of-scope README badge commit; the change had to be restored.
- Ticket 053 closure passed 600 tests and committed evidence, then failed with
  `a branch named 'goal/ticket-053' already exists` until the already-merged
  local branch was manually removed.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
