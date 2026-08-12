---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-050
---
# Participant: codex (AI agent)

## Understanding

The public Goal 2.1.297 correctly identifies its version but predates the
ticket-048 artifactless GitHub Release implementation already present on clean
main. This left `new-project v0.16.1` with a correct immutable annotated tag but
no final Release. A separate integration release must expose the already merged
repair before that downstream publication can be truthfully completed.

## Execution plan

1. Commit this bounded release plan before changing version carriers.
2. Use Goal's governed pull-request mode to synchronize the five established
   carriers to 2.1.298 without registry, tag or Release effects.
3. Run full tests, scoped Ruff, governance, package and Docker validation; then
   require hosted CI and exact-head Validator App approval.
4. Merge only the approved head, retest a clean checkout and publish immutable
   PyPI, annotated tag and final GitHub Release evidence from that merge.
5. Install 2.1.298 from the public index in isolation and use it to repair the
   missing `new-project v0.16.1` Release without moving its tag or main.
6. Close ticket evidence through a separate governed PR and remove temporary
   branches, worktrees, artifacts, images and environments after reachability
   proof.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.
- Allocated ticket-050 after the independently active ticket-049; the allocator
  honored the shared high-water mark across worktrees.
- Confirmed PyPI, tag and Release namespaces for 2.1.298 are unused.
- Confirmed public 2.1.297 lacks the ticket-048 code while clean main includes
  it, reproducing the release-ordering cause of the downstream failure.
- Refreshed the accepted base after ticket-049 merged independently; retained
  both ticket indexes while keeping ticket-049 source outside this ticket's
  diff.
- Synchronized only the five declared release carriers to 2.1.298 and entered
  `PUBLICATION` for Goal-owned test, commit and pull-request delivery.

## Blockers

- None within the bounded release. Trusted exact-head merge approval remains an
  external protected-boundary decision.
