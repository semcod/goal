# Ticket 072: Verify and refresh catalogued internal dependencies

- **ID**: ticket-072
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-05

## Goal and scope

Implement a shared Python/uv dependency command driven by an explicit internal package catalog. Select stable published versions, report old locks and enforce exact upgrade targets. Preserve source policies and surface Python compatibility failures.

## Authorization

SESSION_EXECUTION_AUTHORIZATION: user requested continuation of the reviewed ecosystem update mechanism and pilot implementation. Source changes, tests and reviewable delivery are authorized within this ticket's allowed paths.

## Acceptance criteria

- [x] AC-01: Session authorization and bounded intent recorded.
- [x] AC-02: Read-only audit is bounded, skips alternate sources and reports stable targets.
- [x] AC-03: Explicit lockfile update verifies target versions and handles failures without silent fallback.
- [x] AC-04: Focused/full tests, governance and Docker pass.

## Boundary

This slice supports PyPI packages and uv projects. It does not publish consumers or silently change their Python support, source configuration or installation environments.

## Local validation

Python 3.12.13: 666 passed, 2 skipped. Python 3.13 after standard adoption rebase: 679 passed, 2 skipped. Scoped Ruff and adopted governance pass. Final Docker build and dependency-command smoke pass after rebase. Three real consumer pilots report current catalog versions; an isolated transaction upgraded five exact registry targets. Python 3.12.0 has a pre-existing compiler limit in two existing test modules; use the current Python 3.12 patch release.
