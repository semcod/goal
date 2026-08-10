# Ticket 023: Publish Goal 2.1.292 Python carrier fix

- **ID**: ticket-023
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10

## Goal and scope

Publish the merged ticket-021 Python version-carrier fix as Goal 2.1.292.
Synchronize the five atomic release carriers, pass the full test and protected
PR chain, publish wheel and sdist only from merged `main`, then verify a fresh
public-index installation.

## Acceptance criteria

- [x] AC-01: The user explicitly requested autonomous testing, publication and
  dependent-project updates.
- [x] AC-02: Goal selects `normal-bump -> 2.1.292` once and all release carriers
  are synchronized.
- [x] AC-03: Full tests, build, governance, target CI and exact-head validator
  pass before merge.
- [x] AC-04: Clean merged `main` publishes exactly one wheel and one sdist for
  2.1.292 through `goal -a --delivery-mode publish-only`.
- [x] AC-05: A fresh public-index environment reports Goal 2.1.292.

## Completion evidence

- Release PR #41 was exact-head validated at
  `11ba5706674bffa620b5bb73c8808a6e4e36519f` and merged to protected `main`
  as `788ae1499c7c95e8e97bcfc017c0ead27eb73515`.
- Validation completed with 512 passed and 2 skipped tests, a successful wheel
  and sdist build, and a clean governance report.
- `goal -a --delivery-mode publish-only --force-publish` published Goal
  2.1.292; a fresh no-cache `uvx` invocation reported `goal, version 2.1.292`.
- Published SHA-256: wheel
  `001a381085482fe80dacae1ab5fdd519e173d3cc866e1846988bfc7117b71137`,
  sdist `47d8c210e61833b693d1d95fd9600890bfe64b0a1035caa466771388007ce7a5`.

## Session authorization

The user authorized autonomous publication. No repeated confirmation is
required for this exact release; protected exact-head approval and registry
credential boundaries remain enforced.

## Boundary

This slice owns only `VERSION`, `pyproject.toml`, `uv.lock`,
`goal/__init__.py`, README release badges and ticket metadata. Source,
dependency constraints, top-level changelog, governance and CI are excluded.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
