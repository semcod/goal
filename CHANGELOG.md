## [Unreleased]

### Fixed
- Auto-update prompt no longer blocks help commands (--help, -h) by skipping version banner check
- Fixed nfo dependency constraint from nfo>=0.3.0 to nfo>=0.2.22 to match available PyPI version
- Subproject tests now automatically install dev dependencies when pytest is not available

### Changed
- Updated minimum Python version from 3.8 to 3.10 to match pfix>=0.1.60 requirements
- Updated tox test matrix from py38,py39,py310,py311,py312 to py310,py311,py312,py313

### Added
- **PackageManagerBroker**: Intelligent package manager selection system
  - Automatic detection of uv, pdm, poetry, pip with priority-based selection
  - Lockfile-aware installation (uv.lock, poetry.lock, pdm.lock detection)
  - Auto-installation of uv when missing: `pip install uv --quiet`
  - Timing and fallback reporting: "✅ uv (12.3s) | fallback: pip"
  - New module `goal/installers/` with abstract base class and manager implementations
  - UvManager (priority=10), PdmManager (priority=20), PoetryManager (priority=30), PipManager (priority=100)
- **`goal doctor --manager`**: Force specific package manager for dependency installation
- **21 new E2E tests** for installer system in `tests/test_installers_e2e.py`

### Changed
- **Refactored bootstrap system**: Split `project_bootstrap.py` (1265L) → `goal/bootstrap/` module
  - `goal/bootstrap/detector.py` - Project type detection
  - `goal/bootstrap/templates.py` - Project templates and configuration
  - `goal/bootstrap/installer.py` - Environment setup with PackageManagerBroker integration
  - `goal/bootstrap/configurator.py` - Test scaffolding and configuration helpers
  - Full backward compatibility maintained via re-exports in `goal/project_bootstrap.py`

### Deprecated
- Legacy `_install_python_deps()` waterfall approach (still works via fallback)

## [2.1.205] - 2026-04-26

### Docs
- Update README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/evolution.toon.yaml
- Update project/map.toon.yaml
- Update project/mermaid.export

## [2.1.204] - 2026-04-26

### Docs
- Update README.md

### Other
- Update uv.lock

## [2.1.203] - 2026-04-26

### Docs
- Update README.md

## [2.1.202] - 2026-04-26

### Docs
- Update CHANGELOG.md
- Update README.md

### Other
- Update .gitignore
- Update app.doql.css
- Update uv.lock

## [2.1.201] - 2026-04-26

### Docs
- Update README.md

## [2.1.200] - 2026-04-26

### Docs
- Update README.md

## [2.1.199] - 2026-04-26

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md

### Test
- Update tests/test_installers_e2e.py

## [2.1.198] - 2026-04-26

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update testql-scenarios/generated-cli-tests.testql.toon.yaml
- Update testql-scenarios/generated-from-pytests.testql.toon.yaml

### Other
- Update SUMR.json
- Update app.doql.less
- Update planfile.yaml
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- ... and 15 more files

## [0.1.10] - 2026-04-26

### Fixed
- Fix ai-boilerplate issues (ticket-5c7fe6eb)
- Fix relative-imports issues (ticket-6ffdf184)
- Fix string-concat issues (ticket-ffd86490)
- Fix magic-numbers issues (ticket-72e063c1)
- Fix llm-generated-code issues (ticket-3d5d23ae)
- Fix string-concat issues (ticket-d4e3e5d9)
- Fix llm-generated-code issues (ticket-6f238a23)
- Fix llm-generated-code issues (ticket-c67d7dc6)
- Fix relative-imports issues (ticket-d891f624)
- Fix string-concat issues (ticket-a5066b7f)
- Fix unused-imports issues (ticket-1fb93116)
- Fix duplicate-imports issues (ticket-59df6747)
- Fix smart-return-type issues (ticket-13ffec07)
- Fix relative-imports issues (ticket-a12b43b4)
- Fix smart-return-type issues (ticket-bfe2ab0a)
- Fix smart-return-type issues (ticket-bf75c893)
- Fix string-concat issues (ticket-87216eaa)
- Fix magic-numbers issues (ticket-00e007c1)
- Fix magic-numbers issues (ticket-4f93f900)
- Fix string-concat issues (ticket-9f353b29)
- Fix magic-numbers issues (ticket-c3bd2359)
- Fix smart-return-type issues (ticket-9f4e98ca)
- Fix relative-imports issues (ticket-1747b620)
- Fix relative-imports issues (ticket-a1a7a963)
- Fix magic-numbers issues (ticket-9e509799)
- Fix relative-imports issues (ticket-e37ef835)
- Fix string-concat issues (ticket-0d22f91b)
- Fix ai-boilerplate issues (ticket-41f077a4)
- Fix unused-imports issues (ticket-9a1f39a9)
- Fix magic-numbers issues (ticket-88530c76)
- Fix ai-boilerplate issues (ticket-2a97e91c)
- Fix relative-imports issues (ticket-adf2e12c)
- Fix magic-numbers issues (ticket-a5d61a36)
- Fix duplicate-imports issues (ticket-60fb35fd)
- Fix llm-generated-code issues (ticket-cf3d98ea)
- Fix smart-return-type issues (ticket-1b552216)
- Fix string-concat issues (ticket-6d2226bf)
- Fix duplicate-imports issues (ticket-3ab472e5)
- Fix llm-generated-code issues (ticket-cf8b12e8)
- Fix relative-imports issues (ticket-e9d90a2e)
- Fix unused-imports issues (ticket-d9982610)
- Fix string-concat issues (ticket-9506b597)
- Fix string-concat issues (ticket-17d0f4e6)
- Fix llm-generated-code issues (ticket-a3061483)
- Fix relative-imports issues (ticket-5722901a)
- Fix string-concat issues (ticket-7e3d16e7)
- Fix duplicate-imports issues (ticket-a4236fcf)
- Fix llm-generated-code issues (ticket-2bc855c2)
- Fix relative-imports issues (ticket-c1b28cdb)
- Fix string-concat issues (ticket-eda9fce4)
- Fix magic-numbers issues (ticket-8cce5e66)
- Fix llm-generated-code issues (ticket-5ca0239f)
- Fix relative-imports issues (ticket-60238f99)
- Fix magic-numbers issues (ticket-c49c4576)
- Fix llm-generated-code issues (ticket-c1674106)
- Fix string-concat issues (ticket-db256d03)
- Fix smart-return-type issues (ticket-b338f68e)
- Fix string-concat issues (ticket-65ea4331)
- Fix magic-numbers issues (ticket-e8323fdc)
- Fix smart-return-type issues (ticket-afc71edf)
- Fix relative-imports issues (ticket-b8770605)
- Fix llm-generated-code issues (ticket-99a82c71)
- Fix smart-return-type issues (ticket-31f7a7f8)
- Fix string-concat issues (ticket-c85170fb)
- Fix magic-numbers issues (ticket-eed103c2)
- Fix llm-generated-code issues (ticket-c4b45d93)
- Fix relative-imports issues (ticket-f80ace05)
- Fix relative-imports issues (ticket-87658dfc)
- Fix magic-numbers issues (ticket-6250f32c)
- Fix llm-generated-code issues (ticket-652b2b88)
- Fix ai-boilerplate issues (ticket-8648f1d9)
- Fix llm-generated-code issues (ticket-a3bcc668)
- Fix ai-boilerplate issues (ticket-8505c73d)
- Fix llm-generated-code issues (ticket-70f349c0)
- Fix relative-imports issues (ticket-6ba97fc3)
- Fix magic-numbers issues (ticket-618fbb85)
- Fix llm-generated-code issues (ticket-d6deb1a8)
- Fix llm-generated-code issues (ticket-143f5f36)
- Fix relative-imports issues (ticket-6790085a)
- Fix magic-numbers issues (ticket-199c6bd2)
- Fix llm-generated-code issues (ticket-a5a9f92b)
- Fix relative-imports issues (ticket-a13254b8)
- Fix relative-imports issues (ticket-173ed083)
- Fix string-concat issues (ticket-b3a2881c)
- Fix unused-imports issues (ticket-7832d2a1)
- Fix duplicate-imports issues (ticket-ac5773ec)
- Fix smart-return-type issues (ticket-ffff0750)
- Fix duplicate-imports issues (ticket-9cfce62b)
- Fix magic-numbers issues (ticket-9fae4ec0)
- Fix smart-return-type issues (ticket-24e36212)
- Fix relative-imports issues (ticket-092fe5c3)
- Fix duplicate-imports issues (ticket-28ea3db1)
- Fix smart-return-type issues (ticket-4a3846ab)
- Fix duplicate-imports issues (ticket-ce157c5e)
- Fix magic-numbers issues (ticket-1617f838)
- Fix relative-imports issues (ticket-4d6cc601)
- Fix string-concat issues (ticket-097ed693)
- Fix duplicate-imports issues (ticket-0f5ca70a)
- Fix relative-imports issues (ticket-66f1db01)
- Fix string-concat issues (ticket-8057661f)

