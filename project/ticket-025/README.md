# Ticket 025: Publish Goal 2.1.293 delivery-integrity fixes

- **ID**: ticket-025
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: IMPLEMENTATION
- **Created**: 2026-08-10

## Goal and scope

Publish the merged ticket-024 delivery-integrity fixes as Goal 2.1.293.
Synchronize the five atomic release carriers, pass the full test and protected
PR chain, publish wheel and sdist only from merged `main`, then verify a fresh
public-index installation.

## Acceptance criteria

- [x] AC-01: The user explicitly requested autonomous testing, publication and
  dependent-project updates.
- [ ] AC-02: Goal selects `normal-bump -> 2.1.293` once and all release carriers
  are synchronized; a subsequent check selects `already-bumped`.
- [ ] AC-03: Full tests, build, governance, target CI and exact-head validator
  pass before merge.
- [ ] AC-04: Clean merged `main` publishes exactly one wheel and one sdist for
  2.1.293 through `goal -a --delivery-mode publish-only`.
- [ ] AC-05: A fresh public-index environment reports Goal 2.1.293.

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
