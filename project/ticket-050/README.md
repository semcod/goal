# Ticket 050: Publish Goal 2.1.298 with artifactless Release support

- **ID**: ticket-050
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.298 from clean `main` so the already merged ticket-048 repair
for generic GitHub Releases without package assets is present in the public
CLI. Synchronize only the five established release carriers through a protected
PR, then publish PyPI artifacts, an annotated tag and a final GitHub Release
from the exact retested merge SHA. Use that public CLI to repair the existing
artifactless `wellmanifest/new-project v0.16.1` tag into a final Release.

## Acceptance criteria

- [x] AC-01: The governed PR synchronizes exactly VERSION, `pyproject.toml`,
      `goal/__init__.py`, README version badges and `uv.lock` to 2.1.298, plus
      this ticket's governance evidence.
- [x] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
      protected CI and Validator App approve the exact final PR head.
- [x] AC-03: The clean merged `main` is retested before registry/tag/Release
      effects and produces exactly one wheel and one sdist for 2.1.298.
- [x] AC-04: Annotated `v2.1.298`, final GitHub Release and PyPI artifacts all
      bind to the exact clean merge and immutable hashes are recorded.
- [x] AC-05: A fresh public-index install reports 2.1.298 and uses the merged
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

- Accepted base was refreshed to clean `main@355d49f` after the independently
  validated ticket-049 implementation and closure merged; ticket-048 is
  complete there and its
  generic assetless Release code is absent from public wheel 2.1.297.
- PyPI returns 404 for Goal 2.1.298 and neither annotated tag `v2.1.298` nor a
  GitHub Release exists before entering publication.
- `new-project v0.16.1` is an annotated tag peeled to exact clean merge
  `4e6ba5e`, but public Goal 2.1.297 skipped its required Release because that
  wheel predates ticket-048.
- The refreshed candidate passes 600 tests with 2 existing skips, scoped Ruff,
  governance and exact carrier checks. Wheel SHA-256 is
  `b8890061bb87c2abdc59d2558416c5b18243704e3e07bea6229050912b8e74e2`;
  sdist SHA-256 is
  `86e558e0f1e86b04f20882c924a93523b19736f85655529fedbe0d6a10cc4b34`.
  The wheel contains the artifactless Release and exact-tag recovery paths.
- The pinned-base Docker candidate built successfully as
  `sha256:0d1b1ea750f9b006d868d88f46e24f34f784a202e30a8897fdfc280e520344dc`;
  all candidate distributions, build outputs, virtual environments and the
  validation image were removed after evidence capture.

## Completion evidence

- PR #77 head `c5a24e236535f72a25bc016baf45cbb99d26d39d` passed Python
  3.12 and 3.13 CI. Validator App review `4917221672` approved that exact head
  for ticket-050 before merge `4388d1e4c7b7547ee93b42fddbb9947f358e444e`.
- The clean merge passed 600 tests with 2 existing skips, scoped Ruff,
  governance and carrier checks. Its pinned-base Docker image built as
  `sha256:1f61048c4c2c541b0ed8e630f6e7ac8e0dee16eccd21325cdd12829adfb28e0e`.
- Public PyPI 2.1.298 contains one wheel, SHA-256
  `1b098106e261cb5cd9ff9623dcdff3b6509810af349eec7f7ec55868ddee393d`,
  and one sdist, SHA-256
  `0ccc78efd216da200abdf75d8d372aacfe4e625fa2c40eb687f5dfc625bd9099`.
  The final GitHub Release exposes byte-identical copies of both artifacts.
- Annotated tag object `507f21edc76f0d76a040ded9242cd44b23d59be8`
  peels to exact merge `4388d1e4c7b7547ee93b42fddbb9947f358e444e`; the final,
  non-draft GitHub Release is
  `https://github.com/semcod/goal/releases/tag/v2.1.298`.
- A no-cache public-index install loaded Goal 2.1.298 from `site-packages` and
  exposed the exact-tag recovery implementation. In a fresh clean
  `wellmanifest/new-project` clone it reused annotated tag object
  `d25151e27a6eeff899caff191993df0559ec333d`, kept both tag peel and remote
  `main` at `4e6ba5ec15873346446d67d8787f17f68f57f81e`, created no commit, and
  completed the final assetless Release at
  `https://github.com/wellmanifest/new-project/releases/tag/v0.16.1`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
