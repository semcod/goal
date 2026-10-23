# Ticket 196: Complete pending publication autonomously and protect frozen goal config

- **ID**: ticket-196
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-23

## Goal and scope

Two autonomy defects on governed repositories after the independent validator
merges a release wave:

1. Governed pull-request mode returned "No changes to deliver" on a clean,
   synchronized base even when committed package sources were still awaiting
   the waited-for publication (the legacy flow already continued; the
   pull-request branch returned early). Now the branch completes the publish
   (tag + registry) without creating a commit.
2. Config auto-detection rewrote goal.yaml for any command on governed targets
   (previously only dry-run/--all were protected) and replaced an explicit
   `versioning.files` projection with stale cache snapshots once the real
   source stopped carrying a static version literal. Detection now skips
   tooling caches and governed runtime state, never replaces an explicit
   non-empty `versioning.files`, and governed targets load the config without
   rewrites from every command.

## Acceptance criteria

- [ ] AC-01: Pull-request mode with a clean synchronized base and pending committed sources records `publish-completion`, re-enables publishing and proceeds past the no-change boundary (tests assert the flow and context flags).
- [ ] AC-02: Without pending sources the boundary stays a `no-change` return.
- [ ] AC-03: Version-file discovery ignores `.pytest_cache`/`.subactor` snapshots; `update_from_detection` preserves an explicit non-empty `versioning.files`; a governed target loads config without rewrite from a non-dry, non-`-a` command.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
