# Ticket 087: Preserve virtualenv isolation during package publication

- **ID**: ticket-087
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-06

## Authorization and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested continuing repairs and publishing all changes to GitHub through Goal. Repair the interpreter selection exposed by the redeploy 0.2.80 publication attempt. A symlink resolution selected uv-managed base Python and caused an externally-managed-environment failure.

## Acceptance criteria

- [x] AC-01: Active and local virtualenv selection preserve real subprocess isolation, including installed modules.
- [ ] AC-02: Focused/full tests, governance and Docker validation pass; protected exact-head review merges the source repair.

## Validation

Before the fix: four real virtualenv isolation cases fail; fallback passes. After the fix: 723 tests pass, 2 skip. Managed governance reports zero errors or warnings. Docker engine and Compose configuration pass. New tests pass full Ruff; changed source passes the CI fatal-error selection. Existing broad Ruff findings in publish.py are outside this repair. Exact-head protected publication remains pending.
