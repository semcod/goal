# TODO

## Governed architecture roadmap

- [ ] Deliver [ticket-060](project/ticket-060/README.md): align Goal's own
  tracked Python strategy with the retry-safe Twine contract while preserving
  Node and Rust publishers. State: `IN_PROGRESS / PUBLICATION`; 618 tests
  (2 skips), structural checks and governance pass; classification:
  `BUG / P1 / regression`; depends on ticket-059.

- [x] Deliver [ticket-059](project/ticket-059/README.md): align the default
  Python strategy and pip/pipenv descriptors with ticket-058's retry-safe
  Twine contract. State: `DONE / DONE`; 618 tests (2 skips), scoped Ruff,
  governance, protected CI and exact-head Validator approval pass; PR #98
  merged unchanged as `1895dde...`; classification:
  `BUG / P1 / regression`; depends on ticket-058.

- [x] Deliver [ticket-058](project/ticket-058/README.md): make configured Twine
  publication retries idempotent at runtime and migrate legacy commands
  through doctor PY013. State: `DONE / DONE`; configuration producers and
  governance-owned `goal.yaml` are split into dependent bounded tickets;
  615 tests (2 skips), protected CI and
  exact-head Validator approval passed; PR #96 merged unchanged as
  `f1e5c0e...`; classification: `BUG / P0 / regression`; depends on ticket-057.

- [x] Deliver [ticket-057](project/ticket-057/README.md): publish the merged
  mutation-free PR-resume repair as Goal 2.1.299. State: `DONE / DONE`; PR #94
  passed 607 tests (2 skips), Python 3.12/3.13, Ruff, governance, build, Docker
  and exact-head Validator approval, then merged as `4db0b042...`. PyPI,
  annotated `v2.1.299` and the final GitHub Release are bound to that merge;
  a fresh public-index install proved Git-common audit storage; classification:
  `SERVICE / P0 / requested`; depends on ticket-056.

- [x] Deliver [ticket-056](project/ticket-056/README.md): make canonical bare
  `goal -a` infer exactly one active governed ticket before bootstrap and keep
  committed PR resume plus delivery audit mutation-free. State: `DONE / DONE`;
  54 focused and 607 full tests (2 existing skips), Ruff, governance, package
  and Docker validation passed; exact-head Validator approval `4919030999`;
  PR #92 merged as `a05b2f984511d...`; classification: `BUG / P0 / regression`;
  depends on ticket-055.

- [x] Deliver [ticket-055](project/ticket-055/README.md): make governed
  pull-request resume mutation-free and independent of colliding merged local
  branch aliases. State: `DONE / DONE`; 51 focused and 604 full
  tests (2 existing skips), Ruff, explicit governance, remediation DSL and
  Docker validation pass; PR #89 passed hosted CI, remote lifecycle and
  trusted exact-head Validator approval, then merged as `da81ad9b...`;
  classification: `BUG / P1 / regression`.

- [x] Deliver [ticket-054](project/ticket-054/README.md): remove the redundant
  mutable `goal:local` Compose image tag while retaining the local build. State:
  `DONE / DONE`; PR #85 passed 600 tests (2 existing skips), hosted CI, live
  lifecycle and trusted exact-head Validator approval, then merged as
  `6c7da535...`; classification: `BUG / P1 / regression`; prerequisite for
  ticket-053.

- [x] Deliver [ticket-053](project/ticket-053/README.md): adopt the complete
  published new-project 0.16.1 governance package, including deterministic
  remediation-intent/todo2code analysis and workspace lifecycle checks. State:
  `DONE / DONE`; the exact managed payload, drift check, DSL probes, workspace
  audit and 600 tests (2 existing skips) pass locally; PR #87 passed Python
  3.12/3.13 CI, live lifecycle and trusted exact-head Validator approval and
  merged as `81727017...`; classification: `BUG / P1 / regression`; depends on
  ticket-051, ticket-052 and ticket-054.

- [x] Deliver [ticket-052](project/ticket-052/README.md): install the exact
  published new-project 0.16.1 remote-lifecycle workflow after its checker
  prerequisite. State: `DONE / DONE`; PR #82 passed 600 tests (2 existing
  skips), Python 3.12/3.13 CI, its live lifecycle check and trusted exact-head
  Validator approval, then merged as `ac281ed8...`; classification:
  `BUG / P1 / regression`; depends on ticket-051.

- [x] Deliver [ticket-051](project/ticket-051/README.md): install the exact
  published new-project 0.16.1 branch lifecycle checker as the
  governance-owned prerequisite for the separately owned remote-lifecycle
  workflow and final package adoption. State: `DONE / DONE`; PR #80 passed
  600 tests (2 existing skips), Python 3.12/3.13 CI and trusted exact-head
  Validator approval, then merged as `25f66fae...`; classification:
  `BUG / P1 / regression`.

- [x] Deliver [ticket-050](project/ticket-050/README.md): publish the merged
  artifactless GitHub Release repair as Goal 2.1.298, verify immutable public
  artifacts and use the fresh public CLI to complete `new-project v0.16.1`.
  State: `DONE / DONE`; PR #77 passed Python 3.12/3.13 CI and exact-head
  Validator approval, then merge `4388d1e...` passed 600 tests (2 skipped),
  scoped Ruff, governance, package and Docker checks. Public PyPI, annotated
  tag and final Release are immutable and the fresh public CLI completed the
  assetless `new-project v0.16.1` Release without moving its tag or `main`;
  classification: `SERVICE / P0 / requested`.

