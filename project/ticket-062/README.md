# Ticket 062: Read setuptools setup() version declarations

- **ID**: ticket-062
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-13

## Goal and scope

Make configured and auto-detected `setup.py:version` sources accept the
standard literal `version="..."` keyword passed to `setuptools.setup(...)`.
Keep discovery, reading and synchronization aligned without executing
`setup.py` or rewriting unrelated `version=` keywords.

## Acceptance criteria

- [x] AC-01: The user's instruction to implement the repair records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded defect.
- [x] AC-02: Version-state resolution reads literal versions from imported
  `setuptools.setup(...)` calls, including supported aliases.
- [x] AC-03: Synchronization updates only the selected setup-call version and
  leaves unrelated `version=` keywords unchanged.
- [x] AC-04: Focused and full Python tests, scoped Ruff, governance and the
  repository Docker build pass.

## Boundary

- Parse Python source statically; never import or execute a target `setup.py`.
- Preserve existing module-level `version = "..."` support.
- Do not add runtime dependencies or change public CLI behavior.
- Do not publish, push or modify ticket-061 release evidence.

## Validation evidence

- 55 focused tests and 619 full tests pass with 2 existing skips.
- Scoped Ruff, governance (0 errors / 0 warnings) and whitespace validation
  pass.
- Docker build passed with host networking to avoid allocating a bridge
  subnet; the resulting CLI passed with `--network none`, then the exact
  disposable image was removed. No Docker network was removed or modified.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
