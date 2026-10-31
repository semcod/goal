# Ticket 224: Package reusable Python publication tools as an optional extra

- **ID**: ticket-224
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 60

SESSION_EXECUTION_AUTHORIZATION: user requested reuse of Goal publication, immediate repairs, testing and protected merges. The pip-less publication defect is qualified and repaired in application ticket-223 / PR226. Provide the common optional goal[publish] bundle so downstream projects declare one publication toolchain rather than their own build/twine orchestration. Extend the existing isolated built-wheel test to verify the packaging contract and join the 2.2.7 projections to this material integration.

- [x] AC-01: The built wheel declares build/twine under publish without making them base dependencies; installed observer behavior and all version/lock projections remain consistent.
- [ ] AC-02: Required tests, governance and independent exact-head/current-base source validation pass.
- [ ] AC-03: After both source slices are independently merged, Goal publishes accepted 2.2.7; exact registry artifacts/sources and the installed pip-less canary are verified.

Five declared integration files only. Preserve every existing locked dependency version and runtime requirement. No registry/source-publication authority is inferred from local tests or the package metadata input approval.

Application ticket-223 is independently merged at the declared accepted base; its exact source reservation was released before integration acquisition.

Testless passed 88 affected tests and 3 subtests; the actual installed-wheel command matrix passed five tests. Lock comparison proves every non-root package record unchanged and only the Goal root version advances. Required profile inputs remain independently reviewed under OneDev ticket-781 before package publication.
