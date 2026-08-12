# GOV-REMEDIATION-001/002/003 — invalid or inconsistent remediation intent

## Situation

`GOV-REMEDIATION-001` means the target-owned remediation intent is malformed or
semantically unsafe. `GOV-REMEDIATION-002` means a todo2code plan conflicts with
accepted scope, criteria, priority or preservation constraints.
`GOV-REMEDIATION-003` means the advisory overlay no longer matches the
authority-bearing intent digest.

## Meaning

The deterministic boundary cannot prove that the proposed refactoring still
implements the accepted diagnostic intent. LLM and todo2code output remains
advisory and cannot repair that authority gap by assertion.

## Safe resolution

1. Open the populated `remediation-intent.dsl.json` in the affected target
   repository ticket; do not copy it into the Governance Hub.
2. For `GOV-REMEDIATION-001`, resolve every reported field, path, dependency,
   applicability signal and verification, then validate again.
3. For `GOV-REMEDIATION-002`, reject or regenerate plans outside accepted scope.
   If the objective truly changed, record a fresh bounded intent and authority.
4. For `GOV-REMEDIATION-003`, discard the stale advisory overlay and rerun
   todo2code analysis against the current intent.
5. Keep unknown ownership explicit and preserve dirty worktrees or other user
   state until a human classifies them.

## Verification

Run `python3 .governance/remediation_intent.py validate <intent>` and require a
zero exit status. Regenerated analyzed intents must bind current intent,
diagnostics and plan digests and must contain no blocking todo2code finding
before implementation proceeds.

## Do not

Do not edit digests by hand, suppress applicability uncertainty, infer missing
owners, widen paths from an LLM suggestion, or authorize deletion merely to
make validation pass. Do not use a target ticket or incident log as a reusable
runbook.

## Related rules

`C-DIAGNOSTIC-001`, `C-DIAGNOSTIC-002`, `C-DIAGNOSTIC-003`,
`C-REMEDIATION-001`, `C-REMEDIATION-002`, `C-REMEDIATION-003`,
`C-REMEDIATION-004`, `P-CORE-008`, `P-CORE-020`.
