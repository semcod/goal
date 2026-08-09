# Ticket 009: Preserve contract VERSION files and governed direct pushes

- **ID**: ticket-009
- **Owner**: session user (identity unresolved)
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-09
- **Work classification**: `SERVICE / delivery`

## Goal and scope

Preserve multi-line `VERSION` integrity manifests in repositories where that
file is a data contract rather than release metadata.  Treat repositories
without a package registry as plain-commit projects, and let the pre-push hook
accept an explicitly selected delivery mode when that mode is permitted by the
policy even if it differs from the policy default.

## Acceptance criteria

- [x] AC-01: The user explicitly authorized updating the dependency in source
  and publishing it with `goal -a`.
- [x] AC-02: Multi-line `VERSION` contracts are neither detected nor rewritten
  as release versions.
- [x] AC-03: A no-registry repository uses a plain commit without a synthetic
  version bump or registry publication.
- [x] AC-04: A `direct-main` transaction is accepted when `direct-main` is an
  allowed mode and the configured default is `pull-request`.
- [ ] AC-05: Full tests, governance validation and governed publication pass.

## Validation evidence

- Version/push focused suite: 69 passed.
- Delivery-governance focused suite: 76 passed.
- Full suite before the delivery-mode repair: 480 passed, 2 skipped.
- Final full suite: 481 passed, 2 skipped.
- Governance check: PASS (0 errors, 0 warnings).
- Governed publication: pending.

## Participants

- Human participant: session user; no `user-*` file was generated.
- Agent participant: [ai-codex.md](ai-codex.md).

## Session authorization

On 2026-08-09 the user requested continued autonomous work, direct source
updates of the dependency, and publication through `goal -a`.  That instruction
authorizes the narrowly scoped implementation and delivery recorded here.

## Boundary

This ticket does not change credentials, provider behavior, branch protection,
the set of allowed delivery modes, or any human-owned participant file.
