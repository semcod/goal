# Ticket 061: Publish Goal 2.1.300 retry-safe release

- **ID**: ticket-061
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.300 from the exact merged retry-safety chain in tickets 058,
059 and 060. Synchronize only the five established release carriers through a
protected PR, then publish the wheel, sdist, annotated tag and final GitHub
Release exclusively from the clean, retested merge SHA. Prove the public
package on a disposable exact Glon checkout while preserving the user's dirty
live checkout.

## Acceptance criteria

- [x] AC-01: The user's instruction to repair and continue records
  `SESSION_EXECUTION_AUTHORIZATION` for the bounded release.
- [ ] AC-02: The governed PR synchronizes exactly VERSION, `pyproject.toml`,
  `goal/__init__.py`, README version badges and `uv.lock` to 2.1.300, plus
  this ticket's governance evidence.
- [ ] AC-03: Full tests, scoped Ruff, governance and wheel/sdist pass;
  protected CI and Validator Agent approve the exact final PR head.
- [ ] AC-04: Clean merged `main` is retested before registry/tag/Release
  effects and produces exactly one wheel and one sdist for 2.1.300.
- [ ] AC-05: PyPI, annotated `v2.1.300` and the final GitHub Release bind to
  the exact merge and immutable hashes are recorded.
- [ ] AC-06: A fresh public-index install reports 2.1.300 and safely diagnoses
  or executes the bounded Glon path without changing the live dirty checkout.

## Boundary

- No executable source belongs to this release ticket; implementation is
  already integrated and independently approved in tickets 058-060.
- Top-level CHANGELOG is not rewritten; the release narrative lives here.
- No registry, tag or Release action occurs before protected merge and clean
  merge validation. Existing immutable releases are never moved.
- Do not modify the live Glon checkout or its user-owned dirty files.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Pre-publication evidence

- Accepted base is clean `main@ad06f17`; tickets 058-060 are DONE, their
  exact-head reviews and post-merge CI passed, and Goal has one main branch,
  one worktree, zero open PRs and zero open issues.
- PyPI returned HTTP 404 for 2.1.300; neither local/remote `v2.1.300` nor a
  GitHub Release exists before publication.
