# Ticket 030: Respect package identity and Python support during Goal bootstrap

- **ID**: ticket-030
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
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
- [ ] AC-02: Tags for a different historical package identity are excluded
  from release baseline evidence without weakening matching-tag protection.
- [ ] AC-03: Injected `goal`, `costs` and `pfix` dev requirements carry markers
  matching their supported Python floors, so a Python 3.8 project resolves.
- [ ] AC-04: Focused and full Goal tests, Ruff, governance and Docker pass.
- [ ] AC-05: A read-only regression run against `glon` selects the `glon`
  release line and no longer reports the legacy `gc` baseline or UV conflict.

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
