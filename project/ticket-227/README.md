# Ticket 227: Stabilize wheel fixtures that gate publication

- **ID**: ticket-227
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-01
- **maxActiveMinutes**: 60

SESSION_EXECUTION_AUTHORIZATION: the user requested immediate publication repairs, testing and protected merges. The accepted source ticket-225 is integrated history. Its first release attempt correctly stopped before upload because a fixture generated two ZIP archives on opposite sides of a timestamp boundary; the artifact hash consequently changed and the strict commit-race assertion failed. Preserve that assertion and fix the fixture clock dependence in this single test file. The existing diagnostic owner incident is linked by receipt:goal227/flaky-wheel-fix. Preserve the unknown primary Planfile changes and unrelated ticket-226; publish from the existing supported clean canonical checkout mode.

- [x] AC-01: Wheel fixture bytes remain stable across clock changes, while the original strict race/integrity checks remain enforced.
- [ ] AC-02: Affected Testless, actual Goal and managed checks pass.
- [ ] AC-03: Exact-head/current-base OneDev and independent Validator accept the material fix.
- [ ] AC-04: Goal publishes the held accepted 2.2.7, verifies both public artifacts against Git, and qualifies installed tool/source canaries.

Qualified regression: forcing two distinct clock dates makes the original archive factory fail byte equality. With explicit constant ZIP entry timestamps, all 72 affected source-integrity cases pass under Testless. The existing strict commit-race assertion is unchanged; no production code, packaging input, version or dependency is modified.
