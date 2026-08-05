# Ticket 005: Enable governed delivery policy in Goal

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-05
- **Workstream**: governance
- **Depends on**: ticket-003
- **Response required from**: none

## Goal and scope

Activate the delivery controls implemented by ticket-003 in the Goal
repository itself. Make `goal.yaml` a governance-owned contract, select
pull-request delivery by default, retain explicit direct-main and publish-only
options, and install the bounded local pre-push hook.

This ticket does not configure GitHub branch protection because that is a
server-side administrative change. `verify-delivery` must continue to report
that protected branches and a required CI status are necessary for
authoritative enforcement.

## Planned changes

1. Assign `goal.yaml` to the governance workstream in the target manifest.
2. Configure `governance.delivery` with `require_goal_a: true`, default
   `pull-request`, all three allowed modes, `origin`, and base branch `main`.
3. Regenerate the immutable adoption lock after the reviewed manifest change.
4. Install the bounded `pre-push` block without replacing existing hook logic.
5. Run `goal governance verify-delivery`, hook check, and ticket-scoped gate.
6. Commit and push the activation through a pull request rather than bypassing
   the newly selected default.

## Acceptance criteria

- [x] AC-01: `goal.yaml` is owned by the governance workstream.
- [x] AC-02: raw local push is blocked when no valid Goal transaction exists.
- [x] AC-03: bare governed `goal -a` resolves to `pull-request`.
- [x] AC-04: `direct-main` and `publish-only` remain explicitly selectable.
- [x] AC-05: existing project-owned pre-push logic remains intact.
- [x] AC-06: lock matches the customized manifest.
- [x] AC-07: verification reports that local hooks are bypassable and server
  protection remains required.
- [x] AC-08: ticket-scoped governance validation passes.

## Risks

- **Hook bypass**: `--no-verify` remains possible; require server protection.
- **Default behavior**: after activation, bare `goal -a` creates a PR instead
  of pushing directly to main.
- **Local-only hook**: Git hooks are not distributed by Git; each clone must
  run the install command or an approved bootstrap.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [`ai-codex.md`](ai-codex.md).
