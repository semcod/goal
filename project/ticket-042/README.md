# Ticket 042: Keep help and no-version-sync delivery coherent

- **ID**: ticket-042
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
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

- [x] AC-01: `goal push --help` is observably read-only with both missing and
  existing configuration.
- [x] AC-02: Explicit commit-only flags keep the released version unchanged,
  make one plain commit/push, and do not publish or tag despite committed
  unreleased package source.
- [x] AC-03: Normal release behavior remains unchanged when any commit-only
  condition is absent.
- [x] AC-04: Focused/full tests, scoped Ruff, governance, package and Docker
  builds pass before exact-head protected delivery.

## Boundary

- No version carrier, registry, tag or release change belongs to this
  application ticket.
- Do not weaken normal committed-unreleased source detection. Only the three
  simultaneous explicit suppressions form commit-only intent.
- The user's instruction to repair and continue is recorded as bounded
  `SESSION_EXECUTION_AUTHORIZATION`; trusted merge still requires external
  exact-head evidence.

## Validation evidence

- 53 focused delivery/push tests pass. The regression asserts that committed
  unreleased source is not even queried in explicit commit-only mode, while
  existing normal release tests retain that detection.
- Scoped Ruff and `git diff --check` pass.
- A real source invocation in an isolated directory rendered
  `python -m goal push --help` without creating `goal.yaml`.
- Full validation passes: 573 tests with 2 existing skips, scoped Ruff,
  `GOV-PASS`, wheel/sdist build and Docker image
  `sha256:284242e79a0d28db725429c5b3aef6e1f270b529552ca89aabaa018cc18fbc63`.
  The temporary tagged image was removed immediately after the build.
- Goal's repaired commit-only path itself passed 573 tests (2 skips), kept
  2.1.295 unchanged, created only PR #67, and performed no publish/tag action.
  GitHub CI passed on Python 3.12/3.13; Validator App review `4914980609`
  approved exact head `910fcc685127198fbe798cad178c483feb096308`.
- PR #67 merged as `main@f31e07b1b23a30807b92e6b76ac6b3418ea459fc`.
  A detached clean-merge retest passed 53 focused tests and `GOV-PASS`.
  The remote branch disappeared automatically; the local worktree, branch and
  Docker validation image were removed after reachability proof.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