- [x] Deliver [ticket-049](project/ticket-049/README.md): safely resume governed
  pull-request delivery when an authorized ticket commit exists ahead of the
  remote base but the original run stopped before branch/PR creation. State:
  `DONE / DONE`; PR #76 passed protected CI and exact-head Validator approval,
  then merge `7534d1ab...` passed 600 tests (2 skipped), scoped Ruff and
  governance in a clean worktree. Package and Docker validation also pass;
  classification: `BUG / P1 / regression`.

- [x] Deliver [ticket-048](project/ticket-048/README.md): let generic governed
  direct-main publication create or repair a GitHub Release without package
  assets, while keeping registry fallback artifact-strict and requiring an
  existing recovery tag to be annotated and exact-HEAD. State: `DONE / DONE`;
  PR #72, #73 and #74 merged the release, version-recovery and canonical
  metadata repairs after protected CI and exact-head Validator approvals. The
  clean final merge passes 594 tests (2 skipped) and governance; the real
  assetless `new-project v0.16.0` Release is canonical while its annotated tag
  and remote main remain unchanged at `6800f013...`.
  Classification:
  `BUG / P0 / regression`.

- [x] Deliver [ticket-047](project/ticket-047/README.md): publish the merged
  source-hub health repair as Goal 2.1.297, verify immutable public artifacts
  and use the fresh public CLI for the real `new-project` ticket-065 flow.
  State: `DONE / DONE`; classification: `SERVICE / P0 / requested`.

- [x] Deliver [ticket-046](project/ticket-046/README.md): run the maintained
  `new-project` source-hub health contract through Goal's headless check and
  governed delivery paths without installing the target package into the hub.
  State: `DONE / DONE`; implementation merged as `main@3ba0aa0` after
  exact-head CI and Validator approval; public 2.1.297 and the real source-hub
  delivery proof are complete; classification:
  `BUG / P0 / regression`.

- [x] Deliver [ticket-044](project/ticket-044/README.md): retry one otherwise
  valid open PR's transiently stale head after a successful governed push,
  while preserving the terminal exact-head failure. State:
  `DONE / DONE`; 18 focused and 574 full tests pass (2 existing skips), Ruff,
  governance, package and Docker builds pass, the real governed flow reused PR
  #69, and CI plus Validator approved exact head `6837dd2` before merge as
  `main@000da3c`; classification: `BUG / P0 / regression`.

- [x] Deliver [ticket-043](project/ticket-043/README.md): publish the merged
  source-hub and delivery-coherence repairs as Goal 2.1.296, verify immutable
  public artifacts and use the fresh public CLI for the next `new-project`
  delivery. State: `DONE / DONE`; 573 tests pass with 2 existing skips on the
  clean merge, CI and Validator approved exact head `b99fdd1`, PR #68 merged
  as `main@c5f3684`, and PyPI, annotated tag, final GitHub Release and fresh
  public install all verify 2.1.296; classification: `SERVICE / P0 / requested`.

- [x] Deliver [ticket-042](project/ticket-042/README.md): keep subcommand help
  read-only and make the explicit no-version/no-tag/no-publish combination a
  coherent plain delivery even with committed-unreleased package source.
  State: `DONE / DONE`; 573 tests pass (2 existing skips), CI and Validator
  approved exact head `910fcc6`, PR #67 merged as `main@f31e07b`, clean-merge
  focused/governance checks pass and all ticket resources are removed;
  classification: `BUG / P0 / regression`.

- [x] Deliver [ticket-041](project/ticket-041/README.md): distinguish adopted
  `new-project` targets from the source hub, keep governance verification
  read-only, and surface canonical diagnostics v2 remediation/runbooks. State:
  `DONE / DONE`; 46 focused and 570 full tests pass (2 skipped), governance,
  Ruff, package and Docker builds pass, the real hub probe is read-only, and
  CI plus Validator App approved exact head `0e0f5a0` before PR #66 merged as
  `main@f6f7653`; classification: `BUG / P2 / regression`.

- [x] Deliver [ticket-040](project/ticket-040/README.md): publish Goal 2.1.295
  from the merged adoption-proof and scoped bootstrap repairs, then verify a
  clean public install. State: `DONE / DONE`; real `goal -a` passed 560 tests
  (2 skipped), CI and Validator Agent approved exact head `c37252d`, PR #65
  merged as `main@11561fd`, and PyPI/tag/final GitHub Release evidence matches
  2.1.295; classification:
  `SERVICE / P0 / requested`.

- [x] Deliver [ticket-039](project/ticket-039/README.md): keep legacy Goal tool
  marker migration inside declared development dependency sections so
  bootstrap cannot rewrite runtime requirements. State: `DONE / DONE`; 3
  focused and 560 full tests pass (2 skipped), CI and Validator Agent approved
  exact head `8b5e1ad`, and PR #64 merged as `main@23493d7`;
  classification: `BUG / P0 / regression`.

