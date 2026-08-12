# Ticket 050: Publish Goal 2.1.298 with artifactless Release support

- **ID**: ticket-050
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.298 from clean `main` so the already merged ticket-048 repair
for generic GitHub Releases without package assets is present in the public
CLI. Synchronize only the five established release carriers through a protected
PR, then publish PyPI artifacts, an annotated tag and a final GitHub Release
from the exact retested merge SHA. Use that public CLI to repair the existing
artifactless `wellmanifest/new-project v0.16.1` tag into a final Release.

## Acceptance criteria

- [ ] AC-01: The governed PR synchronizes exactly VERSION, `pyproject.toml`,
      `goal/__init__.py`, README version badges and `uv.lock` to 2.1.298, plus
      this ticket's governance evidence.
- [ ] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
      protected CI and Validator App approve the exact final PR head.
- [ ] AC-03: The clean merged `main` is retested before registry/tag/Release
      effects and produces exactly one wheel and one sdist for 2.1.298.
- [ ] AC-04: Annotated `v2.1.298`, final GitHub Release and PyPI artifacts all
      bind to the exact clean merge and immutable hashes are recorded.
- [ ] AC-05: A fresh public-index install reports 2.1.298 and uses the merged
      artifactless path to create the missing final `new-project v0.16.1`
      GitHub Release without moving its existing annotated tag.

## Boundary

- No executable source belongs to this release ticket; implementation was
  integrated through ticket-048 after Goal 2.1.297 was already published.
- Ticket-049 remains an independent application PR and is not included in this
  release candidate unless it is separately approved and merged before a
  deliberate base refresh.
- Top-level CHANGELOG is not rewritten; the bounded release narrative lives in
  this ticket.
- No registry, tag or Release action occurs before protected merge and clean
  merge validation. Existing immutable releases are never moved.
- The request to repair and continue is bounded
  `SESSION_EXECUTION_AUTHORIZATION`; trusted exact-head approval remains
  external.

## Pre-publication evidence

- Accepted base is clean `main@0c3cd7b`; ticket-048 is complete there and its
  generic assetless Release code is absent from public wheel 2.1.297.
- PyPI returns 404 for Goal 2.1.298 and neither annotated tag `v2.1.298` nor a
  GitHub Release exists before entering publication.
- `new-project v0.16.1` is an annotated tag peeled to exact clean merge
  `4e6ba5e`, but public Goal 2.1.297 skipped its required Release because that
  wheel predates ticket-048.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
