# Ticket 100: Stop bootstrapping pfix auto-repair into projects

- **ID**: ticket-100
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-13

## Goal and scope

On 2026-09-13 the user stated that pfix, intended as development-time
auto-repair, overwrites changes and must be removed from projects or
deactivated (SESSION_EXECUTION_AUTHORIZATION). `goal bootstrap` currently
installs pfix into every Python project, appends `[tool.pfix]` with
`auto_apply = true`, writes a `.env` template with `PFIX_AUTO_APPLY=true` and
injects `pfix` into dev dependencies, so a removal in a project is undone by the
next Goal run. This ticket removes that injection from Goal only.

Non-goals: Goal does not delete existing pfix declarations from projects (that
is an explicit per-project change), the legacy `[tool.pfix] auto_apply = false`
opt-out of Goal's own configuration auto-fix keeps working, and Goal's own
`pyproject.toml`/`uv.lock` are handled by a separate integration ticket.

## Acceptance criteria

- [ ] AC-01: `bootstrap_project` no longer installs pfix, writes `[tool.pfix]`
  or creates a pfix `.env`/`.env.example` template.
- [ ] AC-02: Dev-dependency injection adds only `goal` and `costs`; an existing
  pfix requirement is left for an explicit project change.
- [ ] AC-03: A regression test proves a Python bootstrap runs no pfix command
  and writes no pfix configuration; the bootstrap test modules pass.

Fleet evidence: `subactor/docs/architecture/analysis/semcod-library-quality.md`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