- [x] Deliver [ticket-038](project/ticket-038/README.md): require canonical
  GitHub Release metadata in addition to the exact annotated tag before Goal
  executes a `new-project` production adoption. State: `DONE / DONE`; 24
  focused and 559 full tests pass (2 skipped), CI and Validator Agent approved
  exact head `35047d6`, and PR #63 merged as `main@2d9873c`;
  classification: `BUG / P0 / regression`.

- [x] Deliver [ticket-037](project/ticket-037/README.md): require exact
  annotated-tag evidence before Goal executes a `new-project` adoption
  generator, with an explicit non-production candidate test path. A dependent
  ticket will verify GitHub Release metadata. State: `DONE / DONE`; 551 tests
  passed (2 skipped), Python 3.12/3.13 CI passed, Validator Agent approved the
  exact head, and PR #62 merged as `main@069b678`; classification:
  `BUG / P0 / regression`.

- [x] Deliver [ticket-036](project/ticket-036/README.md): run the immutable
  adopted workspace lifecycle checker through a headless Goal command. State:
  `DONE / DONE`; 12 focused and 547 full tests pass (2 skipped), Python
  3.12/3.13 CI passed, and PR #61 merged as `main@61f34b7`; classification:
  `FEATURE / application`.

- [x] Deliver [ticket-035](project/ticket-035/README.md): stage generated
  slow-test tickets before commit and preserve exact safe bootstrap templates.
  State: `DONE`; 545 tests, Ruff, governance, package and Docker pass;
  classification: `BUG / application`; no publication.
- [x] Deliver [ticket-034](project/ticket-034/README.md): let `goal -a`
  recover only a uniform local version exactly one patch behind the registry.
  State: `DONE`; 541 tests, Ruff, governance, package and Docker pass;
  classification: `BUG / application`; no publication.
- [x] Deliver [ticket-033](project/ticket-033/README.md): migrate legacy
  unmarked Goal tool requirements to interpreter-compatible markers. State:
  `DONE`; 536 tests, Ruff, governance, package and Docker pass;
  classification: `BUG / application`; no publication.
- [x] Deliver [ticket-032](project/ticket-032/README.md): expose the adopted
  deterministic governance package through `goal governance check` and keep
  the whole governance dispatcher headless until a delivery callback explicitly
  requests configuration. Focused/full tests, package build, governance,
  Docker and exact-HEAD downstream adoption pass. State: `DONE / DONE`;
  classification: `FEATURE / application`; no publication.
- [x] Deliver [ticket-030](project/ticket-030/README.md): bind tag evidence to
  package identity and preserve target Python support when injecting developer
  tools. State: `DONE`; classification: `BUG / application`.
- [x] Deliver [ticket-029](project/ticket-029/README.md): keep governed
  publish-only artifacts on the exact clean remote base and make bootstrap
  read-only. State: `DONE`; classification: `BUG / application`.
- [x] Deliver [ticket-028](project/ticket-028/README.md): publish the merged
  exact-head PR lifecycle repair as Goal 2.1.294 and verify a clean public
  install. State: `DONE / DONE`; release carriers merged through validated PR
  #59, and PyPI wheel/sdist plus a fresh wheel import were verified;
  classification: `SERVICE / integration`.
- [x] Deliver [ticket-027](project/ticket-027/README.md): resolve only open,
  exact-head PRs after pushing a governed branch, even when that branch had a
  previously merged PR. State: `DONE`; classification:
  `BUG / application`.
- [x] Deliver [ticket-026](project/ticket-026/README.md): preserve clean
  `publish-only --force-publish` intent without creating a release commit.
  State: `DONE / PUBLICATION`; classification: `BUG / application`.
- [x] Deliver [ticket-025](project/ticket-025/README.md): publish the merged
  delivery-integrity fixes as Goal 2.1.293 and verify a clean public install.
  State: `DONE / PUBLICATION`; classification:
  `SERVICE / integration`.
- [x] Deliver [ticket-024](project/ticket-024/README.md): preserve dry-run state,
  fail closed on every Git push error and retain declared UV verification
  dependencies. State: `DONE / PUBLICATION`; classification:
  `BUG / application`.
- [x] Review and approve [ticket-001](project/ticket-001/README.md): Goal
  URI/DSL/CQRS+ES refactoring blueprint, diagrams and machine-readable scope.
- [x] Re-review [ticket-002](project/ticket-002/README.md): adopt published
  governance revision, preserve the legacy analysis entry point as
  `project/analysis.sh`, and configure target workstreams.
- [x] After ticket-002, review [ticket-003](project/ticket-003/README.md):
  enforce governed `goal -a` delivery with explicit `direct-main`,
  `publish-only`, and `pull-request` modes.
- [x] Review [ticket-005](project/ticket-005/README.md): enable the governed
  delivery policy in Goal configuration and install the local pre-push guard.
- [x] Review and deliver [ticket-006](project/ticket-006/README.md): adopt immutable
  new-project 0.11.0 through Goal's local governance adapter before adding the
  CC-to-kind runtime classifier. State: `DONE`.
- [x] Review and deliver [ticket-007](project/ticket-007/README.md): repair the
  existing OpenRouter environment-validation NameError. State: `DONE`;
  classification: `SERVICE / health`.