### Fixed
- Remove `--asyncio-mode=auto` from pytest configuration for compatibility with older pytest-asyncio versions used by `goal -a`

- feat(goal): configuration management system
- feat(goal): code analysis engine / intelligent analysis pipeline
- feat(goal): CLI interface improvements and output/markdown support
- feat(goal): improved commit message generation
- fix: TODO batch fixes
- refactor(goal): multi-language support and configuration refactors
- docs(docs): update README and documentation for configuration management and markdown output
- chore(goal): update CLI docs and tests

## [2.1.197] - 2026-04-26

### Docs
- Update README.md

## [2.1.196] - 2026-04-25

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md

### Other
- Update .taskill/state.json

## [2.1.195] - 2026-04-24

### Docs
- Update README.md

## [2.1.194] - 2026-04-24

### Docs
- Update README.md

## [2.1.193] - 2026-04-24

### Docs
- Update README.md

## [2.1.192] - 2026-04-24

### Docs
- Update README.md

## [2.1.191] - 2026-04-24

### Docs
- Update README.md
- Update redsl_refactor_plan.md
- Update redsl_refactor_report.md

### Test
- Update tests/test_file_validation.py

### Other
- Update .redsl/history.jsonl
- Update planfile.yaml
- Update redsl_refactor_plan.toon.yaml
- Update redsl_refactor_report.toon.yaml

## [2.1.190] - 2026-04-20

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update redsl_refactor_plan.md
- Update redsl_refactor_report.md

### Other
- Update .gitignore
- Update .redsl/history.jsonl
- Update SUMR.json
- Update goal/cli.py.bak
- Update goal/commit_generator.py.bak
- Update goal/enhanced_summary.py.bak
- Update planfile.yaml
- Update redsl.yaml
- Update redsl_refactor_plan.toon.yaml
- Update redsl_refactor_report.toon.yaml
- ... and 1 more files

## [2.1.189] - 2026-04-19

### Docs
- Update README.md

### Test
- Update tests/test_version_sync.py

## [2.1.188] - 2026-04-19

### Docs
- Update README.md

### Other
- Update Taskfile.yml

## [2.1.187] - 2026-04-19

### Docs
- Update README.md

## [2.1.186] - 2026-04-09

### Docs
- Update README.md

## [2.1.185] - 2026-04-09

### Docs
- Update README.md

## [2.1.184] - 2026-04-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 4 more files

## [2.1.183] - 2026-04-09

### Docs
- Update README.md

## [2.1.182] - 2026-04-09

### Docs
- Update README.md

## [2.1.181] - 2026-04-09

### Docs
- Update README.md

### Other
- Update goal/cli.py.bak
- Update goal/commit_generator.py.bak

## [2.1.180] - 2026-04-08

### Docs
- Update README.md

## [2.1.179] - 2026-04-08

### Docs
- Update README.md

### Other
- Update .aider/caches/model_prices_and_context_window.json
- Update .aider/caches/openrouter_models.json
- Update goal/cli.py.bak
- Update goal/commit_generator.py.bak
- Update goal/enhanced_summary.py.bak

## [2.1.178] - 2026-04-08

### Docs
- Update README.md

### Test
- Update tests/test_push_e2e.py

## [0.1.10] - 2026-04-07

### Fixed
- Fix string-concat issues (ticket-8057661f)
- Fix wildcard-imports issues (ticket-055e3416)
- Fix string-concat issues (ticket-f0741dec)
- Fix wildcard-imports issues (ticket-bbe82c9b)

## [2.1.177] - 2026-04-01

### Docs
- Update README.md

## [2.1.176] - 2026-03-31

### Docs
- Update README.md

### Other
- Update project/validation.toon.yaml

## [2.1.175] - 2026-03-31

### Docs
- Update README.md
- Update REFACTOR_PLAN.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 6 more files

## [2.1.174] - 2026-03-31

### Docs
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Test
- Update tests/test_project_bootstrap.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/validation.toon.yaml

## [2.1.173] - 2026-03-31

### Docs
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 3 more files

## [2.1.172] - 2026-03-31

### Docs
- Update README.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_project_bootstrap.py
- Update tests/test_push_e2e.py

### Other
- Update project/analysis.toon.yaml
- Update project/validation.toon.yaml

## [2.1.171] - 2026-03-30

### Test
- Update tests/test_push_e2e.py

## [2.1.170] - 2026-03-30

### Docs
- Update TODO.md

### Test
- Update tests/test_push_e2e.py

### Other
- Update .gitignore
- Update Taskfile.yml
- Update pyqual.yaml

## [2.1.169] - 2026-03-30

### Test
- Update tests/test_push_e2e.py

## [2.1.168] - 2026-03-30

### Docs
- Update TODO.md

## [2.1.167] - 2026-03-30

### Docs
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 3 more files

## [2.1.166] - 2026-03-30

### Docs
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_push_e2e.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- ... and 2 more files

## [2.1.165] - 2026-03-29

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_project_bootstrap.py
- Update tests/test_push_e2e.py
- Update tests/test_version_sync.py

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [0.1.10] - 2026-03-29

### Fixed
- Fix string-concat issues (ticket-9f353b29)
- Fix llm-generated-code issues (ticket-2bc855c2)
- Fix smart-return-type issues (ticket-cb167f51)
- Fix duplicate-imports issues (ticket-9009a38a)
- Fix llm-generated-code issues (ticket-bbf26324)

## [2.1.164] - 2026-03-29

## [2.1.163] - 2026-03-29

### Test
- Update tests/test_project_bootstrap.py

## [2.1.162] - 2026-03-29

### Test
- Update tests/test_project_bootstrap.py

## [2.1.161] - 2026-03-29

## [2.1.160] - 2026-03-29

## [2.1.159] - 2026-03-29

### Docs
- Update examples/testing/README.md

### Other
- Update examples/run_all_examples.py
- Update examples/testing/01_duplicate_call_detection.py
- Update examples/testing/02_project_detection_tests.py

## [2.1.158] - 2026-03-29

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [0.1.10] - 2026-03-29

