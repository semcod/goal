# Ticket 013: Adopt governance ownership extensions

- **ID**: ticket-013
- **Owner**: session user (identity unresolved)
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10
- **Work classification**: `SERVICE / governance`

## Goal and scope

Upgrade Goal's immutable `wellmanifest/new-project` adoption from published
0.11.0 to published 0.14.1 and install target-local ownership for
`integration/**` and Python lockfiles.  This unlocks ticket 012 without
weakening path enforcement or editing managed files outside the adoption tool.

## Acceptance criteria

- [x] AC-01: The user's dependency/runtime update request authorizes the
  necessary governance adoption identified by the deterministic gate.
- [x] AC-02: Adoption uses the published full SHA behind `v0.14.1`.
- [x] AC-03: Managed-file provenance and governance validation pass after the
  upgrade.
- [x] AC-04: The integration workstream explicitly owns `integration/**` and
  Python lockfiles while all existing owned paths remain intact.
- [x] AC-05: Ticket 012 can claim its final implementation paths.

## Validation evidence

- `goal governance adopt --standard-repository ... --source-revision
  63a3d56b648da0d338be7cf28cbf9045adbb3e5e --check`: PASS; immutable
  adoption is up to date.
- The v0.14.1 gate with accepted base
  `9ef73d2ce297b134da66caceb6d9b3c10741d2f1`: PASS; 0 errors, 0 warnings.
- Atomic adoption verified every changed managed path against both the legacy
  v0.11 lock and v0.14.1 lock; no budget or ownership bypass was used.
- Target manifest retains all existing workstreams and adds `integration/**`,
  `uv.lock`, `poetry.lock` and `Pipfile.lock` to integration ownership.
- Required Python 3.12 Dockerfile and network-isolated Compose declarations
  were published first in PRs #21 and #22.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Dependency and approval

The user's instruction to update, test and publish covers this prerequisite.
Ticket 014 disproved the Goal-adapter hypothesis. The upstream repair is now
published immutably as
`63a3d56b648da0d338be7cf28cbf9045adbb3e5e` (`v0.14.1`), whose annotated tag
and GitHub Release were verified. The user's autonomous execution request
authorizes resumption inside this unchanged adoption scope without another
confirmation; external exact-head merge approval remains separate.

## Boundary

Only standard-managed governance artifacts, the target-owned manifest
extension, and this ticket's governance evidence may change.  The adoption
must be executed through `goal governance adopt`; no integrity check is
disabled or bypassed.

The base planning intent remains `new-project.intent/v2` while the target runs
the v0.11 checker. This adoption transaction upgrades the checker, schema and
intent to v3 in one validated change, avoiding a mixed-schema delivery gap.

## Publication

- Governed delivery produced [PR #23](https://github.com/semcod/goal/pull/23).
- Target CI passed on Python 3.12 and 3.13.
- `ifuri-validator-agent` approved exact head
  `a3e493a145c5d7257daddcc6aa7aac624f682305`.
- The protected PR merged as
  `c1f1305dc71efc7aac1a5bc6b05d3cd8b55275d3`.
