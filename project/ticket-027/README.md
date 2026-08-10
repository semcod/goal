# Ticket 027: Create a fresh PR after a prior branch PR was merged

- **ID**: ticket-027
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-10
- **Work classification**: `BUG / regression / P1 / application`

## Goal and scope

Make governed pull-request delivery distinguish an open PR from historical
closed or merged PRs that used the same controlled branch. Goal 2.1.293
currently asks `gh pr view <branch>` without a state boundary. During the
Koru ticket-008 completion run it pushed exact head `7204329`, returned merged
PR #28 (whose head was `ef673a4`) and left the new branch without an open PR.

The repair must query only open PRs for the declared base/head pair, bind a
reused PR to the current pushed HEAD and verify a newly created PR through the
same exact-head lookup.

## Acceptance criteria

- [x] AC-01: The user requested autonomous Goal refactoring and publication;
  this concrete regression was reproduced in `semcod/koru`.
- [x] AC-02: A merged or closed historical PR is never returned as the result
  of a later governed delivery on the same controlled branch.
- [x] AC-03: Goal reuses only one open PR matching both declared base/head and
  the current pushed commit SHA.
- [x] AC-04: After `gh pr create`, Goal resolves the new open PR again and
  fails closed if its exact-head binding cannot be proven.
- [x] AC-05: Focused regression tests, full Python tests, governance, Docker,
  hosted CI and exact-head validator approval pass before merge.

## Boundary

This application slice owns only the governed PR delivery module and its
focused contract tests. It does not change version carriers, dependencies,
release metadata, GitHub workflows, the local authorization capability or
the target repository's protected approval boundary.

## Local validation evidence

- Focused governed-delivery contract: 10 tests passed, including the three
  new historical/open/stale-head scenarios.
- Full Python suite: 525 passed and 2 skipped.
- Ruff on both implementation files: PASS.
- Repository governance: 0 errors, 0 warnings; `git diff --check`: PASS.
- Production Docker image built successfully; offline `--network none` smoke
  reports Goal 2.1.293.
- Goal registry comparison selects `normal-bump -> 2.1.294`; the application
  ticket intentionally leaves release carriers to a later integration ticket.

## Delivery evidence

- Pull request: `semcod/goal#56`.
- Approved exact head: `0fafc34cd8c7ac4d12707f9998b5a295d88f8926`.
- Target CI run: `31437352017`; Python 3.12 and 3.13 PASS.
- Validator run: `31437462144`; approval identity:
  `ifuri-validator-agent[bot]`.
- Merge commit: `5aab7bc874ec6100dedc7dc0666002223c6c1317`.
- The controlled branch was deleted and no PR remains open after merge.

## Session authorization

The user's standing request explicitly includes autonomous Goal refactoring,
testing and publication. It is recorded as
`SESSION_EXECUTION_AUTHORIZATION`; no redundant confirmation is required for
the bounded paths in `intent.json`.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