### Fixed
- Fix smart-return-type issues (ticket-fead239f)
- Fix string-concat issues (ticket-26a7c4e2)
- Fix magic-numbers issues (ticket-5e7fd1ad)
- Fix ai-boilerplate issues (ticket-0c0b01c1)
- Fix smart-return-type issues (ticket-d8a5fd93)
- Fix string-concat issues (ticket-6ce598f4)
- Fix unused-imports issues (ticket-69da7e0f)
- Fix ai-boilerplate issues (ticket-b4a4f07a)
- Fix smart-return-type issues (ticket-3e3aeddf)
- Fix string-concat issues (ticket-b4c77793)
- Fix unused-imports issues (ticket-cd93bccd)
- Fix magic-numbers issues (ticket-b8748b1a)
- Fix ai-boilerplate issues (ticket-147a27ab)
- Fix smart-return-type issues (ticket-e4700044)
- Fix string-concat issues (ticket-c2e40204)
- Fix unused-imports issues (ticket-5fd9a508)
- Fix magic-numbers issues (ticket-5161efdb)
- Fix ai-boilerplate issues (ticket-54d70962)
- Fix smart-return-type issues (ticket-736906aa)
- Fix string-concat issues (ticket-e8219611)
- Fix ai-boilerplate issues (ticket-6fdc6e8c)
- Fix smart-return-type issues (ticket-c7eed05c)
- Fix magic-numbers issues (ticket-251af8ff)
- Fix ai-boilerplate issues (ticket-2f2b7a84)
- Fix smart-return-type issues (ticket-e9b9f418)
- Fix ai-boilerplate issues (ticket-905e7053)
- Fix smart-return-type issues (ticket-114501e4)
- Fix unused-imports issues (ticket-b70775c5)
- Fix duplicate-imports issues (ticket-56cf5f7d)
- Fix llm-generated-code issues (ticket-0aa571a3)
- Fix ai-boilerplate issues (ticket-ae5a7772)
- Fix smart-return-type issues (ticket-c4a4e677)
- Fix magic-numbers issues (ticket-6ef1ccc3)
- Fix ai-boilerplate issues (ticket-c808f292)
- Fix smart-return-type issues (ticket-44afdd03)
- Fix unused-imports issues (ticket-c4ea6b78)
- Fix ai-boilerplate issues (ticket-3a00d5f3)
- Fix smart-return-type issues (ticket-9cfd9d22)
- Fix string-concat issues (ticket-474c8384)
- Fix magic-numbers issues (ticket-86634dce)
- Fix llm-generated-code issues (ticket-ac153a97)
- Fix ai-boilerplate issues (ticket-9376b731)
- Fix smart-return-type issues (ticket-74f626fa)
- Fix string-concat issues (ticket-e24f8933)
- Fix unused-imports issues (ticket-2bae89d4)
- Fix duplicate-imports issues (ticket-7839b691)
- Fix ai-boilerplate issues (ticket-d1683d0d)
- Fix smart-return-type issues (ticket-45fe8f2a)
- Fix string-concat issues (ticket-494249c6)
- Fix duplicate-imports issues (ticket-1047a7cd)
- Fix ai-boilerplate issues (ticket-66acbce1)
- Fix smart-return-type issues (ticket-a112c847)
- Fix string-concat issues (ticket-a64e0ed4)
- Fix unused-imports issues (ticket-f0016308)
- Fix duplicate-imports issues (ticket-8be42d9d)
- Fix ai-boilerplate issues (ticket-c90887b4)
- Fix smart-return-type issues (ticket-f6719cf0)
- Fix string-concat issues (ticket-51d3cb91)
- Fix duplicate-imports issues (ticket-d449e6b7)
- Fix magic-numbers issues (ticket-ef24defc)
- Fix ai-boilerplate issues (ticket-22ab3397)
- Fix smart-return-type issues (ticket-5fa9baf8)
- Fix string-concat issues (ticket-162db73c)
- Fix magic-numbers issues (ticket-4b8132ef)
- Fix ai-boilerplate issues (ticket-fc757004)
- Fix smart-return-type issues (ticket-4311914f)
- Fix string-concat issues (ticket-0cd1498e)
- Fix unused-imports issues (ticket-e9f8b389)
- Fix ai-boilerplate issues (ticket-5fb6f214)
- Fix smart-return-type issues (ticket-9a9f1285)
- Fix string-concat issues (ticket-0ea4b57d)
- Fix ai-boilerplate issues (ticket-ade3d464)
- Fix smart-return-type issues (ticket-8c6049ff)
- Fix string-concat issues (ticket-70bde475)
- Fix ai-boilerplate issues (ticket-520bc420)
- Fix smart-return-type issues (ticket-585fa109)
- Fix string-concat issues (ticket-53069f77)
- Fix unused-imports issues (ticket-8367cc7d)
- Fix ai-boilerplate issues (ticket-e51c67a5)
- Fix smart-return-type issues (ticket-956564dd)
- Fix magic-numbers issues (ticket-6babf634)
- Fix ai-boilerplate issues (ticket-99b1bd9a)
- Fix smart-return-type issues (ticket-9fa46c37)
- Fix magic-numbers issues (ticket-0add6e1d)
- Fix ai-boilerplate issues (ticket-a2957074)

## [2.1.157] - 2026-03-29

### Docs
- Update examples/README.md
- Update examples/api-usage/README.md
- Update examples/testing/README.md
- Update examples/validation/README.md

### Other
- Update .pre-commit-config.yaml
- Update Taskfile.yml
- Update examples/api-usage/test_integration.py
- Update examples/run_all_examples.py
- Update examples/testing/01_duplicate_call_detection.py
- Update examples/testing/02_project_detection_tests.py
- Update examples/testing/03_advanced_mocking.py
- Update examples/testing/04_debugging_diagnostics.py
- Update examples/validation/run_all_validation.py
- Update examples/validation/test_api_signatures.py
- ... and 4 more files

## [2.1.156] - 2026-03-29

## [2.1.155] - 2026-03-29

## [2.1.154] - 2026-03-29

## [2.1.153] - 2026-03-29

### Other
- Update examples/template-generator/generate.py

## [2.1.152] - 2026-03-29

### Docs
- Update README.md

### Other
- Update VERSION
- Update examples/my-new-project/goal.yaml
- Update examples/my-new-project/pyproject.toml
- Update examples/my-new-project/src/my-new-project/__init__.py
- Update examples/my-new-project/tests/test_my-new-project.py
- Update examples/template-generator/generate.py

## [2.1.150] - 2026-03-29

### Other
- Update examples/api-usage/05_programmatic_workflow.py
- Update examples/custom-hooks/pre-commit.py

## [2.1.149] - 2026-03-29

### Docs
- Update examples/README.md
- Update examples/advanced-workflows/README.md
- Update examples/advanced-workflows/feature-branch.md
- Update examples/advanced-workflows/hotfix-workflow.md
- Update examples/api-usage/README.md
- Update examples/configurations/goal-yaml-examples.md
- Update examples/custom-hooks/README.md
- Update examples/docker-integration/README.md
- Update examples/dotnet-project/README.md
- Update examples/gitlab-ci/README.md
- ... and 9 more files

### Test
- Update tests/test_project_bootstrap.py

### Other
- Update examples/api-usage/01_basic_api.py
- Update examples/api-usage/02_git_operations.py
- Update examples/api-usage/03_commit_generation.py
- Update examples/api-usage/04_version_validation.py
- Update examples/api-usage/05_programmatic_workflow.py
- Update examples/api-usage/test_integration.py
- Update examples/custom-hooks/post-commit.py
- Update examples/custom-hooks/pre-commit.py
- Update examples/custom-hooks/pre-publish.py
- Update examples/dotnet-project/Calculator.cs
- ... and 13 more files

## [2.1.148] - 2026-03-29

### Test
- Update tests/test_file_validation.py

## [2.1.147] - 2026-03-29

## [2.1.146] - 2026-03-29

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [0.1.10] - 2026-03-29

### Fixed
- Fix smart-return-type issues (ticket-ffff0750)
- Fix magic-numbers issues (ticket-9fae4ec0)
- Fix magic-numbers issues (ticket-95201114)

## [2.1.145] - 2026-03-29

## [2.1.144] - 2026-03-29

## [2.1.143] - 2026-03-29

## [2.1.142] - 2026-03-29

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [0.1.10] - 2026-03-29

### Fixed
- Fix string-concat issues (ticket-ad8108d5)

## [2.1.141] - 2026-03-29

## [2.1.140] - 2026-03-29

## [2.1.139] - 2026-03-29

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [0.1.10] - 2026-03-29

### Fixed
- Fix duplicate-imports issues (ticket-a4236fcf)

## [2.1.138] - 2026-03-29

### Docs
- Update README.md

## [2.1.137] - 2026-03-29

### Docs
- Update README.md

### Other
- Update .env.example

## [2.1.136] - 2026-03-29

