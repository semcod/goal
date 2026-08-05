# Ticket 002: Pinned governance bootstrap for Goal

- **ID**: ticket-002
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-04
- **Workstream**: governance
- **Depends on**: ticket-001
- **Response required from**: unresolved:human

## Goal and scope

Adopt an immutable, published `wellmanifest/new-project` governance package in
Goal, preserve existing project-owned content, and configure the target
manifest so later implementation tickets can own `goal/**` and `tests/**`
without overlapping workstreams.

This ticket owns governance bootstrap files only. Root Docker/compose setup,
release implementation, tests and dependency changes belong to later tickets.

## Planned changes

1. Resolve a reviewed, published full standard revision containing the current
   adoption generator and lock schema.
2. Run adoption preflight in check mode and review every managed target.
3. Adopt the exact revision without an unreviewed overwrite.
4. Preserve the existing Goal-specific analysis pipeline as
   `project/analysis.sh`; install the standard governance-only root
   `project.sh`.
5. Customize only `.governance/manifest.json` for Goal package paths and retain
   the standard version.
6. Regenerate the immutable lock through the standard generator.
7. Run the deterministic governance gate and record stable diagnostics.

## Acceptance criteria

- [ ] AC-01: Lock identifies a published 40-character source revision.
- [ ] AC-02: Managed file hashes match the adopted revision.
- [ ] AC-03: Existing `project/README.md` remains owned by the analysis
  generator and is not overwritten.
- [ ] AC-03a: Existing root `project.sh` analysis commands remain available via
  `project/analysis.sh`, while root `project.sh` becomes the pinned gate.
- [ ] AC-04: Manifest declares non-overlapping ownership for `goal/**`,
  `tests/**`, docs/contracts and infrastructure.
- [ ] AC-05: Ticket tooling never creates a human-owned `user-*.md` file.
- [ ] AC-06: Governance gate runs deterministically and its output is logged.
- [ ] AC-07: Existing unrelated worktree changes remain preserved.
- [ ] AC-08: No OpenRouter/LLM call is made during governance bootstrap;
  Gemini 3.1 Pro Preview remains prohibited.

## Risks

- **Unpublished source**: fail closed; do not create a lock that claims
  `publicationStatus: published` for uncommitted files.
- **Managed-file drift**: require target-by-target review before `--upgrade`.
- **Existing project.sh**: preserve its analysis role separately if the
  standard replaces the root entry point.
- **Dirty worktree**: do not absorb or overwrite earlier governance-adoption
  implementation changes.

## Source verification

Published revision `c0bb63e7fc889934140c96b1625f3ab232122baf` identifies version
0.9.0 and contains both the adoption generator and lock schema.

## Current state

Human approval was received on 2026-08-05. The legacy analysis entry point was
preserved as `project/analysis.sh`, and the pinned standard was adopted. Target
workstream ownership uses the Python-only package profile; lock regeneration is
in progress.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [`ai-codex.md`](ai-codex.md).
