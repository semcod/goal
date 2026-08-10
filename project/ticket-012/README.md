# Ticket 012: Refresh runtime and release dependencies

- **ID**: ticket-012
- **Owner**: session user (identity unresolved)
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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
- [x] AC-02: The integration image uses a Python version supported by
  `requires-python` and its eight-project matrix passes.
- [x] AC-03: `uv.lock` is regenerated against current compatible releases and
  remains consistent with `pyproject.toml`.
- [x] AC-04: The full Python suite, build checks and governance gate pass.
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

The first slice merged the runtime and lock refresh. The second slice merged
the atomic five-file version state. This final publication slice is freshly
based on merge `68e69b8d26d3e5ba851bad98351c5e801e17e040` and may publish only that
already-reviewed Goal 2.1.290 state. Repository changes are limited to Goal's
generated `README.md`, `CHANGELOG.md` and ticket evidence; no new version,
source, dependency-range or public-interface change is authorized. Each
downstream repository remains subject to its own governance boundary.

## Validation evidence: runtime and lock slice

- The digest-pinned integration image runs Python 3.12.13.
- The isolated container matrix passed for Python, Node.js, Rust, Go, Ruby,
  PHP, .NET and Java (`8 passed, 0 failed`).
- `uv lock --upgrade` refreshed the compatible 142-package resolution and
  `uv lock --check` passed without changing declared dependency ranges.
- The host suite passed (`508 passed, 2 skipped`) and both wheel and source
  distributions for Goal 2.1.289 were built successfully.

## Dependency resolution

Tickets 013, 016, and 017 are published. Goal now runs immutable governance
v0.14.1, excludes governance helpers from package-source classification, and
assigns integration ownership to the runtime, lockfile, and atomic release
metadata paths. The original session authorization therefore permits this
ticket to resume without another confirmation.

PR #30 merged the runtime and lock slice at exact validated head
`2e0e6202dc5c54582b3d1438c92fb8051ab50e73`. Its merge commit is the accepted
base for the release-version slice.

PR #31 merged the synchronized Goal 2.1.290 version state at exact validated
head `e8767fda6890f6b3c7d79984599dcd2f1f823e51`; merge
`68e69b8d26d3e5ba851bad98351c5e801e17e040` is the accepted publication base.

## Validation evidence: release-version slice

- `goal -a` selected `normal-bump -> 2.1.290` from the shared tag/registry
  baseline 2.1.289 and synchronized all five approved version carriers.
- A subsequent `goal check-versions` selected `already-bumped -> 2.1.290`,
  proving that the complete local bump is not repeated.
- The 508-test suite passed (2 skipped), `uv lock --check` passed for the
  142-package graph, and Goal 2.1.290 wheel and sdist builds succeeded.
