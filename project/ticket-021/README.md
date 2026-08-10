# Ticket 021: Detect writable Python version declarations

- **ID**: ticket-021
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10

## Goal and scope

Make Python version discovery select only writable, top-level
`__version__ = "..."` declarations. Importing or re-exporting `__version__`
must not make a file a version carrier, while conventional `version.py` and
`_version.py` modules must be discoverable. This keeps `goal check-versions`
from rewriting a valid `goal.yaml` to an unreadable selector.

## Acceptance criteria

- [x] AC-01: The user requested autonomous continuation and correct Goal
  decisions about which files carry versions.
- [x] AC-02: Import-only `__init__.py` files are ignored by configuration
  detection.
- [x] AC-03: A conventional Python version module with a literal assignment is
  discovered and remains readable/writable by version-state logic.
- [x] AC-04: Focused and full tests plus governance pass.

## Validation evidence

- Focused version-discovery suite: 26 passed.
- Full Goal suite: 512 passed, 2 skipped.
- The detector run against `wellmanifest/wellm` selects
  `src/wellmanifest/version.py:__version__` and excludes the compatibility
  re-export in `src/well/__init__.py`.
- PR #39 passed Python 3.12/3.13 CI and exact-head validator approval for
  `05ef1167cf43e43fbe1b512ea9808a7ed458adfe`.
- Protected merge completed as
  `c48ff33d12dd9797868959caa3fda4adeec766ff`.

## Session authorization

The user explicitly authorized autonomous implementation, testing and
publication. No repeated confirmation is required inside this bounded ticket;
exact-head validation and protected merge remain mandatory.

## Risk boundary

Only version-source discovery and regression tests change. Version precedence,
bump arithmetic, registry comparison, publication credentials and delivery
policy remain unchanged.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