## [2.1.135] - 2026-03-29

## [2.1.134] - 2026-03-29

## [2.1.133] - 2026-03-29

## [2.1.132] - 2026-03-29

## [2.1.131] - 2026-03-29

## [2.1.130] - 2026-03-29

### Docs
- Update README.md

## [2.1.129] - 2026-03-29

### Docs
- Update docs/integration-guide.md

## [2.1.128] - 2026-03-29

### Docs
- Update docs/integration-guide.md

## [2.1.127] - 2026-03-29

## [2.1.126] - 2026-03-29

## [2.1.125] - 2026-03-29

### Test
- Update tests/test_file_validation.py

## [2.1.124] - 2026-03-29

## [2.1.123] - 2026-03-29

## [2.1.122] - 2026-03-28

### Docs
- Update README.md

## [2.1.121] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Test
- Update tests/test_file_validation.py

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- ... and 2 more files

## [0.1.10] - 2026-03-27

### Fixed
- Fix string-concat issues (ticket-0d22f91b)
- Fix ai-boilerplate issues (ticket-41f077a4)

## [2.1.120] - 2026-03-27

### Docs
- Update TODO.md

## [2.1.119] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [0.1.10] - 2026-03-27

### Fixed
- Fix wildcard-imports issues (ticket-955e5aaa)

## [2.1.118] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [0.1.10] - 2026-03-27

### Fixed
- Fix relative-imports issues (ticket-1747b620)
- Fix relative-imports issues (ticket-e37ef835)
- Fix relative-imports issues (ticket-a1a7a963)
- Fix unused-imports issues (ticket-3ac4ebd1)

## [2.1.117] - 2026-03-27

### Docs
- Update TODO.md
- Update docs/README.md

### Other
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/project.toon.yaml
- Update project/validation.toon.yaml

## [2.1.116] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- ... and 2 more files

## [0.1.10] - 2026-03-27

### Fixed
- Fix wildcard-imports issues (ticket-09656430)

## [0.1.10] - 2026-03-27

### Fixed
- Fix wildcard-imports issues (ticket-0f634339)
- Fix wildcard-imports issues (ticket-0d8f6000)
- Fix wildcard-imports issues (ticket-212c0467)
- Fix wildcard-imports issues (ticket-0fd418e6)

## [2.1.115] - 2026-03-27

## [2.1.114] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update planfile.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [0.1.10] - 2026-03-27

