# Ticket 017: Assign release metadata to integration

- **ID**: ticket-017
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-10

## Goal and scope

Extend Goal's target-owned integration workstream with the exact release
metadata paths updated atomically by `goal -a`: `VERSION`, `CHANGELOG.md`,
`README.md`, and `goal/__init__.py`. The integration workstream already owns
`pyproject.toml` and `uv.lock`; without the remaining paths, a valid version
sync is rejected as a cross-workstream diff.

## Acceptance criteria

- [x] AC-01: The user's autonomous test/publish request authorizes this narrow
  prerequisite without another confirmation.
- [x] AC-02: Integration ownership includes the four missing release metadata
  paths and preserves all existing ownership.
- [x] AC-03: Ticket 012 can validate one atomic Goal version-sync diff without
  a workstream ownership violation.
- [x] AC-04: Managed provenance and governance validation pass with zero
  findings.

## Validation evidence

- Target manifest assertion confirms integration owns `VERSION`,
  `CHANGELOG.md`, `README.md`, `goal/__init__.py`, `pyproject.toml`, and
  `uv.lock`; all pre-existing entries remain present.
- `./project/governance-check.sh --base
  1443cdff4364187554ebcf9b03628096b09f31e5`: PASS; 0 errors, 0 warnings.
- The change is limited to four additions in the extendable target manifest;
  standard-managed base and lock provenance are unchanged.

## Session authorization

This is a direct prerequisite of the already authorized ticket-012 publication
outcome. The agent may proceed in `EDIT`; exact-head merge approval remains an
independent protected action.

## Boundary

Only the target-owned manifest extension and ticket evidence may change. This
ticket does not edit source, version values, dependency manifests, lockfiles,
standard-managed base content, or GitHub policy.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Publication

- Governed delivery produced [PR #29](https://github.com/semcod/goal/pull/29).
- CI passed on Python 3.12 and 3.13.
- `ifuri-validator-agent` approved exact head
  `80417cddeb2549713e895497e3e9c5de094d11c0`.
- The protected PR merged as
  `cd1d8bafea301ffdac21f06bc5f547fd79aee3cd`.
