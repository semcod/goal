# ticket-236: Installed test contracts and Goal2.2.11

- **ID**: ticket-236
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-05

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: continue maskservice:PLF-22282 after the
independently merged and locally deployed test-selection and cold UV repairs.
Release these accepted behaviors as Goal2.2.11, with a material contract that
runs from an isolated installed wheel. Keep all non-root dependency lock
records. Coordinate exact OneDev inputs through its own governed producer
and safe deployment before relying on current-base checks.

## Acceptance criteria

- [x] AC-01: Actual installed wheel distinguishes empty/explicitly skipped
  tests, ignores stale JUnit metrics, preserves failure status and loads a
  required local plugin with the generated cold module invocation.
- [x] AC-02: Four release versions agree, non-root lock records are identical;
  installed qualification, full regressions and managed governance pass.
- [ ] AC-03: Exact verifier inputs are independently accepted/deployed and all
  current-head/base checks plus trusted Validator approval precede source merge.
- [ ] AC-04: Genuine Goal publishes the accepted immutable version only after
  source merge; registry wheel/readback matches accepted source and local CLI
  is updated with the prior prefix retained.

## Boundaries

No application implementation changes, new runtime dependencies, gate bypass,
unreviewed pin changes, registry overwrite or pre-merge package upload.

## Validation and pending publication

Actual isolated wheel qualification: 10 tests passed, including required local
plugin execution through real offline UV and truthful unexecuted statuses.
Full source suite: 1274 passed, 2 existing skips; managed governance passed.
All 143 non-root lock records and dependency metadata are unchanged.
Differential lint has no introduced findings. The verified public2.2.10 wheel
still reproduces both defects, including old37sJUnit metrics with no tests.

Exact new input pins and safe OneDev deployment are tracked by
maskservice:PLF-22285. Current onedev-agent ticket-854 owns the configuration;
no competing infra source or deployment effect has been performed. The Goal
PR provides immutable candidate inputs for independent qualification. Source
merge and registry publication remain blocked until all protected checks and
independent approval bind the final candidate and qualified live profile.