### Fixed
- Fix relative-imports issues (ticket-6ffdf184)
- Fix print-statements issues (ticket-fb4fae09)
- Fix print-statements issues (ticket-4a334ca3)
- Fix ai-boilerplate issues (ticket-5c7fe6eb)
- Fix print-statements issues (ticket-7d2a0e14)
- Fix print-statements issues (ticket-f9de5882)
- Fix string-concat issues (ticket-ffd86490)
- Fix unused-imports issues (ticket-e315126b)
- Fix magic-numbers issues (ticket-72e063c1)
- Fix llm-generated-code issues (ticket-3d5d23ae)
- Fix print-statements issues (ticket-460ea50e)
- Fix string-concat issues (ticket-72013e0b)
- Fix llm-generated-code issues (ticket-c67d7dc6)
- Fix print-statements issues (ticket-5bead0fc)
- Fix smart-return-type issues (ticket-a40b03bb)
- Fix string-concat issues (ticket-d4e3e5d9)
- Fix unused-imports issues (ticket-1b7ef2a4)
- Fix llm-generated-code issues (ticket-6f238a23)
- Fix relative-imports issues (ticket-d891f624)
- Fix print-statements issues (ticket-82a8673d)
- Fix smart-return-type issues (ticket-2022028b)
- Fix string-concat issues (ticket-a5066b7f)
- Fix unused-imports issues (ticket-1fb93116)
- Fix print-statements issues (ticket-61dda27e)
- Fix smart-return-type issues (ticket-13ffec07)
- Fix unused-imports issues (ticket-ef720f39)
- Fix relative-imports issues (ticket-a12b43b4)
- Fix print-statements issues (ticket-809d1304)
- Fix smart-return-type issues (ticket-bfe2ab0a)
- Fix unused-imports issues (ticket-be1f1542)
- Fix duplicate-imports issues (ticket-d10de0d4)
- Fix print-statements issues (ticket-84802f76)
- Fix smart-return-type issues (ticket-bf75c893)
- Fix unused-imports issues (ticket-601d874a)
- Fix print-statements issues (ticket-eea71bb1)
- Fix smart-return-type issues (ticket-410d680a)
- Fix unused-imports issues (ticket-272a13b0)
- Fix print-statements issues (ticket-d44c3967)
- Fix smart-return-type issues (ticket-4212e6a6)
- Fix string-concat issues (ticket-87216eaa)
- Fix unused-imports issues (ticket-00086e06)
- Fix print-statements issues (ticket-7424fa3c)
- Fix smart-return-type issues (ticket-ca4c165d)
- Fix unused-imports issues (ticket-5f2126a0)
- Fix print-statements issues (ticket-ce03eae2)
- Fix smart-return-type issues (ticket-9a8ae60f)
- Fix magic-numbers issues (ticket-00e007c1)
- Fix print-statements issues (ticket-ec97d874)
- Fix unused-imports issues (ticket-ce5810c4)
- Fix print-statements issues (ticket-19571bcc)
- Fix smart-return-type issues (ticket-b22d8681)
- Fix unused-imports issues (ticket-a8853187)
- Fix magic-numbers issues (ticket-4f93f900)
- Fix print-statements issues (ticket-00ed9d66)
- Fix smart-return-type issues (ticket-c1b48756)
- Fix print-statements issues (ticket-ce835184)
- Fix smart-return-type issues (ticket-914eccfa)
- Fix unused-imports issues (ticket-cd5ecddc)
- Fix print-statements issues (ticket-41ca0841)
- Fix unused-imports issues (ticket-284869f1)
- Fix magic-numbers issues (ticket-c3bd2359)
- Fix print-statements issues (ticket-62dd271e)
- Fix smart-return-type issues (ticket-119c70f9)
- Fix unused-imports issues (ticket-c1c11986)
- Fix print-statements issues (ticket-43a71e74)
- Fix smart-return-type issues (ticket-9f4e98ca)
- Fix unused-imports issues (ticket-8dc64013)
- Fix print-statements issues (ticket-bd579d50)
- Fix smart-return-type issues (ticket-e091c738)
- Fix unused-imports issues (ticket-9e71cd0f)
- Fix magic-numbers issues (ticket-9e509799)
- Fix print-statements issues (ticket-f870133f)
- Fix smart-return-type issues (ticket-3b1139b9)
- Fix unused-imports issues (ticket-7148b685)
- Fix magic-numbers issues (ticket-88530c76)
- Fix ai-boilerplate issues (ticket-2a97e91c)
- Fix print-statements issues (ticket-3209296c)
- Fix string-concat issues (ticket-f173cf94)
- Fix unused-imports issues (ticket-ec962bc0)
- Fix ai-boilerplate issues (ticket-666bf566)
- Fix relative-imports issues (ticket-7c4d2f99)
- Fix print-statements issues (ticket-d48b0aac)
- Fix smart-return-type issues (ticket-11009c46)
- Fix unused-imports issues (ticket-9b87cae3)
- Fix ai-boilerplate issues (ticket-fb55a8a3)
- Fix print-statements issues (ticket-50dd0eeb)
- Fix ai-boilerplate issues (ticket-80bb797e)
- Fix relative-imports issues (ticket-adf2e12c)
- Fix print-statements issues (ticket-ee8922ab)
- Fix print-statements issues (ticket-83c35252)
- Fix magic-numbers issues (ticket-a5d61a36)
- Fix print-statements issues (ticket-cb9bcb97)
- Fix unused-imports issues (ticket-3c3f1cc1)
- Fix duplicate-imports issues (ticket-60fb35fd)
- Fix llm-generated-code issues (ticket-cf3d98ea)
- Fix print-statements issues (ticket-786f8532)
- Fix smart-return-type issues (ticket-1b552216)
- Fix string-concat issues (ticket-6d2226bf)
- Fix unused-imports issues (ticket-8cd7632d)
- Fix duplicate-imports issues (ticket-3ab472e5)
- Fix llm-generated-code issues (ticket-cf8b12e8)
- Fix print-statements issues (ticket-232312a3)
- Fix relative-imports issues (ticket-e9d90a2e)
- Fix print-statements issues (ticket-0c162f0b)
- Fix unused-imports issues (ticket-d9982610)
- Fix print-statements issues (ticket-180b30e8)
- Fix string-concat issues (ticket-9506b597)
- Fix print-statements issues (ticket-bbe9ad89)
- Fix string-concat issues (ticket-17d0f4e6)
- Fix print-statements issues (ticket-e3a83324)
- Fix string-concat issues (ticket-5fba8c04)
- Fix llm-generated-code issues (ticket-a3061483)
- Fix print-statements issues (ticket-4c85bc7b)
- Fix relative-imports issues (ticket-5722901a)
- Fix print-statements issues (ticket-e590f640)
- Fix print-statements issues (ticket-0e2d4efb)
- Fix print-statements issues (ticket-c999f721)
- Fix print-statements issues (ticket-74d5093b)
- Fix print-statements issues (ticket-122d1163)
- Fix string-concat issues (ticket-bb82a72c)
- Fix print-statements issues (ticket-9f4e7e36)
- Fix string-concat issues (ticket-7e3d16e7)
- Fix unused-imports issues (ticket-3622aebc)
- Fix print-statements issues (ticket-f685f5ed)
- Fix print-statements issues (ticket-9d80e5cd)
- Fix relative-imports issues (ticket-c1b28cdb)
- Fix print-statements issues (ticket-83d5d946)
- Fix string-concat issues (ticket-eda9fce4)
- Fix magic-numbers issues (ticket-8cce5e66)
- Fix llm-generated-code issues (ticket-5ca0239f)
- Fix print-statements issues (ticket-f0a0ba82)
- Fix relative-imports issues (ticket-60238f99)
- Fix print-statements issues (ticket-caac81ad)
- Fix print-statements issues (ticket-5328f140)
- Fix smart-return-type issues (ticket-c02ed288)
- Fix string-concat issues (ticket-d248eb58)
- Fix magic-numbers issues (ticket-c49c4576)
- Fix llm-generated-code issues (ticket-c1674106)
- Fix print-statements issues (ticket-6c143b7b)
- Fix smart-return-type issues (ticket-b338f68e)
- Fix string-concat issues (ticket-65ea4331)
- Fix unused-imports issues (ticket-eb83b6f3)
- Fix duplicate-imports issues (ticket-31168e84)
- Fix magic-numbers issues (ticket-e8323fdc)
- Fix print-statements issues (ticket-7eb7032a)
- Fix string-concat issues (ticket-db256d03)
- Fix unused-imports issues (ticket-1f931f99)
- Fix print-statements issues (ticket-a39351d1)
- Fix smart-return-type issues (ticket-afc71edf)
- Fix relative-imports issues (ticket-b8770605)
- Fix print-statements issues (ticket-e7fb8677)
- Fix print-statements issues (ticket-2622d72a)
- Fix llm-generated-code issues (ticket-99a82c71)
- Fix print-statements issues (ticket-d4b9f057)
- Fix smart-return-type issues (ticket-31f7a7f8)
- Fix string-concat issues (ticket-c85170fb)
- Fix magic-numbers issues (ticket-eed103c2)
- Fix llm-generated-code issues (ticket-c4b45d93)
- Fix relative-imports issues (ticket-f80ace05)
- Fix print-statements issues (ticket-23ed9134)
- Fix relative-imports issues (ticket-87658dfc)
- Fix print-statements issues (ticket-bb97423d)
- Fix unused-imports issues (ticket-6ee04de8)
- Fix magic-numbers issues (ticket-6250f32c)
- Fix llm-generated-code issues (ticket-652b2b88)
- Fix ai-boilerplate issues (ticket-8648f1d9)
- Fix print-statements issues (ticket-2e3eaa37)
- Fix llm-generated-code issues (ticket-70f349c0)
- Fix relative-imports issues (ticket-69bfa343)
- Fix print-statements issues (ticket-c86d57c8)
- Fix unused-imports issues (ticket-4ec04772)
- Fix llm-generated-code issues (ticket-a3bcc668)
- Fix ai-boilerplate issues (ticket-8505c73d)
- Fix relative-imports issues (ticket-6ba97fc3)
- Fix print-statements issues (ticket-b2c32774)
- Fix print-statements issues (ticket-46b22761)
- Fix unused-imports issues (ticket-4ea3cf5e)
- Fix llm-generated-code issues (ticket-143f5f36)
- Fix print-statements issues (ticket-c1c0a4b3)
- Fix unused-imports issues (ticket-5cb6865b)
- Fix magic-numbers issues (ticket-618fbb85)
- Fix llm-generated-code issues (ticket-d6deb1a8)
- Fix relative-imports issues (ticket-6790085a)
- Fix print-statements issues (ticket-992471b3)
- Fix unused-imports issues (ticket-1b1bef5d)
- Fix magic-numbers issues (ticket-199c6bd2)
- Fix llm-generated-code issues (ticket-a5a9f92b)
- Fix print-statements issues (ticket-af72453b)
- Fix print-statements issues (ticket-68dd969d)
- Fix unused-imports issues (ticket-b02a6284)
- Fix duplicate-imports issues (ticket-9cfce62b)
- Fix relative-imports issues (ticket-a13254b8)
- Fix print-statements issues (ticket-ca726ca5)
- Fix relative-imports issues (ticket-173ed083)
- Fix print-statements issues (ticket-629c4ff3)
- Fix print-statements issues (ticket-f4cb8795)
- Fix print-statements issues (ticket-74151b5d)
- Fix smart-return-type issues (ticket-2c88c6f9)
- Fix string-concat issues (ticket-b3a2881c)
- Fix unused-imports issues (ticket-7832d2a1)
- Fix duplicate-imports issues (ticket-ac5773ec)
- Fix print-statements issues (ticket-840d99b8)
- Fix smart-return-type issues (ticket-24e36212)
- Fix unused-imports issues (ticket-7fe63a75)
- Fix print-statements issues (ticket-0d47cbb0)
- Fix print-statements issues (ticket-171ad054)
- Fix print-statements issues (ticket-95729f08)
- Fix string-concat issues (ticket-378c753e)
- Fix unused-imports issues (ticket-f879c566)
- Fix print-statements issues (ticket-ce04190f)
- Fix unused-imports issues (ticket-f4e81bf7)
- Fix duplicate-imports issues (ticket-7cf307fe)
- Fix relative-imports issues (ticket-092fe5c3)
- Fix print-statements issues (ticket-ca3d10ab)
- Fix string-concat issues (ticket-5d8862c0)
- Fix relative-imports issues (ticket-4d6cc601)
- Fix print-statements issues (ticket-923fc425)
- Fix print-statements issues (ticket-6d91ef65)
- Fix print-statements issues (ticket-6e5f61fa)
- Fix string-concat issues (ticket-097ed693)
- Fix unused-imports issues (ticket-811c3d28)
- Fix duplicate-imports issues (ticket-0f5ca70a)
- Fix print-statements issues (ticket-e9fcfcd3)
- Fix relative-imports issues (ticket-4b53f031)
- Fix print-statements issues (ticket-72b758d6)
- Fix relative-imports issues (ticket-30ba74d6)
- Fix print-statements issues (ticket-c020cd32)
- Fix string-concat issues (ticket-8b623ae1)
- Fix unused-imports issues (ticket-a3a21506)
- Fix relative-imports issues (ticket-ff7823b1)
- Fix print-statements issues (ticket-a1d3592f)
- Fix string-concat issues (ticket-605bec28)
- Fix unused-imports issues (ticket-99429564)
- Fix magic-numbers issues (ticket-f6082379)
- Fix print-statements issues (ticket-79f05589)
- Fix string-concat issues (ticket-4557135b)
- Fix unused-imports issues (ticket-593ef56a)
- Fix print-statements issues (ticket-17562314)
- Fix relative-imports issues (ticket-6d6c9e90)
- Fix print-statements issues (ticket-1953334b)
- Fix smart-return-type issues (ticket-6096eb84)
- Fix llm-generated-code issues (ticket-940e5c7c)
- Fix print-statements issues (ticket-757a8e2f)
- Fix smart-return-type issues (ticket-d2da0c8f)
- Fix string-concat issues (ticket-43dfe792)
- Fix unused-imports issues (ticket-19f56c0c)
- Fix print-statements issues (ticket-14b4ee97)
- Fix string-concat issues (ticket-0112eec7)
- Fix magic-numbers issues (ticket-f1b4a5bb)
- Fix llm-generated-code issues (ticket-33f459d8)
- Fix print-statements issues (ticket-02c0d1c6)
- Fix string-concat issues (ticket-0c21b88b)
- Fix magic-numbers issues (ticket-1aa11f1f)
- Fix llm-generated-code issues (ticket-a7b76e0b)
- Fix print-statements issues (ticket-4020834b)
- Fix magic-numbers issues (ticket-75578b6f)
- Fix llm-generated-code issues (ticket-1b76da8b)
- Fix print-statements issues (ticket-0865a624)
- Fix smart-return-type issues (ticket-3dba36d9)
- Fix magic-numbers issues (ticket-ee284663)
- Fix llm-generated-code issues (ticket-97d6145b)
- Fix relative-imports issues (ticket-b6a414ec)
- Fix print-statements issues (ticket-a3a29ee3)
- Fix relative-imports issues (ticket-917cc8ea)
- Fix print-statements issues (ticket-a3e28a21)
- Fix relative-imports issues (ticket-655ccacb)
- Fix print-statements issues (ticket-2372b592)
- Fix unused-imports issues (ticket-898b096f)
- Fix magic-numbers issues (ticket-35d21e44)
- Fix llm-generated-code issues (ticket-87f3bca7)
- Fix print-statements issues (ticket-ba1e82f0)
- Fix string-concat issues (ticket-aaebb933)
- Fix unused-imports issues (ticket-d510ce52)
- Fix llm-generated-code issues (ticket-4bc2d83c)
- Fix print-statements issues (ticket-9b0c9513)
- Fix string-concat issues (ticket-168cf976)
- Fix duplicate-imports issues (ticket-f1c01cce)
- Fix llm-generated-code issues (ticket-0fbdaa3e)
- Fix print-statements issues (ticket-29f8a179)
- Fix smart-return-type issues (ticket-9a59492d)
- Fix string-concat issues (ticket-f9cafcd0)
- Fix ai-boilerplate issues (ticket-00048bac)
- Fix duplicate-imports issues (ticket-a2e0eb1e)
- Fix print-statements issues (ticket-f65c027e)
- Fix llm-generated-code issues (ticket-73483bbd)

