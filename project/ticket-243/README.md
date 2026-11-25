# Ticket 243: Resolve setuptools dynamic version file in publication observer

- **ID**: ticket-243
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-25

## Goal and scope

Support `project.dynamic = ["version"]` paired with static
`[tool.setuptools.dynamic].version.file` in `goal.publish.state.plan_current_project`
(fixing `heyasa/heyasa#1177` / `PLF-29889`) so `goal-publication-status --verify-source`
resolves the package version instead of failing with
`unsupported_or_missing_package_metadata`.

SESSION_EXECUTION_AUTHORIZATION: The user requested continued repairs and
independent merges (`napraiwaj,sclaja`). This ticket authorizes implementation,
regression tests, and requesting protected CI / independent Validator
publication; it is not trusted review or merge approval.

## Acceptance criteria

- [x] AC-01: `plan_current_project` resolves safe, bounded relative
  `tool.setuptools.dynamic.version.file` strings and single-item lists for
  `setuptools.build_meta` projects with `dynamic = ["version"]`.
- [x] AC-02: Version consistency checks (`version_sources_disagree`) and
  `--verify-source` artifact comparisons remain enforced; unsafe paths,
  symlinks, `attr` providers, non-setuptools backends, missing/empty/multiline
  version files, and conflicting static+dynamic declarations fail closed with
  `unsupported_or_missing_package_metadata`.
- [x] AC-03: Targeted tests, `.github/tests`, repository governance, required
  CI, and independent Validator publication pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
