# Ticket 218: Qualify canonical release checkout preflight and exact-head delivery

- **ID**: ticket-218
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-28

## Goal and scope

Qualify `DeliveryPolicy(mode="direct-main")` for canonical Worktrees v5 release checkouts (`<primaryCheckout>/.worktrees/ticket-NNN--<slug>`) bound to an explicit `--ticket ticket-NNN`, active `wellmanifest.change-lease/v1` lease, clean working tree, exact authoritative remote base SHA (`origin/main`), and independent terminal merge receipt (`.git/new-project/terminal-receipts.json`), while failing closed on primary, `/tmp`, legacy, duplicate, symlinked, dirty, unbound, or unapproved checkouts, revalidating exact-head/lease/receipt state after test execution before tag/publish/push, and pushing only the release tag without moving `main` or touching dirty/foreign primary checkouts (closes #163).

- `SESSION_EXECUTION_AUTHORIZATION`: autonomous session execution requested by user.

## Acceptance criteria

- [x] AC-01: Admit `direct-main` release preflight in a canonical linked worktree `<primaryCheckout>/.worktrees/ticket-NNN--<slug>` with explicit `--ticket ticket-NNN`, relative `.git` link, no symlinks, no duplicate worktrees, clean release worktree, `HEAD == origin/<base_branch>`, valid active `wellmanifest.change-lease/v1` lease, and verified terminal merge receipt in `<git_common_dir>/new-project/terminal-receipts.json`, while preserving dirty/foreign primary checkouts untouched.
- [x] AC-02: Fail closed with clear diagnostics when `--ticket` is missing, checkout is primary, `system-temp` (`/tmp`), `legacy-v1`..`legacy-v4`, `unknown`, symlinked, or `duplicate-delivery`, branch does not match `ticket/NNN-<slug>`, release worktree is dirty, `HEAD != origin/<base_branch>`, lease is missing/expired/released/mismatched, or terminal merge receipt is missing/stale/wrong-repository.
- [x] AC-03: In `execute_push_workflow`, enforce read-only bootstrap and clean release checkout, revalidate exact-head/remote-base/lease/receipt admission after `run_test_stage` before tag creation, package publication, remote tag push, or GitHub release, push only `refs/tags/v<version>` (never moving `main` or pushing the ticket branch), and support idempotent `existing-tag-release-repair` when the remote tag already matches `HEAD`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
