# Ticket 239: Bind frozen source PR heads and isolate update test state

- **ID**: ticket-239
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-12

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested continued investigation,
repairs and protected merging. This is STARTER-031, the corrective follow-up
to independently merged Goal PR242 and prerequisite of standard NP-048.
Keep the immutable prepared candidate bound through PR lookup, creation and
readback. Isolate the first-run self-update test from its inherited reexec
marker without changing the production loop guard.

Only the three source/test paths in intent.json are owned. The primary
checkout's unrelated .planfile/config.yaml is preserved. No standard430/429,
dependency, version, runtime activation or protected policy changes are in scope.

The implementation/publication session is bounded to60 active minutes from
the new controller admission, with no extensions and checkpoints at material
boundaries. A deterministic unchanged failure is handed off, not repeated.

## Acceptance criteria

- [x] AC-01: Real local-Git regressions reject mutations after post-push
  validation, after PR lookup and during creation/readback, preserving existing
  PR recovery and default local behavior.
- [x] AC-02: The first-run self-update test passes with an inherited marker;
  the production reexec-loop prevention remains intact.
- [ ] AC-03: Focused and full tests, managed governance and stack checks pass;
  the exact frozen head is independently verified and merged by the declared
  protected OneDev/Validator process.

## Validation evidence

Before the repair, the three later-window Git races and inherited-marker test
fail4/4 on the accepted base. The same four pass after the repair. The broader
source-review, source-hub, delivery and CLI selection passes169tests, including
the additional REST-recovery mutation. Candidate JSON/governance reports
0errors/0warnings and Docker Compose configuration validates. These are local
results. The full candidate suite passes1307tests with2skipped; the managed
gate passes0errors/0warnings and Docker Compose validates. The remaining
publication step must independently verify and merge the exact frozen head.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
