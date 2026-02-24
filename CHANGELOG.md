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

