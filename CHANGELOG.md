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

