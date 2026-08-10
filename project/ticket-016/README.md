# Ticket 016: Ignore governance payload in release classification

- **ID**: ticket-016
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10

## Goal and scope

Prevent governance-managed Python helpers such as `.governance/*.py` from
being classified as distributable package source.  Both staged-change and
committed-since-tag analysis use the same classifier, so one narrow exclusion
must keep documentation/governance-only delivery on the current version while
preserving releases for actual Python package modules.

## Acceptance criteria

- [x] AC-01: The user's autonomous continuation and publication request covers
  this blocking regression without another confirmation.
- [x] AC-02: `.governance/*.py` is non-publishable for staged and committed
  change analysis.
- [x] AC-03: Real source below `src/`, `goal/`, and top-level package paths
  remains publishable.
- [x] AC-04: Focused classifier/version tests and the full Python suite pass.
- [ ] AC-05: The governance gate passes and the fix is delivered through a
  protected PR with exact-head validator approval.

## Reproduction evidence

Running `goal -a --no-publish --delivery-mode pull-request` after the v0.14.1
adoption reported these files as package source and selected `2.1.290`:

- `.governance/check_required_checks.py`
- `.governance/decision_record.py`
- `.governance/governance_check.py`

The invalid generated release changes were removed and superseded by clean PR
#25; no false version was merged or published.

## Validation evidence

- Focused classifier/history tests: `15 passed`.
- Complete Python suite: `508 passed, 2 skipped`.
- `./project/governance-check.sh --base
  c5d706c81e77a59b4aec5e03afdfa6cb690e60c0`: PASS; 0 errors, 0 warnings.
- The positive committed-source and staged-source cases still recognize real
  package modules.

## Session authorization

The user explicitly requested autonomous execution and continuation of the
planned Goal test/publication/dependency work. This repair is a necessary,
bounded prerequisite and proceeds in `EDIT` without a redundant approval.
Trusted merge approval remains external and exact-head bound.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Boundary

Only the publishable-path classifier, its focused regression tests, and this
ticket's governance evidence may change. No package manifest, version file,
registry state, dependency, public CLI, or governance policy changes here.
