# Ticket 105: Deterministic pinned governance adoption planner

- **ID**: ticket-105
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-14

## Goal and scope

Implement a read-only, deterministic pinned adoption planner in Goal. The
planner preserves a supported current pin by default and uses only explicitly
declared migration edges to prepare exact-revision Goal adoption steps.
Catalog input is operator-supplied policy data, not approval evidence.
This slice covers new-project; fleet execution and cross-pack certification
remain separate work.

## Acceptance criteria

- [x] AC-01: Supported pins remain unchanged; newer releases alone cause no work.
- [x] AC-02: Known migration routes produce stable, digest-bound plans without LLM,
  network, repository writes or arbitrary recipe execution.
- [x] AC-03: Invalid catalogs, missing routes and dirty/stale observations cannot
  produce executable migration steps. Focused tests and managed governance pass.

Local validation: initial focused suite 74 passed; full suite 812 passed,
2 skipped. Managed gate passed with zero errors/warnings; baseline staged
Giton secret scan found zero matches. Added a final root-dispatcher regression;
rerun evidence accompanies the publication checkpoint. This is not deployed
fleet automation or protected exact-head review evidence.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
