# Ticket 032: Expose packaged governance check through Goal

- **ID**: ticket-032
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-11

## Goal and scope

Expose the deterministic validator adopted from `wellmanifest/new-project`
through a stable `goal governance check` command and keep governance package
operations headless. Goal owns invocation, argument forwarding and failure
behavior; the pinned target repository package remains the source of validator
code and policy data.

## Acceptance criteria

- [x] AC-01: The user's instruction that `new-project` use Goal supplies
  bounded execution authorization for this adapter.
- [x] AC-02: `goal governance check` invokes the target's adopted validator
  with its manifest, lock and stack profiles.
- [x] AC-03: Validator arguments, stdout, stderr and nonzero exit status are
  preserved without Goal reimplementing policy decisions.
- [x] AC-04: Missing or incomplete adopted governance fails closed with an
  actionable diagnostic, while the governance dispatcher skips Goal's
  interactive user bootstrap, implicit `goal.yaml` writes, update lookup and
  version banner. Callbacks that need delivery configuration opt in explicitly.
- [x] AC-05: Focused and full tests, changed-file Ruff, governance, package
  build and Docker validation pass.

## Validation evidence

- All 9 focused governance CLI tests, 20 governance/delivery integrity tests
  and the full suite of 532 tests with 2 skips pass; changed-file Ruff and
  governance pass.
- `uv build` produces the wheel and source distribution.
- The production image builds and runs `goal governance check` offline without
  the first-run wizard, version banner, config writes or update lookup.
- Running the adapter against Goal's real adopted package returns `GOV-PASS`
  with zero errors and warnings.
- Running it against `glon` fails closed with the exact four missing adopted
  package files and the `goal governance adopt` remediation; `glon` currently
  has only a legacy analysis `project.sh`, not new-project adoption.
- Initial container execution exposed Goal's unrelated first-run wizard before
  dispatch. The exact `governance check` path now uses a read-only main context;
  a clean container reaches the intended fail-closed adoption diagnostic only.
- A later exact-SHA standard pilot reproduced the remaining gap:
  `goal governance adopt --target-root <other-repo>` created `goal.yaml` in the
  caller's standard worktree before adoption. Both generated files were
  identified as command artifacts and removed from the pilot worktrees.
- The group dispatcher now enters read-only context for every
  `goal governance ...` path. A real fake-standard adoption from a separate
  caller proves that mutable main setup is never reached, the target is
  adopted and no caller-side `goal.yaml` appears.
- The updated branch passes 10 focused and 533 full tests with 2 skips, Ruff,
  deterministic governance, wheel/sdist build and the digest-pinned production
  Docker build (`sha256:6772b0ac7d93...`).
- Exact implementation HEAD `65e2cff` ran the combined standard `365ba23`
  through Goal from a separate empty caller into a fresh `fixop` target.
  Preflight/adoption retained managed output and prerequisite reporting while
  the caller remained completely empty before and after both invocations.

## Boundary

This ticket adds only the Goal-side runtime adapter/context and its regression
tests.
It does not edit the canonical standard, adoption payload, validator rules,
delivery policy, dependency manifests or release metadata. The subsequent
`new-project` wrapper migration is a separate repository-local ticket.

## Session authorization

The user's direct instruction to continue and route `new-project` through Goal
creates `SESSION_EXECUTION_AUTHORIZATION` for this bounded local change. Push,
pull-request creation, merge and publication remain outside this authorization.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
