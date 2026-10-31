# Ticket 220: Reusable exact registry publication observations

- **ID**: ticket-220
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 60

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested autonomous investigation, implementation, tests and independent protected merges for Goal publication and periodic reconciliation. This is the bounded shared read-only registry observation slice, preceding integration and scheduler changes.

Add typed exact-release observations for explicitly supported PyPI and TestPyPI targets. Distinguish authoritative 404 from inaccessible, throttled, malformed, mismatched or empty responses. Preserve Retry-After and compare expected artifact hashes before reporting verified. A JSON module entrypoint permits integrations to reuse the result without copying HTTP logic. Existing exact_version_published remains a boolean compatibility adapter.

## Acceptance criteria

- [x] AC-01: Exact targets, malformed/error responses, retry metadata and artifact verification pass meaningful regression tests; observation performs no upload, repair or Git mutation.
- [ ] AC-02: Compatibility tests and governance pass; source publication uses exact-head OneDev and the independent Validator.

## Delivery boundary

No version or dependency changes, upload, service activation or broad migration. Publish only the ticket branch and PR using Goal commit-only flags. Source merge is separate from package publication and fleet adoption. Keep unrelated and legacy checkouts untouched.

Native allocation, published Worktrees v5 filesystem validation and the existing single-clone ChangeLeaseStore established this canonical relative delivery checkout and source editing grant. 81 affected tests passed with one existing skip; the new observer also verified both Goal 2.2.5 and Heyasa 0.4.1 against their published artifact hashes. Independent merge remains required.
