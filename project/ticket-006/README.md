# Ticket 006: Adopt immutable new-project 0.11.0

- **ID**: ticket-006
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-05

## Goal and scope

Upgrade Goal's governance package from immutable new-project 0.9.0 to the
published 0.11.0 release SHA
`cc9b04673bbd85cb4e35fb683d288ef34be1485f`. Preserve Goal's repository-specific
workstreams and optional-Docker setting, while installing the canonical work
classification DSL and current approval-evidence contract.

This ticket changes governance artifacts only. Mapping Goal's measured
complexity deltas into `BUG/regression` and `SERVICE/health` remains a separate
application ticket after adoption.

## Acceptance criteria

- [x] AC-01: Scope and immutable source SHA are approved by a human owner.
- [x] AC-02: The target manifest preserves Goal ownership and declares 0.11.0.
- [x] AC-03: Local Goal reports and applies only the reviewed immutable upgrade.
- [x] AC-04: The resulting lock binds 0.11.0, published status, full SHA and
  managed classification DSL/schema files.
- [x] AC-05: Governance and focused Goal adoption tests pass; Docker remains
  optional as declared by the preserved target manifest.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Risk boundary

- The installed global `goal` executable lacks the governance command; this
  ticket uses the repository's verified `.venv/bin/goal` entry point.
- Cross-version adoption fails closed until the target manifest version is
  explicitly reviewed and advanced.
- The pre-existing `_validate_pfix_env` failure was repaired independently by
  ticket-007 before this branch was refreshed from `main`; this ticket does not
  contain that application change in its own diff.

## Session authorization

The user approved ticket-006 with the instruction to continue on 2026-08-05.
This authorizes implementation inside `intent.json`, not merge approval.

## Delivery evidence

- PR: `semcod/goal#16`.
- Approved head: `f3a8327bfaf780b0fe2e165da968ef2e7524983c`.
- Validator identity: `ifuri-validator-agent[bot]`.
- Merge commit: `8e859fc55df8905b5d731adf6a11e2d41c7fb6d2`.

## Validation evidence

- Repeated adoption check: up to date at immutable new-project 0.11.0 SHA.
- `./project/governance-check.sh`: PASS with zero errors and warnings.
- Focused governance/adoption and bootstrap tests: 76 passed.
- Full local suite after merging the ticket-007 baseline: 477 passed, 2 skipped,
  0 failed.
- `git diff --check`: PASS.
