---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-048
---
# Participant: codex (AI agent)

## Understanding

The real `new-project` 0.16.0 direct-main run proved a delivery gap in Goal
2.1.297. The non-registry generic project published no package artifacts, which
is correct, and Goal created the exact annotated tag. Its `create_on_tag`
helper nevertheless reused the PyPI fallback rule requiring `dist/*`, skipped
the GitHub Release and returned overall success. A second run would see the
existing tag and skip the release hook entirely.

The fix must preserve artifact-strict registry fallback, allow no-asset GitHub
Releases only when the caller knows the project is generic, validate recovery
tags as annotated and exact-HEAD, and make governed direct-main fail if its
configured Release side effect fails.

## Execution plan

1. Commit this bounded plan at exact clean `origin/main` before source edits.
2. Add explicit internal assetless handling to GitHub Release creation without
   changing the package fallback default.
3. Add exact-HEAD annotated-tag recovery for clean direct-main retries.
4. Require configured create-on-tag success in governed direct-main mode.
5. Run focused/full tests, Ruff, adopted governance and Docker.
6. Deliver one protected PR, obtain exact-head approval and merge only that
   SHA; then use the merged code to complete new-project v0.16.0.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Captured the real failure: new-project annotated `v0.16.0` peels to clean
  merge `6800f013...`, while GitHub Release is absent because Goal logged
  `no dist artifacts for version 0.16.0` and still returned success.
- Added an explicit internal assetless mode while keeping the package fallback
  default artifact-strict; generic create-on-tag is its only caller.
- Added exact annotated-tag recovery for clean direct-main retries and made a
  configured Release failure terminal in governed direct-main mode.
- Passed 30 focused tests, 588 full tests with 2 existing skips, scoped Ruff,
  governance, wheel/sdist and pinned-base Docker validation. No dependency or
  version carrier changed, and generated validation outputs were removed.
- Moved the active ticket to `IN_PROGRESS / PUBLICATION` for independent
  exact-head hosted validation and trusted merge.
- Detected that public Goal refreshed and committed the root AI-cost badge
  after its governance gate. Reverted that out-of-scope drift as a second
  local commit and kept it unpushed until a guarded Goal retry could deliver a
  zero-net README diff through the same PR.
- PR #72 exact head `ef0414d...` passed Python 3.12/3.13 CI and Validator App
  run `31596882004`, then merged as `main@320ad3d` with an identical tree.
- The clean merge passed 588 tests (2 skipped) and governance, but the real
  new-project retry stopped fail-closed at `normal-bump -> 0.16.1`. The version
  decision guard runs before the exact-tag recovery added by PR #72.
- Returned the same active ticket to `EDIT`: recognize only a clean, governed,
  generic create-on-tag repair with a `normal-bump` decision and an existing
  annotated current-version tag at exact HEAD, then retain normal first-release
  and package behavior.
- Refreshed the accepted base from the original ticket allocation SHA to the
  trusted PR #72 merge `320ad3d`; scope, architecture and budgets are unchanged.
- Added a full-workflow regression for the observed normal-bump ordering and
  narrowed recovery to clean generic direct-main with configured create-on-tag.
  The decision becomes `existing-tag-release-repair -> 0.16.0` only after
  exact annotated current-version tag verification.
- Passed 34 focused and 592 full tests (2 skipped), scoped Ruff, governance,
  wheel/sdist and pinned-base Docker validation; temporary outputs were removed.
- Moved the active ticket back to `PUBLICATION` for a protected follow-up PR.
- PR #73 exact head `f4435f2...` passed Python 3.12/3.13 CI and Validator run
  `31598288598`, then merged as `main@b214711`; its clean merge passed 592
  tests (2 skipped) and governance.
- The real flow then created final, assetless v0.16.0 with no Git/tag change,
  proving version recovery. It also exposed a metadata leak: the Release title
  used temporary checkout name `new-project-v0160-release-repair` instead of
  configured project name `new-project`.
- Returned the same active ticket to `EDIT` to resolve the canonical project
  name from Goal config and reconcile title/notes when the Release exists.
- Refreshed accepted base to trusted PR #73 merge `b214711`; ticket scope,
  architecture and budgets remain unchanged.
- Resolved Release display identity from `project.name`, reconciled title and
  notes for existing assetless Releases, and shell-quoted every mutable `gh`
  argument in this path.
- Passed 36 focused and 594 full tests (2 skipped), scoped Ruff, governance and
  pinned-base Docker; removed the temporary image and re-entered `PUBLICATION`.
- Public Goal committed the validated candidate but found the old local
  `goal/ticket-048` alias from already merged PR #73. Verified that alias was
  an ancestor of `origin/main`, deleted only the local ref, and retained the
  candidate commit for a guarded delivery retry.
- PR #74 exact head `c65916f...` passed Python 3.12/3.13 CI and Validator App
  run `31599336116` with approval review `4916776878`, then merged as
  `main@db2da6e`; the clean merge passed 594 tests (2 skipped) and governance.
- Re-ran the real clean `new-project` repair from merged Goal. It reused exact
  annotated `v0.16.0`, changed zero files, edited the existing assetless
  Release to canonical title `new-project v0.16.0`, and left both remote main
  and the peeled tag at `6800f013...`.
- Marked all acceptance criteria and the ticket `DONE / DONE` after recording
  immutable production evidence.

## Blockers

- None.
