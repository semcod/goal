# Ticket 057: Publish Goal 2.1.299 with mutation-free PR resume

- **ID**: ticket-057
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Publish Goal 2.1.299 from the exact merged ticket-056 repair. Synchronize only
the five established release carriers through a protected PR, then publish the
package, annotated tag and final GitHub Release exclusively from the clean,
retested merge SHA. Prove the public package by resuming the already committed
`wellmanifest/new-project` ticket-072 candidate without changing its checkout.

## Acceptance criteria

- [ ] AC-01: The governed PR synchronizes exactly VERSION, `pyproject.toml`,
      `goal/__init__.py`, README version badges and `uv.lock` to 2.1.299, plus
      this ticket's governance evidence.
- [ ] AC-02: Full tests, scoped Ruff, governance, wheel/sdist and Docker pass;
      protected CI and Validator Agent approve the exact final PR head.
- [ ] AC-03: The clean merged `main` is retested before registry, tag or
      Release effects and produces exactly one wheel and one sdist for 2.1.299.
- [ ] AC-04: Annotated `v2.1.299`, final GitHub Release and PyPI artifacts all
      bind to the exact clean merge and immutable hashes are recorded.
- [ ] AC-05: A fresh public-index install reports 2.1.299 and resumes the real
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

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
