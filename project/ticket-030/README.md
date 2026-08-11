# Ticket 030: Respect package identity and Python support during Goal bootstrap

- **ID**: ticket-030
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-11

## Goal and scope

Make Goal bind Git tag evidence to the current package identity and inject its
optional developer tools with Python-version markers compatible with the
target project's declared support range. The regression fixture is the `glon`
repository, where a legacy `gc` tag `v1.0.1` must not override the `glon`
release line and Python 3.8 support must remain installable.

## Acceptance criteria

- [x] AC-01: The user explicitly requested the Goal repair and authorized
  merging the prerequisite PR #60.
- [x] AC-02: Tags for a different historical package identity are excluded
  from release baseline evidence without weakening matching-tag protection.
- [x] AC-03: Injected `goal`, `costs` and `pfix` dev requirements carry markers
  matching their supported Python floors, so a Python 3.8 project resolves.
- [x] AC-04: Focused and full Goal tests, changed-file Ruff, governance,
  package build and Docker pass; the pre-existing repository-wide lint debt is
  recorded without expanding this repair.
- [x] AC-05: A read-only regression run against `glon` selects the `glon`
  release line and no longer reports the legacy `gc` baseline or UV conflict.

## Validation evidence

- 21 focused tests and the full suite of 530 tests with 2 skips pass; Ruff
  reports no issues in the four implementation/test files.
- The repository-wide Ruff baseline still contains 100 unrelated findings,
  so this ticket does not claim a clean global lint baseline.
- Governance passes with zero errors and warnings. The wheel and source
  distribution build successfully with `uv build`.
- The production Docker image builds and reports Goal 2.1.294 with networking
  disabled.
- A read-only `glon` check selects `0.1.26` from `git-tag:v0.1.26` and proposes
  `normal-bump -> 0.1.27`, ignoring the historical `gc` tag `v1.0.1`.
- A Python 3.8 `glon` fixture resolves all 235 packages with `uv lock
  --dry-run`, and a snapshot `goal -a --dry-run` completes without the
  original version-regression or unsatisfiable-dependency error.

## Session authorization

The user's request to fix Goal supplies `SESSION_EXECUTION_AUTHORIZATION` for
this bounded local implementation. Publishing, pushing and merging ticket 030
remain outside the authorization.

## Boundary

This ticket owns only version-evidence selection, Python bootstrap requirement
generation and focused regression tests. Release metadata, dependency
manifests, delivery code, registry publication and global installation are
excluded.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
