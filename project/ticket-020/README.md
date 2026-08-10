# Ticket 020: Record Goal 2.1.291 publication evidence

- **ID**: ticket-020
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / integration`

## Goal and scope

Deliver the metadata intentionally split from ticket-019: public registry
evidence, exact-head release provenance, user-facing 2.1.291 release notes and
the cost badge refreshed by the governed publish-only run. This slice proves
that the repaired version boundary yields `no-release -> 2.1.291` after the
registry catches up.

## Acceptance criteria

- [x] AC-01: Publish-only selected `already-bumped -> 2.1.291`, published two
  artifacts and never proposed 2.1.292.
- [x] AC-02: PyPI JSON/Simple APIs expose 2.1.291 wheel and sdist.
- [x] AC-03: A fresh Python 3.13 public-index install reports 2.1.291 for CLI
  and import from isolated site-packages.
- [x] AC-04: Changelog and ticket-019 record the release fix and protected
  delivery chain; README retains the publish-run cost refresh.
- [ ] AC-05: This metadata-only PR passes governance, target CI and exact-head
  validator approval before merge.

## Session authorization

The user explicitly requested autonomous testing and publication. This is the
bounded evidence/closure phase of that already authorized release; no repeated
confirmation is required. Exact-head merge approval remains external.

## Boundary

Only publication documentation, cost evidence, ticket closure metadata and
the ticket/TODO indexes may change. No version carrier, package source,
dependency, lockfile, governance policy, CI workflow or registry artifact is
modified here.

## Participants

- Human participant: unresolved; no user-* file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
