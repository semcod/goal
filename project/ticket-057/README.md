# Ticket 057: Publish Goal 2.1.299 with mutation-free PR resume

- **ID**: ticket-057
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.299 from the exact merged ticket-056 repair. Synchronize only
the five established release carriers through a protected PR, then publish the
package, annotated tag and final GitHub Release exclusively from the clean,
retested merge SHA. Prove the public package by resuming the already committed
`wellmanifest/new-project` ticket-072 candidate without changing its checkout.

## Acceptance criteria

- [x] AC-01: The governed PR synchronizes exactly VERSION, `pyproject.toml`,
      `goal/__init__.py`, README version badges and `uv.lock` to 2.1.299, plus
      this ticket's governance evidence.
- [x] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
      protected CI and Validator Agent approve the exact final PR head.
- [x] AC-03: The clean merged `main` is retested before registry, tag or
      Release effects and produces exactly one wheel and one sdist for 2.1.299.
- [x] AC-04: Annotated `v2.1.299`, final GitHub Release and PyPI artifacts all
      bind to the exact clean merge and immutable hashes are recorded.
- [x] AC-05: A fresh public-index install reports 2.1.299 and resumes the real
      new-project ticket-072 pull-request candidate while its tree stays clean.

## Boundary

- No executable source belongs to this release ticket; implementation is
  already integrated through exact-head-approved ticket-056 PRs #92 and #93.
- Top-level CHANGELOG is intentionally not rewritten; the bounded release
  narrative lives in this ticket.
- No registry, tag or Release action occurs before protected merge and clean
  merge validation. Existing immutable releases are never moved.
- The user's instruction to repair and continue is bounded
  `SESSION_EXECUTION_AUTHORIZATION`; exact-head Validator approval remains
  independent and mandatory.

## Pre-publication evidence

- Accepted base is clean `main@5ec8fa0`; ticket-056 is DONE, its post-merge
  Python 3.12/3.13 CI run 31620406273 passed, and the repository has no open
  PR, issue, worktree or non-main branch.
- PyPI, the Git remote and GitHub Releases are checked for absence of 2.1.299
  before publication begins.
- Public Goal 2.1.298 reproduced the pre-ticket-056 behavior while opening PR
  #94: it wrote two events to the checkout. The exact generated file and its
  temporary local ignore were removed; neither was committed or pushed.
- The editable runtime now resolves to clean merged `main@5ec8fa0`; resuming
  the exact candidate must write events below the Git common directory and
  leave no checkout file, including when no ignore masks that path.

## Delivery and publication evidence

- Release PR #94 passed Python 3.12/3.13 and remote lifecycle checks on exact
  HEAD `61695d9ce9ea65081ca7c3753d29687033ca6cae`; Validator review
  `4919198753` approved that SHA without findings.
- PR #94 merged as `4db0b042688385684dcd8d536c0b4128d1905e0a`; the merge's second
  parent and tree equal the approved candidate. Post-merge run `31621738849`
  passed on that exact merge.
- Clean merged `main` passed 607 tests with 2 existing skips before any
  publication effect. The candidate also passed scoped Ruff, governance,
  wheel/sdist build and Docker CLI smoke; temporary build output and image
  `sha256:ffd9adc8765af4bdd590006d949b6ec392005cf4f9a048809ad7accec5912b2b`
  were removed.
- PyPI contains exactly `goal-2.1.299-py3-none-any.whl` (338730 bytes,
  SHA-256 `836b75f04a656772736fd18072c2a7f495c18a124e47c07b47bc948be44658d4`)
  and `goal-2.1.299.tar.gz` (384097 bytes, SHA-256
  `de60a91480afc4cfd20f1f7ff1719a61d2f39b7d35eaafaf47766832f00d284f`).
- Annotated tag object `525741c32e0f707aafd3292d015f2ae0be8f8e34` peels to exact merge
  `4db0b042...`. The final, non-draft GitHub Release at
  `https://github.com/semcod/goal/releases/tag/v2.1.299` carries byte-identical
  copies of both PyPI artifacts.
- A fresh public-index 2.1.299 install imported only from isolated
  site-packages and resumed the real historical new-project ticket-072 commit
  `d212d9d9...` against its exact authoritative base `3a997d6b...`. The
  bounded replay used a local bare remote and local `gh` contract double:
  it pushed exact `goal/ticket-072`, recorded both events below
  `.git/goal-delivery`, and left the checkout byte-clean. The already completed
  GitHub ticket was not reopened; the real repository retained zero open PRs.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
