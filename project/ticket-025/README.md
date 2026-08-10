# Ticket 025: Publish Goal 2.1.293 delivery-integrity fixes

- **ID**: ticket-025
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10

## Goal and scope

Publish the merged ticket-024 delivery-integrity fixes as Goal 2.1.293.
Synchronize the five atomic release carriers, pass the full test and protected
PR chain, publish wheel and sdist only from merged `main`, then verify a fresh
public-index installation.

## Acceptance criteria

- [x] AC-01: The user explicitly requested autonomous testing, publication and
  dependent-project updates.
- [x] AC-02: Goal selects `normal-bump -> 2.1.293` once and all release carriers
  are synchronized; a subsequent check selects `already-bumped`.
- [x] AC-03: Full tests, build, governance, target CI and exact-head validator
  pass before merge.
- [x] AC-04: Clean merged `main` publishes exactly one wheel and one sdist for
  2.1.293 through `goal -a --delivery-mode publish-only`.
- [x] AC-05: A fresh public-index environment reports Goal 2.1.293.

## Completion evidence

- Release PR #52 was exact-head validated at
  `d6ec0a2d49895326660d6807fc84580be3a6cf41` by validator run
  `31426414052` and merged as
  `5486c6249c27285ffd81595f2c4721d2de50fa14`.
- The clean publication shortcut discovered during release was repaired in
  ticket-026, validated in run `31427369125` and merged as
  `0b8f7563fe261b402dc9742ae187864261ce7c94`.
- `goal -a --delivery-mode publish-only --force-publish` ran 522 tests with
  2 skips and published exactly one wheel and one sdist without a release
  commit, tag or Git push.
- PyPI reports Goal 2.1.293 and a fresh Python 3.13 no-cache `uvx` environment
  reports `goal, version 2.1.293`.
- Published SHA-256: wheel
  `649c62990a831fef9016662ec399feb343bbfe1cb751babc9fe8d0df32e54834`,
  sdist `2aeb3a1361959e31456b1068c712e49f99b783eaebbe244f5845add81ed6a5a6`.

## Session authorization

The user authorized autonomous testing, publication and dependent-project
updates. No repeated confirmation is required for this exact release;
protected exact-head approval and registry credential boundaries remain
enforced.

## Boundary

This slice owns only `VERSION`, `pyproject.toml`, `uv.lock`,
`goal/__init__.py`, README release badges and ticket metadata. Source,
dependency constraints, top-level changelog, governance and CI are excluded.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