## [2.1.113] - 2026-03-27

### Docs
- Update CHANGELOG.md

## [2.3.0] - 2026-03-27

### Added
- **Pre-commit hooks integration** (v2.3.x feature)
  - New `goal hooks` command for managing pre-commit hooks
  - `goal hooks install` - Install Goal validation hooks
  - `goal hooks uninstall` - Remove Goal validation hooks  
  - `goal hooks run` - Run hooks manually on demand
  - `goal hooks status` - Check hooks installation status
  - Integrates with existing file validation (size, tokens, dot folders)
  - Creates `.pre-commit-config.yaml` with Goal validation hook
  - Automatic pre-commit package installation

- **Post-commit actions** (v2.3.x feature)
  - New `goal postcommit` command for managing post-commit actions
  - `goal postcommit run` - Execute configured actions after commit
  - `goal postcommit list` - Show configured actions
  - `goal postcommit validate` - Validate action configuration
  - `goal postcommit info` - Show available action types
  - Available actions:
    - Notification (desktop notifications)
    - Webhook (HTTP POST requests)
    - Script (custom shell scripts)
    - Git push (automatic pushing)
  - Configure via `goal.yaml` under `post_commit:` section

- **Custom validation rules** (v2.3.x feature)
  - New `goal validation` command for managing custom rules
  - `goal validation run` - Execute all configured validation rules
  - `goal validation list` - Show configured rules
  - `goal validation validate` - Validate rule configurations
  - `goal validation info` - Show available rule types
  - Available rule types:
    - `message_pattern` - Regex pattern matching for commit messages
    - `file_pattern` - File pattern validation (min/max count, forbidden patterns)
    - `script` - Custom validation scripts
    - `commit_size` - Commit size limits (lines/files)
    - `message_length` - Commit message length validation
  - Configure via `goal.yaml` under `validation_rules:` section

### Changed
- Started v2.3.x development with pre-commit hooks and post-commit actions

## [2.1.112] - 2026-03-27

## [2.1.111] - 2026-03-27

## [2.1.110] - 2026-03-27

## [2.1.109] - 2026-03-27

### Docs
- Update README.md

### Other
- Update .gitignore

## [2.1.108] - 2026-03-27

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/commands.md
- Update docs/user-config.md
- Update examples/license-management/README.md
- Update examples/multi-author/README.md
- Update examples/wizard-setup/README.md

### Other
- Update .gitignore

## [2.2.0] - 2026-03-27

### Added
- **goal wizard** command - Interactive guided setup for new projects
  - Git repository initialization and remote configuration
  - User configuration (name, email, license)
  - Project configuration (name, description, versioning strategy)
  - Complete setup summary

- **goal license** command - Comprehensive license management
  - Create and update LICENSE files with 8 common license templates
  - Custom license template support
  - SPDX license ID validation
  - License compatibility checking
  - Automatic template variable substitution ({year}, {fullname})

- **goal authors** command - Multi-author project support
  - Add, remove, update project authors
  - Import authors from git history
  - Export to CONTRIBUTORS.md
  - Find authors by name, email, or alias

- **Co-author support** in commit messages
  - `--co-author` flag for `goal commit` command
  - Automatic formatting of co-author trailers
  - Support for multiple co-authors

### Changed
- Improved error messages with actionable suggestions
- Enhanced subprocess error handling in git operations
- Updated commit command to support co-author attribution

### Fixed
- Removed outdated build-system issue from TODO.md
- Fixed import error in license module (missing Tuple type hint)

### Docs
- Updated TODO.md with v2.2.0 completion status
- Added documentation for new commands (will be updated in docs/)

## [2.1.107] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/README.md

### Test
- Update test_large_file_auto.py
- Update test_path_extraction.py

### Other
- Update debug_recovery.py
- Update project/duplication.toon.yaml
- Update project/index.html
- Update project/project.toon.yaml
- Update project/prompt.txt
- Update project/validation.toon.yaml

## [2.1.106] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update test_path_extraction.py

### Other
- Update debug_recovery.py
- Update planfile.yaml
- Update prefact.yaml
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 6 more files

## [2.1.105] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/context.md

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml
- ... and 1 more files

## [2.1.104] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 3 more files

## [2.1.103] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/context.md

### Test
- Update test_large_file_auto.py

### Other
- Update project.sh
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- ... and 2 more files

## [2.1.102] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- ... and 2 more files

## [2.1.101] - 2026-03-27

### Docs
- Update docs/README.md
- Update project/context.md

### Test
- Update test_recovery.py

### Other
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- Update project/map.toon.yaml
- Update project/project.toon.yaml

## [2.1.100] - 2026-03-27

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update claude-taking-longer-than-usual.webm
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/index.html
- ... and 3 more files

## [2.1.99] - 2026-03-27

### Docs
- Update README.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update project/analysis.toon
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/evolution.toon.yaml
- Update project/flow.mmd
- Update project/flow.png
- Update project/flow.toon
- ... and 6 more files

## [2.1.98] - 2026-03-25

