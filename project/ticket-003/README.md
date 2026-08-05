# Ticket 003: Governed Goal delivery modes

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-05
- **Workstream**: application
- **Depends on**: ticket-002
- **Response required from**: none

## Goal and scope

Make repository governance capable of requiring a controlled `goal -a` run
before remote delivery. A governed repository selects an allowed delivery mode
instead of relying on an implicit raw `git push`:

1. `direct-main`: run the complete Goal workflow and push only from the
   configured base branch directly to the matching remote branch.
2. `publish-only`: run the governed checks and registry publication without
   pushing commits or tags to the Git remote.
3. `pull-request`: let Goal create or reuse a controlled head branch, push that
   branch, and create a pull request to the configured base branch.

The feature must not present a local Git hook as a security boundary. The hook
is a fail-fast developer guard; branch protection and a required CI status are
the authoritative server-side enforcement against `git push --no-verify`, hook
removal, and calls made outside Goal.

## Proposed configuration contract

```yaml
governance:
  delivery:
    require_goal_a: true
    default_mode: pull-request
    allowed_modes: [direct-main, publish-only, pull-request]
    remote: origin
    base_branch: main
    require_clean_governance: true
```

CLI selection is explicit with
`goal -a --delivery-mode direct-main|publish-only|pull-request`. When the option
is omitted, Goal uses `default_mode`. A requested mode outside `allowed_modes`
fails closed before commit, push, tag, PR creation, or publication.

## Planned changes

1. Add a typed delivery-policy loader and validator for `goal.yaml`.
2. Expose `--delivery-mode` in the root `goal -a` flow and forward the resolved
   policy through `PushContext`.
3. Add `goal governance delivery-hook install|check|remove` without overwriting
   unrelated commands in an existing `pre-push` hook.
4. Authorize remote pushes only for the active Goal delivery transaction and
   record mode, base, head and result in `.governance/delivery-events.jsonl`.
5. Implement `direct-main` with exact branch/remote checks and no silent
   cross-branch refspec.
6. Implement `publish-only` so Git commit/tag push stages are skipped while
   governance validation, tests, build and configured publication remain
   active.
7. Implement `pull-request` with a deterministic `goal/<ticket-or-change-id>`
   head branch and `gh pr create`; never fall back to direct `main` push.
8. Add a machine-readable CI verification result and actionable CLI guidance
   for protected branch rules.
9. Add focused CLI, policy, hook and delivery tests without performing network
   operations.

## Acceptance criteria

- [x] AC-01: `require_goal_a: true` blocks a normal local `git push` through
  the managed hook with an actionable `goal -a` command.
- [x] AC-02: invalid, missing, or disallowed modes fail closed before side
  effects.
- [x] AC-03: `direct-main` works only on the configured base branch and remote.
- [x] AC-04: `publish-only` never invokes Git commit/tag push or PR creation.
- [x] AC-05: `pull-request` pushes only its controlled head and creates or
  reports the PR targeting the configured base branch.
- [x] AC-06: Goal's own push receives transaction-scoped authorization; raw
  environment flags alone are not accepted as durable authorization.
- [x] AC-07: each attempt appends a secret-free JSONL audit event under
  `.governance/`.
- [x] AC-08: existing `pre-push` behavior is preserved on install and restored
  on removal.
- [x] AC-09: CLI verification states that local hooks are bypassable and provides
  branch-protection plus required-status setup for authoritative enforcement.
- [x] AC-10: existing `goal push`, `goal publish`, and bare `goal -a` behavior
  remains compatible when no delivery policy is configured.

## Risks

- **False security**: local hooks can be bypassed; do not claim server-grade
  enforcement without protected branches and required CI checks.
- **Registry traceability**: `publish-only` can publish code not reachable from
  the remote. The audit event must preserve the local commit SHA and policy
  decision, and governance may disable this mode.
- **PR tooling**: missing or unauthenticated `gh` must fail closed and retain
  the prepared branch without pushing to `main`.
- **Hook ownership**: installation must use a bounded managed block or hook
  dispatcher and must not replace project-owned shell logic.
- **Dirty worktree**: ticket implementation must not absorb unrelated changes.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [`ai-codex.md`](ai-codex.md).