- [x] Validate and deliver [ticket-009](project/ticket-009/README.md): preserve
  multi-line `VERSION` contracts and governed explicit delivery modes. State:
  `DONE`; classification: `SERVICE / delivery`.
- [x] Review and approve [ticket-010](project/ticket-010/README.md): make Goal
  resolve normal, already-bumped and partially bumped version states from
  file/Git/registry evidence, then enforce strict pre-release consistency.
  State: `DONE`; classification: `SERVICE / release`.
- [x] Deliver [ticket-011](project/ticket-011/README.md): isolate the
  metadata-only workflow test from real Git commits and abort delivery when a
  docs-only commit fails. State: `DONE`; classification:
  `SERVICE / delivery`.
- [x] Deliver [ticket-012](project/ticket-012/README.md): align the integration
  runtime with Python 3.12+, refresh compatible dependencies, pass the full
  test/container matrix and publish through `goal -a`. State:
  `DONE / PUBLICATION`; release 2.1.290 verified from the public registry;
  classification: `SERVICE / integration`.
- [x] Deliver [ticket-013](project/ticket-013/README.md): adopt immutable
  new-project 0.14.1 and assign integration/lockfile ownership. State:
  `DONE / PUBLICATION`; classification: `SERVICE / governance`.
- [x] Deliver [ticket-015](project/ticket-015/README.md): add the required root
  Goal CLI image on Python 3.12 so the v0.14.1 governance adoption can pass.
  State: `DONE / PUBLICATION`; classification: `SERVICE / infrastructure`.
- [x] Close [ticket-014](project/ticket-014/README.md): the proposed Goal-side
  prior-revision fetch was disproved and safely cancelled before implementation;
  the defect was routed upstream. State: `CANCELLED`; classification:
  `BUG / application`.
- [x] Deliver [ticket-016](project/ticket-016/README.md): exclude managed
  governance Python helpers from package release classification before ticket
  012 publishes. State: `DONE / PUBLICATION`; classification:
  `BUG / application`.
- [x] Deliver [ticket-017](project/ticket-017/README.md): assign the remaining
  atomic release metadata to integration before ticket 012 publishes. State:
  `DONE / PUBLICATION`; classification: `SERVICE / governance`.
- [x] Deliver [ticket-018](project/ticket-018/README.md): infer the synchronized
  version transition after a stale tag so post-publication metadata delivery
  does not select a duplicate patch. State: `DONE / PUBLICATION`;
  classification: `BUG / application`.
- [x] Deliver [ticket-019](project/ticket-019/README.md): publish the merged
  boundary repair as Goal 2.1.291 and verify a fresh public-index install.
  State: `DONE / PUBLICATION`; classification: `SERVICE / integration`.
- [x] Deliver [ticket-020](project/ticket-020/README.md): record Goal 2.1.291
  release notes and publication evidence without another version change.
  State: `DONE / PUBLICATION`; classification: `SERVICE / integration`.
- [x] Deliver [ticket-021](project/ticket-021/README.md): detect only writable
  Python `__version__` declarations and support conventional version modules.
  State: `DONE / PUBLICATION`; classification: `BUG / application`.
- [x] Deliver [ticket-023](project/ticket-023/README.md): publish the merged
  Python carrier fix as Goal 2.1.292 and verify a clean public install.
  State: `DONE / PUBLICATION`; classification: `SERVICE / integration`.
- [ ] After governance bootstrap, execute the sequential phases defined in
  [the refactoring plan](docs/GOAL_KORU_SUBACTOR_REFACTORING_PLAN.md), with one
  narrowly scoped ticket active at a time.

> Current workflow state: `ticket-001 DONE`; `ticket-002 DONE`;
> `ticket-003 DONE`; `ticket-004 DONE`; `ticket-005 DONE`;
> `ticket-006 DONE`; `ticket-007 DONE`; `ticket-009 DONE`.
> `ticket-010 DONE`; `ticket-011 DONE`; `ticket-012 DONE`;
> `ticket-013 DONE`; `ticket-014 CANCELLED`; `ticket-015 DONE`;
> `ticket-016 DONE`; `ticket-017 DONE`; `ticket-018 DONE`;
> `ticket-019 DONE`; `ticket-020 DONE`; `ticket-021 DONE`;
> `ticket-023 DONE`; `ticket-024 DONE`; `ticket-025 DONE`;
> `ticket-026 DONE`; `ticket-027 DONE`; `ticket-028 IN_PROGRESS`;
> `ticket-029 DONE`; `ticket-030 DONE`; `ticket-032 DONE`;
> `ticket-033 DONE`; `ticket-034 DONE`; `ticket-035 DONE`.

> **Recently shipped (manual note):** `goal all [PATHS...]` monorepo sweep —
> runs `goal -a` in every git repo with uncommitted changes under the given
> paths. Includes the `goal -a ./*` shorthand and the `goal auto` word-form of
> the `-a` flag. See `docs/commands.md` and the CHANGELOG `[Unreleased]` entry.
>
> Follow-ups to consider:
> - `goal all` option to skip repos whose only changes are generated artifacts
>   (avoid empty "docs" commits during a sweep).
> - Parallelize per-project runs (currently sequential).
> - Forward `--bump`/`--no-publish`/`--message` from `goal all` into each child.

**Generated by:** prefact v0.1.58
**Generated on:** 2026-06-20T01:12:19.891555
**Total issues:** 377 active, 33 completed

