# Ticket 113: Refuse default-branch delivery from an ungoverned checkout of a governed clone

- **ID**: ticket-113
- **Owner**: claude-goal
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-15

## Goal and scope

On 2026-09-15 `semcod/monag` received commit `04228b3` ("chore(goal):
configuration management") pushed straight to `main`. The repository's
adoption existed only on the ticket-001 worktree, so the default checkout had
no `.governance/manifest.json`. `goal -a` there took the legacy path:
`ensure_config()` pruned a version file that lived in the ticket worktree,
rewrote `goal.yaml`, committed it and pushed the default branch without the
gate. Reproduced in an isolated fixture with a bare remote.

Goal now treats a checkout as governed when any registered worktree of its
clone carries the adopted manifest or the primary checkout holds worktree
leases. Legacy delivery from such a checkout is refused before any commit with
`GOV-DELIVERY-CLONE-001`, and `goal -a` loads its configuration read-only there.
Repositories without governance anywhere keep the legacy flow.

## Acceptance criteria

- [x] AC-01: `goal -a --no-publish` in the default checkout of a clone whose
  ticket worktree is governed exits non-zero with `GOV-DELIVERY-CLONE-001`,
  leaves `goal.yaml` byte-identical and does not move the remote default branch.
- [x] AC-02: A primary worktree lease marks the clone governed; a linked
  worktree without governance keeps the legacy flow.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

SESSION_EXECUTION_AUTHORIZATION: the user requested investigating and fixing
regressions detected in this session, pushing, testing and merging through the
declared review process. No self-approval or direct merge.
