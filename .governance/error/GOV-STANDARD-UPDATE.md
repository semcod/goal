# GOV-STANDARD-UPDATE-001: pre-commit cannot safely prepare a standard update

## Situation

The managed hook found a pinned adoption but its controller is missing, Goal is
unavailable or incompatible, release verification failed, or Goal prepared or
refused an update and stopped the commit.

## Meaning

The committed pin remains authoritative. A newer release gains trust only when
Goal verifies its annotated tag, final GitHub Release, full SHA and generated
digests. Preparation does not stage, commit, merge or publish the result.

## Safe resolution

1. Preserve the worktree and read the Goal output above this code.
2. Install Goal with `governance adopt --latest --pre-commit` support.
3. Validate `.governance/standard-adoption.json`; when `executor` is
   `koru-goal`, install a compatible Koru supervisor as well.
4. Allocate or resume exactly one standard-adoption ticket in its own worktree.
5. Retry the commit, review the prepared diff, stage it explicitly and retry.

## Verification

- The Goal pre-commit adoption command returns zero when the verified release
  is already pinned.
- A prepared update remains visible and the original commit remains uncreated.
- Managed governance and standard conformance pass after explicit restaging.

## Do not

- Do not use `--no-verify`, delete the hook or weaken digest checks.
- Do not trust `main`, `latest`, a lightweight tag or unbound release metadata.
- Do not commit the prepared update from an unrelated feature ticket.

## Related rules

- `P-CORE-007`, `P-CORE-014`, `P-CORE-024`
- `GOV-SYNC-001`, `GOV-TICKET-001`