---

## ✅ Completed Tasks

- [x] Issue #11 - Make `goal --dry-run publish` report the planned
  method/version without invoking Make or a package registry.
- [x] Issue #13 - Align declared, tox and CI support at Python 3.12–3.13,
  configure the runner Git/Goal identity and stop suppressing dependency
  installation failures.
- [x] goal/cli/__init__.py:384 - Relative import (level=1): '.version'
- [x] goal/cli/__init__.py:307 - String concatenation can be converted to f-string
- [x] goal/cli/__init__.py:9 - Unused List imported from typing
- [x] goal/cli/publish.py:195 - String concatenation can be converted to f-string
- [x] goal/cli/publish.py:218 - String concatenation can be converted to f-string
- [x] goal/cli/publish.py:179 - Magic number: 120 - use named constant
- [x] goal/cli/publish.py:179 - Magic number: 300 - use named constant
- [x] goal/cli/tests.py:188 - String concatenation can be converted to f-string
- [x] goal/cli/tests.py:332 - String concatenation can be converted to f-string
- [x] goal/cli/tests.py:274 - String concatenation can be converted to f-string
- [x] goal/cli/tests.py:188 - Magic number: 120 - use named constant
- [x] goal/cli/tests.py:202 - Magic number: 120 - use named constant
- [x] goal/cli/tests_pytest_setup.py:45 - Magic number: 120 - use named constant
- [x] goal/cli/tests_pytest_setup.py:107 - Magic number: 120 - use named constant
- [x] goal/config/constants.py:262 - Magic number: 50 - use named constant
- [x] goal/config/manager.py:425 - LLM-style docstring in init_config
- [x] goal/config/manager.py:445 - LLM-style docstring in load_config
- [x] goal/config/manager.py:459 - LLM-style docstring in ensure_config
- [x] goal/config/validation.py:332 - Function 'check_keys' missing return type (suggested: -> None)
- [x] goal/config/validation.py:400 - String concatenation can be converted to f-string
- [x] goal/config/validation.py:413 - String concatenation can be converted to f-string
- [x] goal/config/validation.py:382 - LLM-style docstring in validate_config_file
- [x] goal/config/validation.py:441 - LLM-style docstring in validate_config_interactive
- [x] goal/config/validation.py:494 - LLM-style docstring in _auto_fix_config
- [x] goal/git_ops.py:61 - String concatenation can be converted to f-string
- [x] goal/git_ops.py:96 - String concatenation can be converted to f-string
- [x] goal/git_ops.py:616 - Magic number: 10000 - use named constant
- [x] goal/git_ops.py:259 - LLM-style docstring in clone_repository
- [x] goal/package_managers.py:506 - LLM-style docstring in format_package_manager_command
- [x] goal/push/core.py:47 - String concatenation can be converted to f-string
- [x] goal/push/core.py:291 - String concatenation can be converted to f-string
- [x] goal/push/core.py:112 - String concatenation can be converted to f-string
- [x] goal/push/commands.py:30 - Function 'push' missing return type (suggested: -> None)

## 📋 Current Issues (showing 200 of 377)

