# Ticket 067: Publish Goal 2.1.301 standard update protocol

- **ID**: ticket-067
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-02

## Goal and scope

Publish the merged ticket-064 authenticated latest-release and pre-commit
standard-update protocol as Goal 2.1.301. Synchronize only the established
release carriers through protected PR delivery, then publish immutable PyPI
artifacts, annotated tag and final GitHub Release from clean merged `main`.

## Acceptance criteria

- [x] AC-01: The user's instruction to continue, deploy and test records
  `SESSION_EXECUTION_AUTHORIZATION` for this bounded release.
- [x] AC-02: Exactly the five established release carriers are synchronized to
  2.1.301 together with ticket-owned governance evidence.
- [x] AC-03: Full tests, Ruff, governance, package build and Docker validation
  pass before protected exact-head review and merge.
- [ ] AC-04: Clean merged `main` publishes one wheel and one sdist, annotated
  `v2.1.301` and a final GitHub Release bound to the same source.
- [ ] AC-05: A fresh public-index installation exposes
  `goal governance adopt --latest --pre-commit --ticket`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

No executable source or dependency-set change belongs to this release ticket.
Existing immutable releases are never moved or replaced.
