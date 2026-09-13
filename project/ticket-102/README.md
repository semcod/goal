# ticket-102: Preserve canonical ticket branches during PR publication

- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Workstream**: application
- **GitHub Issue**: https://github.com/semcod/goal/issues/140
- **Created**: 2026-09-13

SESSION_EXECUTION_AUTHORIZATION: The user requested continued fixes, durable branch/worktree/Issue/PR registration and protected publication. This bounded application repair is disjoint from active bootstrap ticket-100 and integration ticket-101. Allocation used the unchanged adopted allocator after a scoped read-only observation returned NEW_TICKET_CANDIDATE with no blockers. The source observation grants no write or merge authority.

## Acceptance criteria

- AC-01: New canonical ticket branches retain their remote name; a conflicting ticket binding fails before push. An existing legacy Goal PR is resumed without a duplicate; ambiguous or failed observations do not publish. Existing noncanonical and detached behavior stays compatible.
- AC-02: Regression tests, exact-base/head governance and protected CI pass; independent Validator approves before merge. Local tracking links and the terminal lease are reconciled from the actual outcome.

This is a product prerequisite for wellmanifest/new-project#330, not completion of mandatory Planfile installation or fleet enforcement.

Project-owned Planfile: `semcod/goal::PLF-001`, linked to Issue #140 and this exact branch/worktree/lease. The pilot runtime is isolated under the primary checkout and pinned to Planfile revision 31aaab644486400237ce8ffbfe6a01a9b02fb095; this does not change application dependencies.

Validation: 12 new regression cases failed on the original implementation. After the fix, all 50 publication tests passed; the full suite passed 758 tests with two skips. Scoped Ruff and governance passed. Protected CI and independent exact-head publication remain required.
