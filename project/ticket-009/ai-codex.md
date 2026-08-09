---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-009
---
# Participant: codex (AI agent)

## Understanding

Goal treated every non-empty root `VERSION` as release metadata.  In the
bioxfoundry corpus that file is a multi-line integrity contract, so a `goal -a`
run replaced it with `0.0.1`.  The same run exposed a second issue: the push
transaction carried the explicitly selected `direct-main` mode, while the hook
resolved the configured default `pull-request` mode and rejected the valid
transaction despite `direct-main` being in `allowedModes`.

## Execution plan

1. Distinguish plain semver-like values from multi-line contract manifests.
2. Preserve contract files during discovery and synchronization.
3. Use a plain commit for repositories without a registry project type.
4. Validate hook transactions against the allowed mode set and configured
   remote.
5. Run focused and full suites, governance validation, then publish with the
   governed `goal -a` path.

## Actual changes

- Added a shared plain-version predicate and applied it to root-version reads
  and synchronization.
- Excluded multi-line contracts from automatic release-file detection.
- Made no-registry repositories skip synthetic release machinery while still
  committing their changes.
- Corrected hook authorization for an explicit allowed delivery mode.
- Added regression coverage for all four behaviors.

## Blockers

- Final governance validation and publication remain to be completed.
