# Ticket 055: Make governed pull-request resume mutation-free and collision-safe

- **ID**: ticket-055
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Make governed pull-request delivery idempotent after a commit has already been
created. Resume must be classified and revalidated before bootstrap can mutate
the tree; ordinary PR bootstrap must not refresh unrelated cost badges; and
publication of the canonical remote head must not depend on creating a local
branch name that may legitimately remain from a merged attempt.

## Acceptance criteria

- [x] AC-01: A clean exact-ticket committed candidate resumes before bootstrap,
      TODO generation, staging or any Goal-owned metadata mutation, while still
      rerunning tests and revalidating the immutable candidate before delivery.
- [x] AC-02: Pull-request bootstrap and commit phases suppress Goal-owned cost
      badge refreshes without leaking that private control into project tests.
- [x] AC-03: Delivery pushes the current reviewed HEAD to the canonical remote
      `goal/ticket-NNN` ref without deleting, overwriting or checking out a
      colliding local branch; remote non-fast-forward safety remains intact.
- [x] AC-04: Focused tests, full tests, scoped Ruff, governance and Docker
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

## Validation evidence

- Remediation intent validation reports 2 findings, 3 actions, 0 errors and
  0 warnings at digest `e014ecda829f...`.
- Deterministic todo2code 0.5.0 analysis was rejected safely: the analyzer
  recorded 22 blocking scope expansions plus review hints for missing finding
  and acceptance links instead of allowing unrelated historical plans.
- Focused delivery tests pass: 51 passed. Full tests pass: 604 passed with
  2 existing skips. Scoped Ruff and formatting checks pass.
- Explicit changed-file governance passes with 0 errors and 0 warnings.
  Docker build and `goal --version` smoke test pass for the validation image.
- The real mutation-free resume reran 604 tests (2 skips) and published exact
  head `2ba40a5955fa...` as PR #89 without changing the clean worktree.
  Hosted Python 3.12/3.13 CI and remote lifecycle passed; trusted Validator App
  review `4918403955` approved that exact head, and PR #89 merged as
  `da81ad9b221e...`.
- Closure attempt PR #90 was closed without merge and its remote branch deleted
  after incomplete commit-only flags prepared release carriers outside scope.
  The replacement uses the explicit four-flag commit-only contract.