## [2.1.97] - 2026-03-25

### Other
- Update Makefile

## [2.1.96] - 2026-03-15

## [2.1.95] - 2026-03-08

### Docs
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_project_doctor.py

### Other
- Update project.sh
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/flow.mmd
- Update project/flow.png
- ... and 5 more files

## [2.1.94] - 2026-03-07

## [2.1.93] - 2026-03-07

## [2.1.92] - 2026-03-07

## [2.1.91] - 2026-03-07

## [2.1.90] - 2026-03-07

## [2.1.89] - 2026-03-07

## [2.1.88] - 2026-03-07

## [2.1.87] - 2026-03-07

## [2.1.86] - 2026-03-07

## [2.1.85] - 2026-03-07

## [2.1.84] - 2026-03-07

### Docs
- Update README.md

### Other
- Update VERSION

## [2.1.81] - 2026-03-07

## [2.1.80] - 2026-03-07

## [2.1.79] - 2026-03-07

### Docs
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_version_validation.py

### Other
- Update project.sh
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/flow.mmd
- Update project/flow.png
- ... and 4 more files

## [2.1.78] - 2026-03-05

### Test
- Update tests/test_version_sync.py

## [2.1.77] - 2026-03-05

## [2.1.76] - 2026-03-05

## [2.1.75] - 2026-03-05

## [2.1.74] - 2026-03-05

## [2.1.73] - 2026-03-05

### Test
- Update tests/test_cli_options.py
- Update tests/test_clone_repo.py
- Update tests/test_project_bootstrap.py
- Update tests/test_project_doctor.py

## [2.1.72] - 2026-03-05

### Docs
- Update project/README.md
- Update project/context.md

### Other
- Update project.sh
- Update project/analysis.toon
- Update project/dashboard.html
- Update project/evolution.toon
- Update project/project.toon
- Update project/project.yaml
- Update project/prompt.txt

## [2.1.71] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.70] - 2026-02-24

### Summary

refactor(goal): intelligent code analysis pipeline

### Docs

- docs: update README

### Other

- update goal-2.1.68/LICENSE
- update goal-2.1.68/PKG-INFO
- update goal-2.1.68/goal/__init__.py
- update goal-2.1.68/goal/__main__.py
- update goal-2.1.68/goal/cli.py
- update goal-2.1.68/goal/commit_generator.py
- update goal-2.1.68/goal/config.py
- update goal-2.1.68/goal/deep_analyzer.py
- update goal-2.1.68/goal/enhanced_summary.py
- update goal-2.1.68/goal/formatter.py
- ... and 14 more


## [2.1.69] - 2026-02-24

### Summary

refactor(goal): intelligent code analysis pipeline

### Core

- update goal/cli.py

### Docs

- docs: update README

### Other

- update goal-2.1.68/LICENSE
- update goal-2.1.68/PKG-INFO
- update goal-2.1.68/goal/__init__.py
- update goal-2.1.68/goal/__main__.py
- update goal-2.1.68/goal/cli.py
- update goal-2.1.68/goal/commit_generator.py
- update goal-2.1.68/goal/config.py
- update goal-2.1.68/goal/deep_analyzer.py
- update goal-2.1.68/goal/enhanced_summary.py
- update goal-2.1.68/goal/formatter.py
- ... and 14 more


## [2.1.68] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py

### Docs

- docs: update README


## [2.1.67] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py

### Docs

- docs: update README


## [2.1.66] - 2026-02-24

### Added
- **CLI shortcuts**: Added `-t` flag as shorthand for `--todo` in both `goal` and `goal doctor` commands
- **Version shortcut**: Added `-v` flag as shorthand for `--version` command
- **Full workflow TODO tracking**: `goal -a -t` now runs complete workflow with automatic issue tracking
- **Doctor phase integration**: TODO tracking integrated into main push workflow when `-t/--todo` is used

### Improved
- **User experience**: Shorter commands for common TODO tracking workflows
- **Documentation**: Updated examples and command reference with new flags
- **Workflow integration**: Seamless TODO tracking during full automation

### Examples
```bash
# Quick version check
goal -v

# Quick TODO tracking with full automation
goal -a -t

# Doctor with TODO tracking (short form)
goal doctor -t

# Full workflow with TODO tracking
goal --all --todo
```

### Docs

- docs: update README


## [2.1.65] - 2026-02-24

### Added
- **TODO Management**: `goal doctor --todo` automatically adds detected issues to TODO.md
- **Unique ticket IDs**: Generate `[CODE-identifier]` format for issue tracking
- **Duplicate prevention**: Checks existing tickets before adding new ones
- **Rich formatting**: Severity icons, file references, and timestamps in TODO entries

### Fixed
- **Publishing error**: Fixed "cannot access local variable 'Path'" in publish_project
- **Artifact handling**: Proper initialization of artifacts variable
- **Python path**: Use sys.executable instead of hardcoded 'python' command
- **Authentication**: Better support for ~/.pypirc configuration files

### Improved
- **Documentation**: Updated publishing guide with ~/.pypirc instructions
- **Error messages**: More descriptive error reporting for publishing failures
- **Build process**: More reliable artifact detection and cleanup

### Examples
```bash
# Diagnose and track issues
goal doctor --todo

# Full workflow with reliable publishing
goal --all

# Check project health
goal doctor
```

### Core

- update goal/cli.py


## [2.1.64] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.63] - 2026-02-24

### Summary

docs(docs): configuration management system

### Docs

- docs: update TODO.md


## [2.1.62] - 2026-02-24

### Summary

fix(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/project_doctor.py


## [2.1.61] - 2026-02-24

### Summary

feat(docs): configuration management system

### Docs

- docs: update README

### Config

- config: update goal.yaml


## [2.1.60] - 2026-02-22

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.59] - 2026-02-22

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/package_managers.py


## [2.1.58] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.57] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.56] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.55] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/config.py


## [2.1.54] - 2026-02-16

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.53] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.52] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.51] - 2026-02-16

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.50] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.49] - 2026-02-16

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/enhanced_summary.py
- update goal/git_ops.py

### Docs

- docs: update README
- docs: update TODO.md

### Test

- update tests/test_clone_repo.py
- update tests/test_version_sync.py


## [2.1.46] - 2026-02-16

### Summary

feat(goal): interactive git workflow and verbose logging

### New Features

- **Interactive Git Setup**: New 4-option menu when no git repo is found:
  1. Initialize & connect to remote (keeps local files)
  2. Clone existing repo
  3. Initialize local-only repo
  4. Exit
- **Verbose Logging**: All git commands are now echoed to the console (`→ git ...`) for full transparency.
- **Remote Configuration**: New `ensure_remote()` flow helps configure upstream if missing.
- **Version Sync**: Now updates `__version__` in `__init__.py` files (excluding venvs/build dirs).
- **Auto Mode**: `goal -a/--all` now gracefully skips interactive prompts in non-git directories (exit code 1).

### Core

- add `goal/git_ops.py` - Extract git operations into dedicated module.
- update `goal/cli.py` - Major refactor of `ensure_git_repository` and git command execution.
- update `pyproject.toml` - Bump version to 2.1.46.

### Test

- update `tests/test_clone_repo.py` - Add tests for new interactive options and auto mode.
- update `tests/test_cli_options.py` - Verify unknown command handling.


## [2.1.45] - 2026-02-16

### Summary

fix(goal): configuration management system

### Core

- update goal/enhanced_summary.py

### Test

- update tests/test_project_doctor.py


## [2.1.44] - 2026-02-16

### Summary

