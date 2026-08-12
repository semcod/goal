# Ticket 039: Keep dependency marker migration inside dev sections

- **ID**: ticket-039
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Fix the marker migration used by Goal bootstrap. Legacy unmarked Goal tooling
requirements must gain interpreter markers only inside supported development
dependency lists. Runtime dependencies with the same package name must remain
unchanged. This prevents governed delivery bootstrap from silently rewriting
the package runtime contract before staging.

## Acceptance criteria

- [x] AC-01: A legacy unmarked tool in the optional `dev` list gains its
  required Python marker and the transform remains idempotent.
- [x] AC-02: A matching runtime dependency is byte-for-byte unchanged and is
  not treated as a development tool migration target.
- [x] AC-03: Missing Goal tools are still added to optional and Hatch
  development lists with their compatibility markers.
- [x] AC-04: Focused/full tests, scoped Ruff, governance, package and Docker
  builds pass.

## Boundary

- This ticket changes only dependency-list transformation logic and tests.
- Synchronizing Goal's own legacy `pfix` dev marker and release metadata belongs
  to the dependent integration ticket.
- No runtime dependency, version or publication changes are allowed here.

## Validation evidence

- Three focused transformation tests pass, including runtime preservation and
  idempotence.
- The full suite passes with 560 tests and 2 existing skips.
- Scoped Ruff and deterministic governance pass.
- A dry transformation of Goal's real `pyproject.toml` preserves runtime
  `costs` and proposes only the legacy dev `pfix` marker.
- Python wheel/sdist and Docker image builds pass; temporary output and
  generated `goal.egg-info` were removed.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
