# Agent decisions within an authorized task

This guidance composes session authorization, ticket ownership and workspace
observation. It grants no new Git, deployment, credential or cleanup authority.

## Decide from the requested effect

1. Recover the current request, recorded intent and existing session authority.
   An instruction to execute remains valid for the same outcome across turns;
   do not ask again merely because a phase, tool or checkout changed. A new
   request to improve policy does not approve a previously proposed deletion.
2. Identify the next concrete effect, its owner, target and reversibility. Read
   the applicable rule and its activation condition. A warning about a possible
   destructive operation does not require choosing that operation.
3. Inspect current evidence before interpreting a failure: exact command and
   diagnostic, Git identity and ancestry, actual dirty paths, active ticket,
   protected receipts and, when relevant, active processes and leases.
4. Prefer a bounded route already authorized that preserves unknown work.
   Continue disjoint implementation, tests and read-only diagnosis while a
   dependent effect waits. Keep the original requested outcome active.
5. Ask only when necessary information or authority is still missing. Before
   asking, finish the independent preparation so the choice is reviewable.
   State the exact operation and target, evidence inspected, expected effect,
   preservation or recovery plan, and the rule requiring a new decision.
   Silence, elapsed time, a suggested answer and a diagnostic are not approval.

| Observation | Decision |
| --- | --- |
| Same authorized scope, routine reversible fix and required tests | Proceed within the ticket. |
| Protected delivery is part of the authorized outcome | Invoke the declared validator/controller; its trusted evidence still governs merge/apply. |
| Detached snapshot shares the writer's HEAD and has no competing source delta | Preserve it; common history alone is not a second writer. |
| Real competing dirty changes or active overlapping intent | Stop the affected write and resolve ownership; keep disjoint work progressing. |
| Missing or contradictory evidence | Report uncertainty, gather bounded observations; do not infer permission. |
| CI capacity, credentials or another external prerequisite is unavailable | Persist the exact blocker and remaining stages; do not manufacture successful checks. |
| Removing, relocating or repairing unknown work is necessary | Audit and preserve it, then obtain authority for that exact operation unless already explicitly authorized. |

## Separate conflict evidence from cleanup authority

`wellmanifest/worktrees` classifies registrations and their permitted placement.
An `unknown`, legacy or quarantine classification is not proof of a competing
write and does not require cleanup to continue an unrelated canonical ticket.
It also never makes that registration publishable or disposable.

The overlap guard compares dirty changes with the peer's new contribution
since the pair's common ancestor. A shared implementation already present in
both HEADs is inherited context. Two actual dirty writers remain contested;
unresolved ancestry retains conservative checking. Intent ownership remains a
separate check even when Git can merge file contents.

`wellmanifest/git-lifecycle` still owns cleanup effects; `ticket-lifecycle`
owns reservations, and protected merge/publication controllers own external
effects. Fix an incorrect checker at its HOME with a failing regression and
adopt the verified revision. Do not disable a hook, edit a managed hash by
hand, add a blanket ignore, or delete evidence merely to make a gate green.

## Report the achieved stage

Distinguish source edited, tests passed, commit created, PR open, trusted merge,
deployment applied and public behavior verified. Each claim needs evidence
from that stage. A local preview, HTTP 200, an unchanged version number, or a
completed coding ticket alone cannot prove the requested production change.
When blocked, preserve the work and name the remaining dependent effect;
do not describe the overall task as completed.
