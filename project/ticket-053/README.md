# Ticket 053: Adopt the complete new-project 0.16.1 governance package

- **ID**: ticket-053
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-12

## Goal and scope

Upgrade Goal's managed governance package from `new-project` 0.14.1 to the
complete published 0.16.1 payload at exact commit `4e6ba5ec...`. Tickets 051
and 052 already integrated the cross-owner checker and workflow prerequisites,
so the remaining 23-path adoption plan is entirely governance-owned.

## Acceptance criteria

- [x] AC-01: `goal governance adopt --upgrade` applies exactly the reviewed
      23-path plan and pins published source revision `4e6ba5ec...` / standard
      version 0.16.1 without changing `.github/**` or Goal runtime code.
- [x] AC-02: Deterministic governance, package drift checks and the workspace
      lifecycle audit pass from the adopted package.
- [x] AC-03: The adopted remediation-intent schema, template and analyzer
      validate the DSL, render canonical LLM/todo2code inputs, bind advisory
      todo2code output by digest and reject unsafe/stale plans.
- [ ] AC-04: Full Goal tests pass before a protected PR; Python 3.12/3.13 CI,
      the remote-lifecycle job and exact-head Validator approval are required
      before merge.

## Reviewed adoption plan

- Update/chmod 12 existing `.governance` contract files and create 10 managed
  diagnostics, runbook, remediation and workspace-lifecycle assets.
- Update `AGENTS.md`, `project/new-ticket.sh` and the managed lock.
- No `.github/**`, package source, tests, release version or human-owned file
  is in the plan.

## Prerequisite discovered by the adopted gate

The 0.16.1 validator correctly rejected the former local-build-only
`compose.yml` image tag as mutable. Ticket 054 removed that redundant tag and
closed on `main` at `05f7250c...`; ticket 053 is therefore active again and the
managed payload is bound atomically from the old to the new standard revision.

## Local validation evidence

- Public Goal 2.1.298 upgraded the target and its immediate `--check` reports
  the package is up to date at new-project 0.16.1 / `4e6ba5ec...`.
- The adopted gate passes the complete working-tree change set against accepted
  base `05f7250c...`; the non-terminal workspace audit passes only with the
  exact active worktree allowlisted.
- The DRAFT template validates but is rejected as executable input. The full
  upstream governance-script suite passes READY rendering, todo2code advisory
  binding, unsafe-plan rejection and stale-overlay rejection against the exact
  byte-identical adopted analyzer.
- The complete Goal suite passes: 600 tests, with 2 existing skips.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
