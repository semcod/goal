# Ticket 010: Dependency-aware version state validation and synchronization

- **ID**: ticket-010
- **Owner**: session user (identity unresolved)
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-09
- **Work classification**: `SERVICE / release`

## Goal and scope

Make Goal determine release versions from a complete, explainable version
state instead of blindly bumping the first version source it finds.  The
decision must distinguish a normal release from a version that was already
bumped locally, repair an unambiguous partial bump, and stop on ambiguous
drift before commit, tag, build or publication.

The state is built from configured and safely auto-detected version sources,
Git release evidence and optional registry evidence.  It also identifies
derived files (lock files and badges) affected by synchronization.  Explicit
CLI intent (`--target-version`, then `--bump`) has precedence, but it is still
validated against published/released versions and every configured source.

## Decision rules

1. A valid explicit `--target-version` is the requested target; Goal reports
   why it was selected and synchronizes stale sources to it.
2. If Git/registry evidence establishes a released baseline and local sources
   contain exactly one newer candidate, Goal treats that candidate as an
   already applied bump.  Sources still at the baseline are repaired forward;
   the candidate is not bumped a second time.
3. If every local source equals the released baseline, Goal computes the next
   version using the requested bump kind.
4. A source below the release baseline is repaired forward when another
   managed source proves the baseline and there is no conflicting forward
   candidate.  Without package changes this is a repair-only commit; with
   package changes all sources advance to the next release.  Ambiguous
   regressions, conflicting forward candidates, unreadable sources or residual
   drift remain fatal.
5. Registry lookup is safety evidence, not a required online dependency.  An
   unavailable registry is reported and Git/local evidence remains usable;
   a registry version ahead of the selected target blocks publication.
6. Multi-line `VERSION` contracts and independently versioned nested projects
   remain outside the synchronized release set.  Nested packages already in
   lockstep remain part of it.

## Acceptance criteria

- [x] AC-01: A human owner approves this scope and the transition to
  `IN_PROGRESS / EDIT`.
- [x] AC-02: Goal inventories every configured or safely detected version
  source and reports its path, selector, observed value and relation to the
  selected baseline/target.
- [x] AC-03: The version resolver handles normal, already-bumped and partial
  bump states according to the decision rules without performing a second
  accidental bump.
- [x] AC-04: `--target-version` and `--bump` reach the resolver consistently in
  `goal push`, bare `goal -a` and dry-run mode.
- [x] AC-05: Synchronization is followed by strict read-back validation;
  missing, unreadable, unsupported or still-stale configured sources stop the
  workflow before commit, tag, build or publication.
- [x] AC-06: `goal check-versions` and dry-run explain the decision and affected
  derived files without mutation, while retaining registry comparison.
- [x] AC-07: Regression tests cover a complete pre-bump, partial pre-bump,
  ordinary bump, explicit target, divergent candidates, registry-ahead guard,
  multiline contracts and lockstep versus independent monorepo packages.
- [x] AC-08: Focused tests, the full Python suite and
  `project/governance-check.sh` pass before publication is considered.

## Analysis evidence

- `goal.cli.version_utils.get_current_version()` currently trusts the first
  readable source and never exposes disagreement among sources.
- `goal.push.core.execute_push_workflow()` calls `get_version_info()` without
  the requested bump or `ctx.obj["version"]`; consequently the global target
  version is recorded but not used for release selection.
- `sync_all_versions()` captures one root value and updates nested manifests
  only when they equal it.  In a partial bump, a stale nested file can therefore
  be excluded from repair.
- Several writers warn and continue on errors.  There is no strict read-back
  gate immediately before the release commit and publication.
- `goal check-versions` currently compares the first local version only with a
  registry; it does not validate local file-to-file consistency.

## Participants

- Human participant: session user; no `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Boundary

This ticket does not modify registry credentials, publishing providers,
delivery-mode authorization, branch protection, human-owned participant files
or independently versioned example/vendor projects.  Documentation changes
outside the ticket require a separate integration workstream ticket.

## Session authorization

On 2026-08-10 the session user reviewed the prepared scope and explicitly
instructed the agent to continue.  This authorizes the transition from
`PLAN / WAIT_FOR_APPROVAL` to the narrowly scoped implementation in
`IN_PROGRESS / EDIT`.

## Validation evidence

- Version-focused suite: 115 passed, 1 optional skip.
- Full Python 3.13 suite: 501 passed, 2 optional skips.
- Focused Python 3.12 suite: 68 passed.
- Container integration matrix on Python 3.12: 8 project types passed, 0
  failed.
- `goal --ascii check-versions` on Goal itself reports matching Git tag and
  PyPI evidence, all three managed version declarations and derived updates.
- Governance check: PASS (0 errors, 0 warnings).
- Post-publication smoke exposed that standalone `check-versions` did not yet
  reuse the release-intent classifier from `goal -a`; a documentation-only
  tree could therefore be reported as a normal bump.  The same file and Git
  evidence now drives both commands, with regression coverage for uncommitted
  documentation and committed-but-unreleased package source.
- Follow-up focused suite: 88 passed, 1 optional skip.
- Follow-up full Python 3.13 suite: 503 passed, 2 optional skips.
- Follow-up focused Python 3.12 suite: 40 passed.
- Follow-up governance check: PASS (0 errors, 0 warnings).

## Infrastructure observation

The repository-provided `integration/Dockerfile` still starts from Python 3.11
although `pyproject.toml` requires Python 3.12 or newer.  Its build therefore
fails before testing.  This infrastructure-owned defect is outside this
application ticket; equivalent matrix validation passed in a one-shot
`python:3.12-slim` container.