fix(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/project_bootstrap.py
- update goal/project_doctor.py


## [2.1.43] - 2026-02-16

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py

### Test

- update tests/test_project_bootstrap.py


## [2.1.37] - 2026-02-16

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py

### Test

- update tests/test_clone_repo.py

### Build

- update pyproject.toml


## [2.1.35] - 2026-02-15

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py

### Build

- update pyproject.toml


## [2.1.34] - 2026-02-15

### Summary

feat(docs): configuration management system

### Docs

- docs: update README
- docs: update TODO.md
- docs: update commands.md
- docs: update enhanced-summary.md

### Other

- update project.functions.toon
- scripts: update project.sh
- update project.toon-schema.json


## [2.1.33] - 2026-02-15

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/enhanced_summary.py


## [2.1.33] - 2026-02-15

### Summary

feat(goal): version validation and registry checking

### Added

- **Version validation system** (`goal/version_validation.py`) - Validates version consistency across project files
- **Registry version checking** - Checks PyPI, npm, crates.io, RubyGems for published versions
- **README badge validation** - Verifies and updates version badges in README.md
- **`goal check-versions` command** - Manual version validation with `--update-badges` flag
- **Auto-validation in publish** - Warns about version mismatches before publishing

### Changed

- **Commit message format** - Changed from ASCII tree to valid YAML structure
- **CLI improvements** - Better `--all` mode feedback with "🤖 AUTO" indicators

### Core

- Add `goal/version_validation.py` - Registry API integration and badge management
- Update `goal/cli.py` - Integrate version validation into publish workflow
- Update `goal/enhanced_summary.py` - YAML format for commit messages

### Test

- Add `test_version_validation.py` - Comprehensive test suite for validation


## [2.1.32] - 2026-02-15

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.31] - 2026-02-15

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/enhanced_summary.py


## [2.1.30] - 2026-02-15

### Summary

feat(tests): deep code analysis engine with 3 supporting modules

### Test

- update test_version_validation.py


## [2.1.29] - 2026-02-15

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/version_validation.py

### Test

- update test_version_validation.py


## [2.1.28] - 2026-02-15

### Summary

docs(docs): configuration management system

### Docs

- docs: update TODO.md
- docs: update README
- docs: update commands.md
- docs: update user-config.md


## [2.1.27] - 2026-02-15

### Summary

refactor(goal): CLI interface improvements

### Core

- update goal/cli.py
- update goal/user_config.py

### Docs

- docs: update README


## [2.1.27] - 2026-02-15

### Summary

feat(core): user configuration and smart metadata management system

### Added

- **User configuration system** (`~/.goal`) - Stores git author info and license preferences
- **Auto-detection** of git `user.name` and `user.email` on first run
- **Interactive license selection** - 8 popular open source licenses (Apache-2.0, MIT, GPL-3.0, etc.)
- **Smart author management** - Adds authors to projects instead of replacing them
- **Automatic README updates** - Updates license badges, License section, and Author section
- **Multi-file metadata sync** - Updates pyproject.toml, package.json, Cargo.toml with user info
- **`goal config` command** - View and manage user configuration

### Core

- Add `goal/user_config.py` - User configuration management module
- Update `goal/cli.py` - Integrate user config initialization and metadata updates
- Add `update_project_metadata()` - Smart author and license updates for project files
- Add `update_readme_metadata()` - Automatic README.md badge and section updates
- Enhance `sync_all_versions()` - Now updates version, authors, and license together

### Docs

- Update README.md with User Configuration section
- Add comprehensive examples of configuration workflow
- Document smart author management behavior

### Build

- Update pyproject.toml with new author and license from user config

## [2.1.26] - 2026-02-15

### Summary

feat(docs): configuration management system

### Docs

- docs: update README

### Build

- update pyproject.toml


## [2.1.23] - 2026-01-30

### Summary

feat(core): add database, testing and more

### Core

- update goal/cli.py


## [2.1.22] - 2026-01-30

### Summary

test(core): add auth, logging and more

### Core

- update goal/cli.py


## [2.1.21] - 2026-01-30

### Summary

feat(core): add Make support

### Core

- update goal/cli.py


## [2.1.20] - 2026-01-29

### Summary

feat(other): add Make support

### Other

- build: update Makefile


## [2.1.19] - 2026-01-29

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py

### Other

- docker: update Dockerfile
- scripts: update run_matrix.sh


## [2.1.18] - 2026-01-29

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.17] - 2026-01-29

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.16] - 2026-01-29

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.15] - 2026-01-29

### Summary

feat(goal): CLI interface improvements

### Core

- update goal/cli.py


## [2.1.14] - 2026-01-29

### Summary

refactor(goal): commit message generator

### Core

- update goal/cli.py
- update goal/commit_generator.py
- update goal/enhanced_summary.py


## [2.1.13] - 2026-01-29

### Summary

feat(goal): commit message generator

### Core

- update goal/cli.py
- update goal/commit_generator.py


## [2.1.12] - 2026-01-29

### Summary

feat(core): add auth, formatting, api

### Core

- update goal/cli.py
- update goal/commit_generator.py
- update goal/config.py
- update goal/enhanced_summary.py


## [2.1.11] - 2026-01-29

### Summary

feat(core): add cli, logging and more

### Core

- update goal/enhanced_summary.py


## [2.1.10] - 2026-01-29

### Summary

feat(core): add formatting, cli and more

### Core

- update goal/enhanced_summary.py


## [2.1.9] - 2026-01-29

### Summary

refactor(core): add logging, configuration and more

### Core

- update goal/enhanced_summary.py


## [2.1.8] - 2026-01-29

### Summary

fix(core): add database, api, auth

### Core

- update goal/cli.py
- update goal/enhanced_summary.py


## [2.1.7] - 2026-01-29

### Summary

fix(core): add formatting, cli and more

### Core

- update goal/commit_generator.py


## [2.1.6] - 2026-01-29

### Summary

feat(core): add logging, api and more

### Core

- update goal/enhanced_summary.py


## [2.1.5] - 2026-01-29

### Summary

test(core): improved test coverage

### Core

- update goal/__init__.py
- update goal/cli.py
- update goal/formatter.py
- update goal/smart_commit.py

### Docs

- docs: update README

### Build

- update pyproject.toml


## [2.1.3] - 2026-01-29

### Summary

feat(goal): add markdown output and commit messages

### Changes

- update goal/cli.py
- update goal/commit_generator.py
- update goal/config.py
- update goal/smart_commit.py

## [2.1.2] - 2026-01-29

### Summary

docs(docs): add markdown output and commit messages

### Changes

- docs: update README
- docs: update README
- docs: update ci-cd.md
- docs: update commands.md
- docs: update configuration.md
- docs: update examples.md
- docs: update faq.md
- docs: update hooks.md
- docs: update installation.md
- docs: update markdown-output-guide.md
- docs: update quickstart.md
- docs: update registries.md
- docs: update strategies.md
- docs: update troubleshooting.md
- docs: update usage.md

## [2.1.1] - 2026-01-29

### Summary

feat(goal): add markdown output and commit messages

### Changes

- docs: update README
- config: update goal.yaml
- update goal/__init__.py
- update goal/cli.py
- update goal/config.py
- update pyproject.toml

## [2.1.0] - 2026-01-29

### Summary

feat(goal): add YAML configuration support with goal.yaml

### Added

- **goal.yaml configuration file** - Full project configuration via YAML
- **Auto-detection** - Automatic project type, name, and version file detection
- **Config commands** - `goal config show/get/set/validate/update`
- **Custom config path** - `goal --config custom.yaml` support
- **Strategies** - Configurable test/build/publish per project type
- **Registries** - Registry configuration with token environment variables
- **Hooks** - Pre/post commit and push hooks configuration
- **Version sync** - Configurable version file synchronization

### Changed

- `goal init` now creates goal.yaml with auto-detected settings
- Added `--config` / `-c` option to main command
- Added `--force` option to `goal init` for regenerating config

### Dependencies

- Added PyYAML>=6.0 as core dependency

## [2.0.5] - 2026-01-29

### Summary

fix(goal): update 5 files (+22/-5)

### Changes

- update goal/__init__.py
- update goal/cli.py
- update pyproject.toml

## [2.0.4] - 2026-01-29

### Summary

test(tests): update pyproject.toml, test_cli_options.py

### Changes

- update pyproject.toml
- update tests/test_cli_options.py

## [1.0.1] - 2026-01-29

- docs: update README
- update pyproject.toml

