# Ticket 223: Bootstrap publication tools in pip-less UV environments

- **ID**: ticket-223
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 45

SESSION_EXECUTION_AUTHORIZATION: user requested immediate publication/Goal repairs, tests and protected merges across the workspace. A real Goal 2.2.6 helper probe against Heyasa ticket-226's freshly locked UV environment found no pip/build/twine; preparation returned failure (`No module named pip`) before any upload. Fix the shared tool boundary instead of adding project-specific installer workarounds.

- [x] AC-01: UV targets the exact interpreter for missing tools, pip compatibility is bounded, failures/timeouts abort, successful installs are rechecked and diagnostics do not expose installer credentials; source locks stay unchanged.
- [ ] AC-02: Affected tests, managed checks, exact-head/current-base CI and independent source merge pass.
- [ ] AC-03: The packaged accepted source passes a real pip-less bootstrap canary; publication and package projections remain owned by material packaging integration.

Evidence: `receipt:goal/pipless-publisher-probe`. Only the shared publisher and its existing regression module are implementation paths. Preserve admission, source ownership and independent upload/merge boundaries.

The real pip-less canary installed build and twine through UV into an isolated exact interpreter while pip remained absent; no upload was attempted. This qualifies the local implementation, not its independent publication. Raw target/probe receipt is external.
