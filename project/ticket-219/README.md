# Ticket 219: Respect Koru admission and propagate publication failures

- **ID**: ticket-219
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-31
- **maxActiveMinutes**: 60

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested investigation, implementation, tests and protected merges for publication through Goal. Keep this bounded repair in the existing ticket; the fleet migration and scheduler are separate dependent work.

Goal previously invoked mutating Koru repair before admission, including during dry runs, and continued after repair failure. Admit first, keep preview and merged release checkouts read-only, recheck the repaired checkout, and abort on repair failure. The standalone publish command must also raise a nonzero Click error when its upload transport fails, including after a failed Makefile fallback.

Scope is exactly the three implementation files and their three regression modules declared in intent.json. No dependency manifest, version, registry configuration or protected policy changes.

During delivery, governed bootstrap tried to install the optional costs package despite disabling badges. Skip its probe/install only when both governed read-only mode and badge opt-out are active; ordinary tracking bootstrap keeps its existing behavior.

## Acceptance criteria

- [x] AC-01: Explicit and context dry runs never invoke mutating Koru repair.
- [x] AC-02: Admission precedes repair; read-only release checkouts refuse it, repaired state is rechecked, and repair/upload failures stop the workflow.
- [ ] AC-03: Affected regressions and governance pass; exact-head protected verification and independent Validator complete publication.

## Ownership and validation

The native allocator reserved ticket-219. The published Worktrees v5 planner and filesystem validator established the canonical relative checkout. The existing local-single-clone ChangeLeaseStore granted source editing through acquire and begin-edit CAS, refreshed after the bounded intent amendment. The managed work-start report returns REUSE_EXISTING. Source ownership is separate from independent merge approval.

Fifteen focused regressions and 174 affected tests passed. Testless collected coverage and generated advisory plans; the managed gate passed with zero errors and warnings. External evidence uses receipt:goal-publication-audit/refactor-20261031. The earlier isolated fake-Koru and failed-upload probes established the defects without real repair or upload.

## Delivery boundary

Publish the ticket branch and PR through Goal and require the protected local OneDev profile and independent Validator. Preserve all unrelated checkouts and changes. No package upload or live runtime activation is implied by source tests or a merge.
