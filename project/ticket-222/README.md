# Ticket 222: Repair governed Koru workflow and unpublished release discovery

- **ID**: ticket-222
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 120

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested autonomous investigation, immediate repairs, tests and protected merges for goal -a publication and goal -k repair across the workspace. Goal PR224 is independently merged; its installed observer will ship with these material fixes in the already integrated 2.2.6.

A safe disposable probe reproduced bare goal -k rejecting a governed repository before repair because the full-workflow flag was absent. Batch currently drops parent flags and ignores every clean repository. Its Git detection also excludes linked worktrees. Core publication readiness conflates unavailable latest metadata with first publication. Read-only bootstrap assumes pip exists even in the supported pip-less UV environment.

Keep all existing source admission, repair refusal on read-only release roots, dry-run and independent publication boundaries. Add a read-only project plan through the existing observer, using exact package/registry/version and source observations. Include clean pending public-PyPI releases in batch only when they are suitable for the protected workflow. Preserve --no-publish and Koru flags in child calls. Authoritative absence can request the committed initial version; unknown network/auth/rate observations cannot. The plan is diagnostic and grants no writer or merge authority. UV pip installs declared dependencies into the exact environment without sync/lock mutation.

## Acceptance criteria

- [x] AC-01: Koru workflow aliases select the complete governed workflow, preserve effect-limiting flags and never repair during previews or without admission.
- [x] AC-02: Read-only source/registry plans distinguish missing from unknown, batch selects clean configured pending releases, and an initial merged release does not create a version/source commit.
- [x] AC-03: Read-only bootstrap handles pip-less UV environments, preserves locks, and retains a bounded pip fallback.
- [ ] AC-04: Affected tests, governance, protected verification and independent merge pass, then Goal publishes the accepted 2.2.6 package with exact artifact readback.

## Delivery boundary

Ten declared implementation/test files in four components; no dependency or version changes. Do not claim an artifact is published from process success or an old dist directory. Registry-independent source/build artifact receipts, downstream queue adoption, Heyasa scheduling and owner-scoped fleet migration remain subsequent slices. Do not normalize or delete unrelated worktrees.

## Verification evidence

Testless scoped run: 222 tests passed; the final single-registry guard adds one case. Isolated Python 3.13 wheel installation: four tests passed with three artifact/network subtests. Governance passed with zero findings. The shared plan never grants authority, skips private/multiple registry workflows, and reports unknown registry state without creating another ticket. Source acceptance and actual 2.2.6 upload remain pending. External receipts: `receipt:goal222/readmodel-release-tests`, `receipt:goal222/bootstrap-tests`, `receipt:goal222/routing-tests`.
