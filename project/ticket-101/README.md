# Ticket 101: Remove pfix from Goal packaging metadata

- **ID**: ticket-101
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-13

## Goal and scope

On 2026-09-13 the user stated that pfix overwrites development changes and must
be removed from projects or deactivated (SESSION_EXECUTION_AUTHORIZATION).
Goal itself still declares pfix: a `[tool.pfix]` table with `auto_apply = true`
and `auto_install_deps = true`, a `pfix` dev requirement, a pfix dependency in
the tox test environment and a `lint` tox environment whose only command is
`pfix check`. This integration ticket removes those declarations and
regenerates `uv.lock`. The bootstrap code that injected pfix into other
projects is changed separately by ticket-100.

Non-goals: no source or test change, no release, and no rewrite of the
historical tox example in `docs/pyqual.md`.

## Acceptance criteria

- [ ] AC-01: `pyproject.toml` has no `[tool.pfix]` table, no pfix requirement
  and no tox environment that runs pfix; every other parsed value is unchanged.
- [ ] AC-02: `uv.lock` is regenerated and records no pfix requirement for Goal.

Fleet evidence: `subactor/docs/architecture/analysis/semcod-library-quality.md`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
