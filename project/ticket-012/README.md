# Ticket 012: Refresh runtime and release dependencies

- **ID**: ticket-012
- **Owner**: session user (identity unresolved)
- **Status**: PLAN
- **Workflow state**: WAIT_FOR_DEPENDENCY
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / integration`

## Goal and scope

Align the repository-owned integration container with Goal's declared Python
support, refresh the resolved Python dependency set, verify the package across
the full test and container matrix, and publish the resulting release through
the governed `goal -a` path.  Audit local consumers for explicit older Goal
dependency constraints and update only unambiguous declarations in clean,
governed repositories.

## Acceptance criteria

- [x] AC-01: The user explicitly requested testing, publication and dependency
  refresh after the Python 3.11 container mismatch was reported.
- [ ] AC-02: The integration image uses a Python version supported by
  `requires-python` and its eight-project matrix passes.
- [ ] AC-03: `uv.lock` is regenerated against current compatible releases and
  remains consistent with `pyproject.toml`.
- [ ] AC-04: The full Python suite, build checks and governance gate pass.
- [ ] AC-05: Publication is performed through governed `goal -a`, and the
  released version is independently installable.
- [ ] AC-06: Explicit stale Goal constraints found in in-scope local consumers
  are reported and updated only after their own repository policy is honored.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Session authorization

The user responded `tak, przetestuj i opublikuj i zaktualizuj zaleznosci i goal
w zaleznosciach` to the reported Python 3.11 integration-image backlog.  This
is recorded as approval for this narrow integration/release scope and permits
the transition from `PLAN / WAIT_FOR_APPROVAL` to `IN_PROGRESS / EDIT`.

## Boundary

This ticket may change `integration/Dockerfile`, `pyproject.toml` and `uv.lock`.
It does not authorize speculative source refactors, automatic major-version
dependency changes, or edits to dirty downstream repositories.  Each downstream
repository remains subject to its own governance and publication boundary.

## Dependency discovered by the gate

The adopted governance revision 0.11.0 does not assign `uv.lock` or
`integration/**` to any workstream.  Ticket 012 therefore releases its active
reservation until a separate governance ticket upgrades the immutable standard
and installs an explicit target-local ownership extension.  Implementation
must not begin before that dependency is merged and this intent is re-approved
with the final paths.
