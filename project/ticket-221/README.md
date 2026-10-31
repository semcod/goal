# Ticket 221: Install reusable publication status command

- **ID**: ticket-221
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 90

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested implementation, tests and protected merges for publication through Goal, followed by actual package publication. This material integration makes the already merged observer available to Dockuri and Heyasa as an installed command.

Register goal-publication-status to the existing goal.publish.state:main. Add a disposable-wheel installation test that invokes the actual command from an empty directory, observes JSON failure/argument behavior and verifies that no project bootstrap or source mutation occurs. Match the setuptools requirement to existing PEP 639 metadata and declare the same backend for offline development builds. Reconcile the existing lockfile root version and add only this development/build dependency. Runtime dependencies remain unchanged. Ship this command as Goal 2.2.6; version projections belong to this material integration ticket.

## Acceptance criteria

- [x] AC-01: A freshly built/installed wheel exposes the JSON observer and fails invalid input without project bootstrap or ambient imports.
- [x] AC-02: Managed version projections and lockfile agree; declared backend supports the existing license metadata; runtime dependencies are unchanged.
- [ ] AC-03: Affected tests and governance pass; OneDev verifies the exact source head and the independent Validator approves and merges.
- [ ] AC-04: Goal publishes the merged release; PyPI artifact digests and installed command are read back.

## Delivery boundary

Use the native allocator, canonical relative worktree and actual source editing lease. Keep independent approval separate from source ownership. Publish this source through Goal commit-only delivery, then use goal -a on the verified merged clean base for package publication. Preserve unrelated legacy or dirty checkouts.

The published Worktrees v5 planner and filesystem check passed. Source ownership was acquired through the existing single-clone controller CAS and fencing. Testless passed 85 tests with one existing skip and three verification subtests. The lock changed only the Goal root version and added setuptools 84.2.1 / wheel 0.48.0 for development; all existing runtime package versions were preserved. Managed governance passed. The existing setuptools>=77 build floor is retained.
