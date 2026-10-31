# Ticket 225: Reconcile published Python content with exact source

- **ID**: ticket-225
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 90

SESSION_EXECUTION_AUTHORIZATION: the user requested publication repairs, tests and protected merges. Verified PyPI Heyasa 0.4.1 corresponds to source 8c36d972203ac88f28248eee321b12c89944356c; clean current main changes ten package paths but the observer reports version_present_or_not_newer and pending=false. Reuse a common bounded Goal source comparison and separate reconciliation eligibility. Keep immutable existing-version uploads ineligible. Packaging ticket-224 is independently merged at the accepted base; its 2.2.7 has not been uploaded, so this material application repair joins that version without a release-only branch or changing the reviewed dependency inputs.

- [x] AC-01: Opt-in JSON comparison binds supported clean source and verified public Python content; divergence, uncertainty, bounds and retries are explicit and existing missing-version behavior remains unchanged.
- [ ] AC-02: Focused Testless, actual Goal delivery and managed checks pass.
- [ ] AC-03: Exact-head/current-base OneDev and independent Validator accept source.
- [ ] AC-04: Goal publishes accepted 2.2.7, registry wheel/sdist source and hashes match Git, and installed pip-less and source-divergence canaries pass.

Validation: 150 focused source/registry cases passed. A real read-only PyPI canary compared the public Heyasa 0.4.1 wheel (SHA-256 350763291f683d06a2cae375a123998fe3ea7f63a3e28cec508453d4a6b52725) with 52 tracked Python files at clean source 8bd80e0e4fdf2029a335650b59d7cc4d2dbc78a8. It reports divergence and reconciliation_required=true while pending, ready_for_goal, source_publication_verified and authorization remain false. Git source reads are batched and archive/source sizes bounded. Exact public artifact readback and packaged canaries remain pending independent source publication.
