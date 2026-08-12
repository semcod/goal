# Ticket 042: Keep help and no-version-sync delivery coherent

- **ID**: ticket-042
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-12

## Goal and scope

Repair two read-only/commit-only CLI invariants exposed while delivering the
already merged ticket-041 closure. Subcommand help must not initialize or
rewrite `goal.yaml`. A full workflow with the explicit combination
`--no-version-sync --no-tag --no-publish` must make a plain tested commit even
when package source has been committed since the latest release; it must not
compute a new release version and then reject the deliberately unchanged
version carriers.

## Acceptance criteria

- [ ] AC-01: `goal push --help` is observably read-only with both missing and
  existing configuration.
- [ ] AC-02: Explicit commit-only flags keep the released version unchanged,
  make one plain commit/push, and do not publish or tag despite committed
  unreleased package source.
- [ ] AC-03: Normal release behavior remains unchanged when any commit-only
  condition is absent.
- [ ] AC-04: Focused/full tests, scoped Ruff, governance, package and Docker
  builds pass before exact-head protected delivery.

## Boundary

- No version carrier, registry, tag or release change belongs to this
  application ticket.
- Do not weaken normal committed-unreleased source detection. Only the three
  simultaneous explicit suppressions form commit-only intent.
- The user's instruction to repair and continue is recorded as bounded
  `SESSION_EXECUTION_AUTHORIZATION`; trusted merge still requires external
  exact-head evidence.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
