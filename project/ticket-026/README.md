# Ticket 026: Preserve clean publish-only release intent

- **ID**: ticket-026
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10

## Goal and scope

Allow an explicitly forced `publish-only` run on a clean, protected merged
checkout to validate, test and publish its already synchronized version. The
no-files shortcut currently discards this release intent and exits successfully
without publishing, blocking Goal 2.1.293.

## Acceptance criteria

- [x] AC-01: The clean-tree publication failure is reproduced on merged
  `main` with `--force-publish`.
- [x] AC-02: Clean forced publication bypasses only the no-files shortcut,
  validates a pre-bumped synchronized version and runs tests.
- [x] AC-03: The clean release path never creates a commit and fails closed for
  an unresolved or normal-bump version decision.
- [x] AC-04: Regression coverage and the full test/governance/CI/validator chain
  pass before protected merge.
- [x] AC-05: Ticket-025 can publish Goal 2.1.293 from the resulting clean
  protected `main`.

## Completion evidence

- PR #53 was exact-head validated at
  `c64c7c4c5411e7760581649e79fd99d3992bfbed` by validator run
  `31427369125` and merged to protected `main` as
  `0b8f7563fe261b402dc9742ae187864261ce7c94`.
- The target CI matrix passed on Python 3.12 and 3.13; local validation passed
  with 522 tests and 2 skips and governance reported no findings.
- A clean checkout of the merge selected `already-bumped -> 2.1.293`, ran the
  full tests, skipped commit creation and published both distributions through
  governed `goal -a --delivery-mode publish-only --force-publish`.
- A fresh no-cache public-index environment reported Goal 2.1.293.

## Boundary

This application slice owns `goal/push/core.py`, its focused regression test
and ticket metadata. Release carriers, package metadata, dependencies,
top-level changelog, governance and CI are excluded.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
