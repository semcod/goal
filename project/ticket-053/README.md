# Ticket 053: Adopt the complete new-project 0.16.1 governance package

- **ID**: ticket-053
- **Owner**: unresolved:human
- **Status**: BACKLOG
- **Workflow state**: PLAN
- **Created**: 2026-08-12

## Goal and scope

Upgrade Goal's managed governance package from `new-project` 0.14.1 to the
complete published 0.16.1 payload at exact commit `4e6ba5ec...`. Tickets 051
and 052 already integrated the cross-owner checker and workflow prerequisites,
so the remaining 23-path adoption plan is entirely governance-owned.

## Acceptance criteria

- [ ] AC-01: `goal governance adopt --upgrade` applies exactly the reviewed
      23-path plan and pins published source revision `4e6ba5ec...` / standard
      version 0.16.1 without changing `.github/**` or Goal runtime code.
- [ ] AC-02: Deterministic governance, package drift checks and the workspace
      lifecycle audit pass from the adopted package.
- [ ] AC-03: The adopted remediation-intent schema, template and analyzer
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

The 0.16.1 validator correctly rejects the existing local-build-only
`compose.yml` image tag as mutable. That infrastructure-owned repair must be
integrated first in a separate non-overlapping ticket. This ticket releases
its reservation while waiting and will return to `IN_PROGRESS` before applying
the atomic managed payload.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
