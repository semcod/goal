# Ticket 043: Publish Goal 2.1.296 delivery coherence fixes

- **ID**: ticket-043
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Pre-PR evidence

- The release plan is a distinct commit on clean accepted base `3fb66ab`.
- Goal 2.1.295 is the public baseline; PyPI has no 2.1.296 artifact and GitHub
  has no `v2.1.296` tag or Release before the candidate workflow.
- The high-level source workflow selected `explicit-target -> 2.1.296`, passed
  573 tests with 2 existing skips, changed only the five release carriers and
  ticket evidence, skipped registry/tag effects and opened PR #68.
- All carriers agree at 2.1.296; deterministic governance passes with zero
  findings. Build produced exactly `goal-2.1.296-py3-none-any.whl`
  (`5c56b2def98d44271e2f8de8e79247ea39c421455adfb6bf711ef11f2e7c593e`)
  and `goal-2.1.296.tar.gz`
  (`0925cc776b2eeb406ed6997599055ed59b506f54cda281dd3f328a45a1f9c3a9`).
- Docker built image
  `sha256:d53507165c77e8ea170d5570b4454b6229a2b500c1574a92dcaa44a995e8c86a`;
  its temporary local image was removed immediately after recording it.

## Publication evidence

- Protected CI passed on exact PR head `b99fdd1`; trusted Validator App review
  `4915080136` approved that same SHA before PR #68 merged as
  `main@c5f3684ed83da71ab312808bfbbf79af80551b50`.
- The clean merge passed 573 tests with 2 existing skips, scoped Ruff,
  governance with zero findings, a two-artifact package build and Docker image
  `sha256:bd249e98b34893e7c603efabb8701495ec785bb208d7e9a5d61d9c46a99ac769`.
- Governed `publish-only` ran the full test suite again and uploaded exactly
  `goal-2.1.296-py3-none-any.whl`
  (`c2fd441d0b8afa8f3335248f14021cf48d3ca654772c5ca5311f7fe7826356d4`)
  and `goal-2.1.296.tar.gz`
  (`0a29b0ee906dd36a1d86f5a53388b22c51e50b16b29640865723288456478cfb`).
- PyPI metadata and independently downloaded final GitHub Release assets match
  both hashes. Annotated `v2.1.296` dereferences to `c5f3684`; the final Release
  is <https://github.com/semcod/goal/releases/tag/v2.1.296>.
- A no-cache Python 3.12 install from the public PyPI index reports 2.1.296 via
  both import and CLI. `goal push --help` leaves a fresh empty directory empty.

## Goal and scope

Publish the exact merged ticket-041 source-hub layout diagnostics and
ticket-042 read-only help/commit-only orchestration repairs as Goal 2.1.296.
Synchronize only the five established release carriers through a protected PR,
then publish the package, annotated tag and final GitHub Release exclusively
from the clean validated merge SHA. Verify a fresh public install before using
the new Goal version to resume `wellmanifest/new-project` ticket-065.

## Acceptance criteria

- [x] AC-01: The governed high-level PR workflow synchronizes exactly VERSION,
  `pyproject.toml`, `goal/__init__.py`, README version badges and `uv.lock` to
  2.1.296, plus this ticket's evidence.
- [x] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
  protected CI and Validator App approve the exact final PR head.
- [x] AC-03: The clean merged `main` is retested before registry/tag/Release
  effects and produces exactly one wheel and one sdist for 2.1.296.
- [x] AC-04: Annotated `v2.1.296`, final GitHub Release and PyPI artifacts all
  bind to the exact clean merge and immutable hashes are recorded.
- [x] AC-05: A fresh public-index install reports 2.1.296; `push --help` is
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