- [x] goal/authors/__init__.py:9 - Relative import (level=1): '.manager'
- [x] goal/authors/__init__.py:10 - Relative import (level=1): '.utils'
- [ ] goal/__main__.py:16 - module execution block
- [ ] goal/authors/manager.py:227 - String concatenation can be converted to f-string
- [ ] goal/authors/manager.py:206 - Magic number: 40 - use named constant
- [ ] goal/authors/manager.py:315 - LLM-style docstring in get_project_authors
- [ ] goal/authors/manager.py:328 - LLM-style docstring in add_project_author
- [x] goal/authors/manager.py:15 - LLM-style docstring in __init__
- [ ] goal/authors/utils.py:7 - LLM-style docstring in format_co_author_trailer
- [ ] goal/authors/utils.py:20 - LLM-style docstring in parse_co_authors
- [ ] goal/authors/utils.py:44 - LLM-style docstring in add_co_authors_to_message
- [ ] goal/bootstrap/costs_badge.py:77 - Function 'calculate_human_time' missing return type (suggested: -> Any)
- [ ] goal/bootstrap/costs_badge.py:3 - Unused import: 'annotations'
- [ ] goal/bootstrap/costs_badge.py:162 - Magic number: 500 - use named constant
- [ ] goal/bootstrap/costs_badge.py:170 - Magic number: 50 - use named constant
- [ ] goal/bootstrap/pyproject_costs_setup.py:76 - String concatenation can be converted to f-string
- [ ] goal/bootstrap/pyproject_costs_setup.py:97 - String concatenation can be converted to f-string
- [ ] goal/bootstrap/pyproject_costs_setup.py:73 - String concatenation can be converted to f-string
- [ ] goal/bootstrap/pyproject_costs_setup.py:3 - Unused import: 'annotations'
- [ ] goal/bootstrap/installer.py:140 - LLM-style docstring in _install_python_deps_broker
- [ ] goal/changelog.py:52 - String concatenation can be converted to f-string
- [ ] goal/changelog.py:93 - String concatenation can be converted to f-string
- [ ] goal/changelog.py:94 - String concatenation can be converted to f-string
- [ ] goal/changelog.py:97 - LLM-style docstring in update_changelog
- [ ] goal/cli/__init__.py:456 - Relative import (level=1): '.version'
- [ ] goal/cli/__init__.py:344 - String concatenation can be converted to f-string
- [ ] goal/cli/__init__.py:4 - Unused import re
- [ ] goal/cli/__init__.py:9 - Unused Dict imported from typing
- [ ] goal/cli/__init__.py:23 - Unused run_git imported from goal.git_ops
- [ ] goal/cli/authors_cmd.py:102 - Function 'authors_co_author' missing return type (suggested: -> None)
- [ ] goal/cli/authors_cmd.py:109 - Function 'authors_current' missing return type (suggested: -> None)
- [ ] goal/cli/commit_cmd.py:103 - Relative import (level=2): '..enhanced_summary'
- [ ] goal/cli/commit_cmd.py:101 - Function 'fix_summary' missing return type (suggested: -> None)
- [ ] goal/cli/commit_cmd.py:161 - Function 'validate' missing return type (suggested: -> None)
- [ ] goal/cli/config_cmd.py:68 - Function 'config_update' missing return type (suggested: -> None)
- [ ] goal/cli/config_cmd.py:78 - Function 'config_set' missing return type (suggested: -> None)
- [ ] goal/cli/config_cmd.py:91 - Function 'config_get' missing return type (suggested: -> None)
- [ ] goal/cli/doctor_cmd.py:31 - Formatting a regular string which could be an f-string
- [ ] goal/cli/doctor_cmd.py:61 - String concatenation can be converted to f-string
- [ ] goal/cli/license_cmd.py:191 - Magic number: 40 - use named constant
- [ ] goal/cli/publish.py:437 - String concatenation can be converted to f-string
- [ ] goal/cli/publish.py:495 - String concatenation can be converted to f-string
- [ ] goal/cli/publish.py:17 - Unused github_fallback_actionable imported from goal.publish.github_fallback
- [ ] goal/cli/publish.py:17 - Unused import: 'github_fallback_actionable'
- [ ] goal/cli/publish.py:376 - Magic number: 120 - use named constant
- [ ] goal/cli/publish.py:376 - Magic number: 300 - use named constant
- [ ] goal/cli/postcommit_cmd.py:55 - Magic number: 40 - use named constant
- [ ] goal/cli/tests_pytest_setup.py:3 - Unused import: 'annotations'
- [ ] goal/cli/tests_pytest_setup.py:44 - Magic number: 120 - use named constant
- [ ] goal/cli/tests_pytest_setup.py:106 - Magic number: 120 - use named constant
- [ ] goal/cli/tests.py:224 - String concatenation can be converted to f-string
- [ ] goal/cli/tests.py:377 - String concatenation can be converted to f-string
- [ ] goal/cli/tests.py:391 - String concatenation can be converted to f-string
- [ ] goal/cli/tests.py:224 - Magic number: 120 - use named constant
- [ ] goal/cli/tests.py:238 - Magic number: 120 - use named constant
- [x] goal/cli/version.py:8 - Relative import (level=1): '.version_types'
- [x] goal/cli/version.py:9 - Relative import (level=1): '.version_utils'
- [x] goal/cli/version.py:20 - Relative import (level=1): '.version_sync'
- [ ] goal/cli/version_sync.py:13 - Relative import (level=1): '.version_utils'
- [ ] goal/cli/utils_cmd.py:113 - Function 'version' missing return type (suggested: -> None)
- [ ] goal/cli/utils_cmd.py:140 - Function 'package_managers' missing return type (suggested: -> None)
- [ ] goal/cli/utils_cmd.py:163 - Function 'check_versions' missing return type (suggested: -> None)
- [ ] goal/cli/validation_cmd.py:55 - Magic number: 40 - use named constant
- [ ] goal/cli/version_utils.py:20 - Relative import (level=1): '.version_types'
- [ ] goal/cli/version_utils.py:344 - String concatenation can be converted to f-string
- [ ] goal/cli/version_utils.py:428 - String concatenation can be converted to f-string
- [ ] goal/cli/version_utils.py:453 - String concatenation can be converted to f-string
- [ ] goal/cli/version_utils.py:3 - Unused import: 'annotations'
- [ ] goal/cli/version_utils.py:413 - boilerplate copyright
- [ ] goal/cli/version_utils.py:427 - boilerplate copyright
- [ ] goal/cli/version_utils.py:433 - boilerplate copyright
- [ ] goal/cli/wizard_cmd.py:77 - Magic number: 40 - use named constant
- [ ] goal/cli/wizard_cmd.py:165 - Magic number: 40 - use named constant
- [ ] goal/cli/wizard_cmd.py:224 - Magic number: 40 - use named constant
- [ ] goal/cli/wizard_cmd.py:205 - boilerplate copyright
- [x] goal/config/__init__.py:8 - Relative import (level=1): '.constants'
- [x] goal/config/__init__.py:11 - Relative import (level=1): '.manager'
- [x] goal/config/__init__.py:19 - Relative import (level=1): '.validation'
- [ ] goal/config/constants.py:19 - Magic number: 50 - use named constant
- [ ] goal/config/constants.py:20 - Magic number: 200 - use named constant
- [ ] goal/config/constants.py:278 - Magic number: 50 - use named constant
- [ ] goal/config/validation.py:355 - Function 'check_keys' missing return type (suggested: -> None)
- [ ] goal/config/validation.py:428 - String concatenation can be converted to f-string
- [ ] goal/config/validation.py:441 - String concatenation can be converted to f-string
- [ ] goal/config/validation.py:410 - LLM-style docstring in validate_config_file
- [ ] goal/config/validation.py:469 - LLM-style docstring in validate_config_interactive
- [ ] goal/config/validation.py:522 - LLM-style docstring in _auto_fix_config
- [ ] goal/config/manager.py:490 - LLM-style docstring in init_config
- [ ] goal/config/manager.py:510 - LLM-style docstring in load_config
- [ ] goal/config/manager.py:524 - LLM-style docstring in ensure_config
- [ ] goal/deep_analyzer.py:49 - String concatenation can be converted to f-string
- [x] goal/doctor/__init__.py:8 - Relative import (level=1): '.models'
- [x] goal/doctor/__init__.py:11 - Relative import (level=1): '.core'
- [x] goal/doctor/__init__.py:18 - Relative import (level=1): '.python'
- [ ] goal/doctor/__init__.py:11 - Unused _DIAGNOSTICS imported from core
- [ ] goal/doctor/__init__.py:28 - Unused _generate_ticket_id imported from todo
- [ ] goal/doctor/__init__.py:28 - Unused _read_existing_tickets imported from todo
- [ ] goal/dependency_update.py:58 - String concatenation can be converted to f-string
- [ ] goal/dependency_update.py:3 - Unused import: 'annotations'
- [ ] goal/doctor/dotnet.py:12 - String concatenation can be converted to f-string
- [x] goal/doctor/core.py:35 - LLM-style docstring in diagnose_project
- [ ] goal/doctor/logging.py:4 - Relative import (level=1): '.models'
- [ ] goal/doctor/python_diag_core.py:81 - String concatenation can be converted to f-string
- [ ] goal/doctor/python_diag_core.py:67 - String concatenation can be converted to f-string
- [ ] goal/doctor/python_diag_core.py:262 - LLM-style docstring in check_py009_string_authors
- [x] goal/generator/__init__.py:3 - Relative import (level=1): '.git_ops'
- [x] goal/generator/__init__.py:4 - Relative import (level=1): '.analyzer'
- [x] goal/generator/__init__.py:5 - Relative import (level=1): '.generator'
- [ ] goal/doctor/todo.py:134 - Relative import (level=1): '.core'
- [ ] goal/doctor/todo.py:115 - String concatenation can be converted to f-string
- [ ] goal/doctor/todo.py:15 - Magic number: 50 - use named constant
- [ ] goal/doctor/todo.py:56 - LLM-style docstring in add_issues_to_todo
- [ ] goal/formatter.py:3 - Magic number: 20 - use named constant
- [ ] goal/formatter.py:4 - Magic number: 50 - use named constant
- [ ] goal/formatter.py:79 - LLM-style docstring in _build_functional_overview
- [ ] goal/generator/analyzer.py:303 - String concatenation can be converted to f-string
- [ ] goal/generator/generator.py:339 - Function 'fmt_file_list' missing return type (suggested: -> None)
- [ ] goal/generator/generator.py:285 - String concatenation can be converted to f-string
- [ ] goal/generator/generator.py:346 - Magic number in comparison: 20
- [ ] goal/generator/generator.py:346 - Magic number: 20 - use named constant
- [ ] goal/generator/generator.py:343 - Magic number: 20 - use named constant
- [ ] goal/generator/git_ops.py:172 - Function 'clear_cache' missing return type (suggested: -> None)
- [x] goal/hooks/__init__.py:9 - Relative import (level=1): '.manager'
- [x] goal/hooks/__init__.py:10 - Relative import (level=1): '.config'
- [ ] goal/git_ops.py:19 - Function 'echo_md' missing return type (suggested: -> None)
- [ ] goal/git_ops.py:41 - String concatenation can be converted to f-string
- [ ] goal/git_ops.py:67 - String concatenation can be converted to f-string
- [ ] goal/git_ops.py:104 - String concatenation can be converted to f-string
- [ ] goal/git_ops.py:634 - Magic number: 10000 - use named constant
- [ ] goal/git_ops.py:277 - LLM-style docstring in clone_repository
- [ ] goal/hooks/config.py:41 - LLM-style docstring in get_hook_config
- [ ] goal/hooks/config.py:71 - LLM-style docstring in create_precommit_config
- [x] goal/hooks/manager.py:14 - Relative import (level=2): '..validators.file_validator'
- [x] goal/hooks/manager.py:15 - Relative import (level=2): '..git_ops'
- [ ] goal/hooks/manager.py:94 - Magic number: 493 - use named constant
- [ ] goal/hooks/manager.py:257 - Magic number: 30 - use named constant
- [ ] goal/hooks/manager.py:275 - LLM-style docstring in install_hooks
- [ ] goal/hooks/manager.py:289 - LLM-style docstring in uninstall_hooks
- [ ] goal/hooks/manager.py:302 - LLM-style docstring in run_hooks
- [ ] goal/hooks/manager.py:83 - standalone main function
- [ ] goal/installers/config.py:14 - Magic number: 300 - use named constant
- [ ] goal/installers/config.py:16 - Magic number: 300 - use named constant
- [ ] goal/installers/config.py:24 - Magic number: 300 - use named constant
- [x] goal/installers/broker.py:153 - Magic number in comparison: 50
- [x] goal/installers/broker.py:153 - Magic number: 50 - use named constant
- [ ] goal/installers/broker.py:48 - LLM-style docstring in install
- [ ] goal/installers/managers/pdm.py:11 - Magic number: 20 - use named constant
- [ ] goal/installers/managers/poetry.py:11 - Magic number: 30 - use named constant
- [ ] goal/io/__init__.py:3 - Relative import (level=1): '.stdio'
- [x] goal/license/__init__.py:10 - Relative import (level=1): '.manager'
- [x] goal/license/__init__.py:11 - Relative import (level=1): '.spdx'
- [ ] goal/io/stdio.py:3 - Unused import: 'annotations'
- [x] goal/postcommit/__init__.py:10 - Relative import (level=1): '.manager'
- [x] goal/postcommit/__init__.py:11 - Relative import (level=1): '.actions'
- [ ] goal/license/manager.py:550 - LLM-style docstring in create_license_file
- [ ] goal/license/manager.py:571 - LLM-style docstring in update_license_file
- [ ] goal/license/manager.py:310 - LLM-style docstring in __init__
- [x] goal/license/manager.py:12 - boilerplate copyright
- [ ] goal/license/spdx.py:109 - LLM-style docstring in validate_spdx_id
- [ ] goal/license/spdx.py:153 - LLM-style docstring in get_license_info
- [ ] goal/license/spdx.py:178 - LLM-style docstring in check_compatibility
- [ ] goal/package_managers.py:485 - LLM-style docstring in get_preferred_package_manager
- [ ] goal/package_managers.py:543 - LLM-style docstring in format_package_manager_command
- [ ] goal/postcommit/actions.py:55 - Magic number: 50 - use named constant
- [ ] goal/postcommit/actions.py:18 - LLM-style docstring in execute
- [ ] goal/publish/__init__.py:3 - Relative import (level=1): '.changes'
- [x] goal/postcommit/manager.py:9 - Relative import (level=1): '.actions'
- [ ] goal/postcommit/manager.py:112 - Magic number: 40 - use named constant
- [ ] goal/postcommit/manager.py:152 - Magic number: 40 - use named constant
- [ ] goal/postcommit/manager.py:201 - LLM-style docstring in run_post_commit_actions
- [x] goal/postcommit/manager.py:15 - LLM-style docstring in __init__
- [x] goal/postcommit/manager.py:24 - LLM-style docstring in get_config
- [ ] goal/project_bootstrap.py:10 - Unused import json
- [ ] goal/project_bootstrap.py:10 - Unused import: 'json'
- [ ] goal/project_bootstrap.py:606 - LLM-style docstring in _install_python_deps_broker
- [x] goal/push/__init__.py:9 - Relative import (level=1): '.core'
- [x] goal/push/__init__.py:18 - Relative import (level=1): '.stages'
- [ ] goal/publish/changes.py:3 - Unused import: 'annotations'
- [ ] goal/publish/github_fallback.py:3 - Unused import: 'annotations'
- [x] goal/push/stages/__init__.py:3 - Relative import (level=1): '.commit'
- [ ] goal/push/stages/__init__.py:9 - Relative import (level=1): '.version'
- [ ] goal/push/stages/__init__.py:10 - Relative import (level=1): '.changelog'
- [ ] goal/push/commands.py:36 - Function 'push' missing return type (suggested: -> None)
- [ ] goal/push/core.py:51 - String concatenation can be converted to f-string
- [ ] goal/push/core.py:341 - String concatenation can be converted to f-string
- [ ] goal/push/core.py:116 - String concatenation can be converted to f-string
- [ ] goal/push/stages/publish.py:53 - String concatenation can be converted to f-string
- [ ] goal/push/stages/publish.py:103 - String concatenation can be converted to f-string
- [ ] goal/push/stages/publish.py:34 - String concatenation can be converted to f-string
- [ ] goal/push/stages/publish.py:8 - Unused echo_status_error imported from goal.io.stdio
- [ ] goal/push/stages/publish.py:8 - Unused import: 'echo_status_error'
- [ ] goal/push/stages/commit.py:207 - Relative import (level=2): '..core'
- [ ] goal/push/stages/commit.py:277 - Relative import (level=2): '..core'
- [ ] goal/push/stages/commit.py:210 - Relative import (level=1): '.version'
- [ ] goal/push/stages/costs.py:74 - Function 'calculate_human_time' missing return type (suggested: -> Any)
- [ ] goal/push/stages/costs.py:36 - Magic number: 500 - use named constant
- [ ] goal/push/stages/costs.py:43 - Magic number: 50 - use named constant
- [ ] goal/push/stages/todo.py:9 - LLM-style docstring in handle_todo_stage
- [x] goal/recovery/__init__.py:12 - Relative import (level=1): '.strategies'
- [x] goal/recovery/__init__.py:21 - Relative import (level=1): '.manager'

---

*To execute all tasks, run: `prefact -a --execute-todos`*
