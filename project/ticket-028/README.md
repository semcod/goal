# Ticket 028: Publish Goal 2.1.294 with exact-head PR delivery repair

- **ID**: ticket-028
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-10

## Goal and scope

Publish the merged ticket-027 exact-head pull-request lifecycle repair as Goal
2.1.294. Synchronize the five atomic release carriers, pass the complete local
and protected PR validation chain, publish wheel and sdist only from clean,
merged `main`, and verify a fresh public-index installation.

## Acceptance criteria

- [x] AC-01: The user explicitly requested autonomous testing, publication and
  dependent-project updates.
- [x] AC-02: Goal selects `explicit-target -> 2.1.294` once, synchronizes all five
  release carriers, and subsequently selects `already-bumped`.
- [x] AC-03: Full tests, build, governance, Docker, target CI and exact-head
  validator pass before merge.
- [x] AC-04: Clean merged `main` publishes exactly one wheel and one sdist for
  2.1.294 through `goal -a --delivery-mode publish-only --force-publish`.
- [x] AC-05: A fresh no-cache public-index environment reports Goal 2.1.294.

## Session authorization

The user authorized autonomous testing, publication and dependent-project
updates. No repeated confirmation is required for this exact release;
protected exact-head approval and registry credential boundaries remain
enforced.

## Boundary

This slice owns only `VERSION`, `pyproject.toml`, `uv.lock`,
`goal/__init__.py`, README release badges and ticket metadata. Source,
dependency constraints, top-level changelog, governance and CI are excluded.

## Release evidence

- The abandoned PR #58 was closed without merge; it is not counted as release
  delivery evidence.
- The same release chain was completed by PR #59 at exact head
  `1c011015ae66357a1b2c4217ebcb207238634d48`: Python 3.12/3.13 CI passed,
  Validator Agent approved that exact head, and GitHub merged it as
  `051a59aaf4ffe007491fb50c826774871ea73a6b`.
- PyPI published exactly `goal-2.1.294-py3-none-any.whl` and
  `goal-2.1.294.tar.gz`. Their SHA-256 values are respectively
  `834c8ae3630781763d5e0eb8a88afdd70dda75a303c7cddeb107e27e765f7e6f` and
  `29a8d554c7867c7bf9704806e196d577e5a10d583f61051ab3770d488b1028ee`.
- A fresh isolated installation of the public wheel imported
  `goal.__version__ == 2.1.294`; all temporary download/install data was
  removed immediately after verification.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
