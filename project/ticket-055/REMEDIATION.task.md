# Refactoring task RI-GOAL-PR-RESUME-BOUNDARY

Ticket: ticket-055
Repository: semcod/goal
Intent-Digest: e014ecda829f580300a76714916d2968d7b63f0b57a769b5ffaf0f115f74da1a

## Outcome

Governed pull-request resume publishes the already reviewed ticket HEAD without mutating unrelated files or depending on a free local canonical branch name.

## Required changes

### A-RESUME-BOUNDARY

[A-RESUME-BOUNDARY] Implement Move exact committed-candidate classification ahead of bootstrap and isolate Goal-owned badge mutation in pull-request mode. Findings: F-RESUME-MUTATION/GOAL_PR_RESUME_MUTATES_WORKTREE/P1. Paths: `goal/push/core.py`. Acceptance: [AC-01] Committed-candidate resume and ordinary pull-request preparation cannot create an unrelated badge change or bypass post-bootstrap governance.

### A-REMOTE-REFSPEC

[A-REMOTE-REFSPEC] Implement Replace local canonical branch creation with a non-forced explicit HEAD-to-remote refspec. Findings: F-LOCAL-BRANCH-COLLISION/GOAL_PR_LOCAL_BRANCH_COLLISION/P1. Paths: `goal/governance/delivery.py`. Acceptance: [AC-02] Canonical remote PR publication succeeds without modifying a colliding local branch and without using force.

### A-REGRESSION-COVERAGE

[A-REGRESSION-COVERAGE] Implement Add regression coverage for ordering, badge isolation, candidate revalidation, local alias preservation and explicit remote ref publication. Findings: F-RESUME-MUTATION/GOAL_PR_RESUME_MUTATES_WORKTREE/P1, F-LOCAL-BRANCH-COLLISION/GOAL_PR_LOCAL_BRANCH_COLLISION/P1. Paths: `tests/test_delivery_integrity.py`, `tests/test_governance_delivery.py`. Acceptance: [AC-01] Committed-candidate resume and ordinary pull-request preparation cannot create an unrelated badge change or bypass post-bootstrap governance.; [AC-02] Canonical remote PR publication succeeds without modifying a colliding local branch and without using force.

## Constraints

- Keep the repair within two internal delivery components and four implementation/test files.
- Preserve README.md, dependency carriers and every human-owned ticket file.
- Use a non-forced explicit remote refspec for the canonical PR head.

## Non-goals

- Do not weaken exact-ticket, clean-tree, ancestry or post-test revalidation checks.
- Do not delete, reset or overwrite local branches or worktrees.
- Do not change version, release, registry, direct-main or publish-only behavior.
