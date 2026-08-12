# Ticket 043: Publish Goal 2.1.296 delivery coherence fixes

- **ID**: ticket-043
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Publish the exact merged ticket-041 source-hub layout diagnostics and
ticket-042 read-only help/commit-only orchestration repairs as Goal 2.1.296.
Synchronize only the five established release carriers through a protected PR,
then publish the package, annotated tag and final GitHub Release exclusively
from the clean validated merge SHA. Verify a fresh public install before using
the new Goal version to resume `wellmanifest/new-project` ticket-065.

## Acceptance criteria

- [ ] AC-01: The governed high-level PR workflow synchronizes exactly VERSION,
  `pyproject.toml`, `goal/__init__.py`, README version badges and `uv.lock` to
  2.1.296, plus this ticket's evidence.
- [ ] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
  protected CI and Validator App approve the exact final PR head.
- [ ] AC-03: The clean merged `main` is retested before registry/tag/Release
  effects and produces exactly one wheel and one sdist for 2.1.296.
- [ ] AC-04: Annotated `v2.1.296`, final GitHub Release and PyPI artifacts all
  bind to the exact clean merge and immutable hashes are recorded.
- [ ] AC-05: A fresh public-index install reports 2.1.296; `push --help` is
  read-only and the public CLI can drive the next `new-project` delivery.

## Boundary

- No executable source belongs to this release ticket; implementation is
  already integrated by exact-head-approved PRs #66 and #67.
- Top-level CHANGELOG is intentionally not rewritten; the bounded release
  narrative lives in this ticket.
- No registry, tag or Release action occurs before protected merge and clean
  merge validation. Existing immutable releases are never moved.
- The user's repeated instruction to repair and continue is bounded
  `SESSION_EXECUTION_AUTHORIZATION`; independent approval remains external.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
