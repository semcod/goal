# Ticket 242: Accept unambiguous merge commit ticket suffixes

- **ID**: ticket-242
- **Owner**: agent:codex / codex-goal-merge-binding-20261116t1341z
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-16

## Goal and scope

Resume protected publication of an existing ticket branch whose history contains
a real synchronization merge named `chore(merge): sync current origin/main
(ticket-666)`. Goal currently rejects its trailing ticket reference even though
the merge is bound to the same ticket. Preserve the strict binding of ordinary
commits and require Git to confirm multiple parents before accepting this exact
legacy synchronization format.

SESSION_EXECUTION_AUTHORIZATION: the user requested continued repairs and
independent merges. This bounded prerequisite restores the declared Goal
publication route for Heyasa PR #799. It authorizes implementation, regression
tests and a request for protected publication; it is not trusted review approval.

## Acceptance criteria

- [x] AC-01: A real synchronization merge with one exact trailing ticket resumes
  publication; a normal commit with the same subject remains rejected.
- [x] AC-02: Missing, longer, conflicting and misplaced ticket references remain
  rejected; existing prefix and Conventional Commit scope bindings still pass.
- [ ] AC-03: The complete delivery regression module and governance pass, followed
  by exact-head/current-base required CI and independent Validator publication.

The native controller allocated this canonical checkout. The change owns only
the delivery parser and its existing regression module. It does not modify the
separate standard adoption, example versions, writer leases or protected checks.

Baseline controls reproduced two rejected valid merges with ten negative cases
passing. After implementation, the complete delivery module passed all 112 tests
through the independently pinned full Wellman runtime. Raw logs remain outside
the tracked ticket; required CI and independent publication remain pending.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

<!-- ticket-radar:start -->
## Ticket Radar

Assessment unavailable: managed ticket storage bridge declined the radar assessment.
Advisory only; no execution or merge approval.
<!-- ticket-radar:end -->
