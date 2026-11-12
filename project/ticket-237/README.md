# ticket-237: Stop owned source-hub processes after interruption

- **ID**: ticket-237
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-12

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user "kontynuuj,scalaj" continues the Heyasa
autonomy objective through semcod/goal:STARTER-029 / GitHub issue239.
This bounded prerequisite fixes Linux source-hub timeout/cancellation teardown.
Full validation also repairs checkout-bound fixture isolation in the same scope:
the missing-config test gets its own Git root, noncanonical checkout rejection
retains explicit system-temp classification coverage, and Python bootstrap
fixtures cannot discover and write the real source README.
It does not qualify or publish frozen NP429, extend its stopped stages, or close
the remaining baseline/candidate resource comparison in Goal239.

## Acceptance criteria

- [x] AC-01: Real timeout and interruption kill owned POSIX descendants,
  including TERM-ignoring children; partial output and real failures survive.
- [x] AC-02: All canonical commands, dirty-state checks, genuine success cache,
  unchanged-head reuse and cross-head invalidation retain their contracts.
- [ ] AC-03: Full checks and exact-head OneDev/independent Validator publication.

## Boundaries

No foreign process termination, timeout increase, bypass publication,
managed-standard edits, runtime activation or version/registry changes.
Raw results and controller fencing receipts stay in ignored private storage.

## Validation

Full admitted suite: 1281 passed, 2 skipped; native governance: 0 errors and
0 warnings. All dirty snapshot bytes and Git state remain unchanged through
the full run. Differential Ruff introduces no findings. Two original process
regressions and the guarded bootstrap-write diagnostic reproduce the defects.
Timeout, KeyboardInterrupt and main-thread default SIGTERM cancellation are
covered. Independent exact-head OneDev/Validator publication is pending.
