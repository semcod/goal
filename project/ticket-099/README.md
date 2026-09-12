# Ticket 099: Adopt wellmanifest/new-project 0.20.25

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-12

SESSION_EXECUTION_AUTHORIZATION: adopt, test, push and protected merge, requested by the owner on 2026-09-12.

## Goal and scope

Goal pinned `0.20.16` (`6d2da011`). The current published release is `0.20.25`
(`d54878a1`), which fixes a defect affecting every adopter that runs Python
3.10: `scripts/agent_host_check.py` imported `tomllib` at module scope,
`governance_check.py` reported the resulting `ImportError` as a missing managed
validator (`GOV-SYNC-001`), and because `GOV-PACKAGING-003` binds the gate to
the test lifecycle, the session aborted.

Found and fixed while adopting the standard in `semcod/planfile`:
wellmanifest/new-project#325 (fix), #326 (release 0.20.25).

The adoption advances the managed governance files, the pre-commit hook,
`AGENTS.md`, `project/new-ticket.sh` and `scripts/runtime.sh`, and realigns the
`[tool.wellmanifest]` pin in `pyproject.toml` with the regenerated lock
(`GOV-PACKAGING-002` compares them). The manifest instance files are owned by
the `governance` workstream; `pyproject.toml` is covered by the standard
adoption's atomic packaging binding.

Out of scope: any change to Goal's own source, tests or released behaviour.

## Acceptance criteria

- [x] AC-01: `goal governance adopt --source-revision d54878a… --check` reports no drift.
- [x] AC-02: `./project/governance-check.sh --base origin/main --head HEAD --actor agent` passes.
- [x] AC-03: The existing test suite still passes (no source change).

## Validation evidence

- Immutable adoption check: `up-to-date wellmanifest/new-project 0.20.25` at
  `d54878a105a20d84dd554f205bc177dcacc8730a`.
- Governance gate: `GOV-PASS` with 0 errors and 0 warnings.
- Host contract check: active.
- Full suite: `743 passed, 2 skipped`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
