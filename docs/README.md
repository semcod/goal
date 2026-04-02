<!-- code2docs:start --># goal

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.8-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-733-green)
> **733** functions | **64** classes | **130** files | CC̄ = 4.8

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/wronai/goal](https://github.com/wronai/goal)

## Installation

### From PyPI

```bash
pip install goal
```

### From Source

```bash
git clone https://github.com/wronai/goal
cd goal
pip install -e .
```

### Optional Extras

```bash
pip install goal[nfo]    # nfo features
pip install goal[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
goal ./my-project

# Only regenerate README
goal ./my-project --readme-only

# Preview what would be generated (no file writes)
goal ./my-project --dry-run

# Check documentation health
goal check ./my-project

# Sync — regenerate only changed modules
goal sync ./my-project
```

### Python API

```python
from goal import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `goal`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `goal.yaml` in your project root (or run `goal init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

goal can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- goal:start -->
# Project Title
... auto-generated content ...
<!-- goal:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
goal/
    ├── markdown-demo├── project        ├── Calculator            ├── my-new-project/        ├── discord-webhook        ├── post-commit        ├── install        ├── slack-webhook        ├── main        ├── pre-commit        ├── pre-publish        ├── 05_programmatic_workflow        ├── 04_version_validation        ├── 03_commit_generation        ├── 01_basic_api            ├── Example                            ├── Main        ├── 02_git_operations    ├── config/    ├── enhanced_summary        ├── generate        ├── run_all_validation    ├── toml_validation    ├── cli/    ├── commit_generator    ├── changelog    ├── version_validation    ├── user_config├── goal/    ├── __main__    ├── smart_commit/    ├── formatter    ├── deep_analyzer    ├── project_bootstrap    ├── project_doctor    ├── git_ops    ├── generator/        ├── generator        ├── config        ├── analyzer    ├── hooks/        ├── git_ops        ├── exceptions    ├── validators/        ├── manager        ├── gitignore        ├── dot_folders        ├── tokens        ├── file_validator        ├── exceptions        ├── base        ├── strategies        ├── large_file        ├── auth        ├── lfs    ├── recovery/        ├── force_push        ├── corrupted        ├── manager    ├── push/        ├── commands        ├── divergent            ├── version            ├── changelog            ├── dry_run            ├── tag        ├── stages/            ├── commit            ├── publish        ├── core        ├── version_sync        ├── version        ├── recover_cmd        ├── hooks_cmd        ├── config_validate_cmd            ├── push_remote        ├── license_cmd        ├── doctor_cmd        ├── authors_cmd        ├── postcommit_cmd        ├── commit_cmd        ├── utils_cmd        ├── version_utils        ├── wizard_cmd        ├── version_types        ├── publish        ├── validation_cmd        ├── publish_cmd        ├── push_cmd        ├── config_cmd        ├── manager    ├── postcommit/        ├── actions        ├── manager        ├── constants        ├── validation        ├── validator    ├── summary/        ├── generator        ├── manager    ├── validation/    ├── package_managers        ├── rust        ├── ruby        ├── quality_filter        ├── rules        ├── dotnet    ├── doctor/        ├── go        ├── todo        ├── logging        ├── php        ├── python        ├── java        ├── abstraction        ├── generator        ├── manager    ├── authors/        ├── utils        ├── manager        ├── spdx    ├── license/    ├── run_docker_matrix    ├── run_matrix        ├── models        ├── nodejs        ├── core```

## API Overview

### Classes

- **`Calculator`** — —
- **`Program`** — —
- **`Example`** — —
- **`Main`** — —
- **`ValidationRunner`** — Runs all validation tests and aggregates results.
- **`UserConfig`** — Manages user-specific configuration stored in ~/.goal
- **`MarkdownFormatter`** — Formats Goal output as structured markdown for LLM consumption.
- **`CodeChangeAnalyzer`** — Analyzes code changes to extract functional meaning.
- **`CommitMessageGenerator`** — Generate conventional commit messages using diff analysis and lightweight classification.
- **`ChangeAnalyzer`** — Analyze git changes to classify type, detect scope, and extract functions.
- **`ContentAnalyzer`** — Analyze content for short summaries and per-file notes.
- **`GitDiffOperations`** — Git diff operations with caching.
- **`ValidationError`** — Base validation error.
- **`FileSizeError`** — Error for files exceeding size limit.
- **`TokenDetectedError`** — Error when API tokens are detected in files.
- **`DotFolderError`** — Error when dot folders are detected that should be in .gitignore.
- **`HooksManager`** — Manages pre-commit hooks for Goal.
- **`RecoveryError`** — Base exception for all recovery operations.
- **`AuthError`** — Raised when authentication fails.
- **`LargeFileError`** — Raised when large files block the push.
- **`DivergentHistoryError`** — Raised when local and remote histories have diverged.
- **`CorruptedObjectError`** — Raised when git objects are corrupted.
- **`LFSIssueError`** — Raised when Git LFS has issues.
- **`RollbackError`** — Raised when rollback operation fails.
- **`NetworkError`** — Raised when network connectivity issues occur.
- **`QuotaExceededError`** — Raised when GitHub API quota is exceeded.
- **`RecoveryStrategy`** — Base class for all recovery strategies.
- **`LargeFileStrategy`** — Handles large file errors.
- **`AuthErrorStrategy`** — Handles authentication errors.
- **`LFSIssueStrategy`** — Handles Git LFS issues.
- **`ForcePushStrategy`** — Handles force push recovery scenarios.
- **`CorruptedObjectStrategy`** — Handles corrupted git objects.
- **`RecoveryManager`** — Manages the recovery process for failed git pushes.
- **`DivergentHistoryStrategy`** — Handles divergent history errors.
- **`PushContext`** — Context object wrapper for push command.
- **`PostCommitManager`** — Manages post-commit actions for Goal.
- **`PostCommitAction`** — Base class for post-commit actions.
- **`NotificationAction`** — Send desktop notification after commit.
- **`WebhookAction`** — Send webhook POST request after commit.
- **`ScriptAction`** — Run custom script after commit.
- **`GitPushAction`** — Automatically push after commit.
- **`GoalConfig`** — Manages goal.yaml configuration file.
- **`ConfigValidationError`** — Error raised when configuration validation fails.
- **`ConfigValidator`** — Validates Goal configuration files.
- **`QualityValidator`** — Validate commit summary against quality gates.
- **`EnhancedSummaryGenerator`** — Generate business-value focused commit summaries.
- **`ValidationRuleManager`** — Manages custom validation rules for Goal.
- **`PackageManager`** — Package manager configuration and capabilities.
- **`SummaryQualityFilter`** — Filter noise and improve summary quality.
- **`ValidationRule`** — Base class for custom validation rules.
- **`MessagePatternRule`** — Validate commit message against pattern.
- **`FilePatternRule`** — Validate files against pattern rules.
- **`ScriptRule`** — Run custom validation script.
- **`CommitSizeRule`** — Validate commit size (lines changed).
- **`MessageLengthRule`** — Validate commit message length.
- **`GoalGroup`** — Custom Click Group that shows docs URL for unknown commands (like Poetry),
- **`PythonDiagnostics`** — Container for Python diagnostic checks with shared state.
- **`CodeAbstraction`** — Extracts meaningful abstractions from code changes.
- **`SmartCommitGenerator`** — Generates smart commit messages using code abstraction.
- **`AuthorsManager`** — Manages project authors and team members.
- **`LicenseManager`** — Manages license operations including template handling and file creation.
- **`App`** — —
- **`Issue`** — A single diagnosed issue.
- **`DoctorReport`** — Aggregated report from a doctor run.

### Functions

- `send_discord_notification(message, commit_info)` — Send notification to Discord.
- `main()` — CLI entry point.
- `get_commit_info()` — Get information about the last commit.
- `notify_slack(info)` — Send Slack notification.
- `update_changelog(info)` — Auto-update changelog with commit info.
- `log_to_file(info)` — Log commit to local file.
- `main()` — Run post-commit actions.
- `send_slack_notification(message, commit_info)` — Send notification to Slack.
- `main()` — CLI entry point.
- `main()` — —
- `check_secrets()` — Check for potential secrets in staged files.
- `check_file_sizes(max_size_mb)` — Check that no file exceeds size limit.
- `run_tests()` — Run quick tests before commit.
- `main()` — Run all pre-commit checks.
- `test_build()` — Test that package builds correctly.
- `test_install()` — Test package installation in clean environment.
- `check_version()` — Verify version is not already published.
- `run_security_check()` — Run security checks on package.
- `main()` — Run all pre-publish checks.
- `run_custom_workflow()` — Run a custom push workflow.
- `create_minimal_workflow()` — Create a minimal workflow example.
- `main()` — Demonstrate version validation.
- `main()` — Demonstrate commit message generation.
- `main()` — Run basic API examples.
- `main()` — Demonstrate git operations.
- `generate_project(template_type, project_name)` — Generate project from template.
- `main()` — CLI entry point.
- `main()` — Run all validations.
- `get_tomllib()` — Get the best available TOML library.
- `validate_toml_file(filepath)` — Validate a TOML file and return helpful error message if invalid.
- `validate_project_toml_files(project_dir)` — Validate all common TOML files in a project.
- `check_pyproject_toml()` — Quick check for pyproject.toml validity.
- `update_changelog(version, files, commit_msg, config)` — Update CHANGELOG.md with new version and changes.
- `get_pypi_version(package_name)` — Get latest version of a package from PyPI.
- `get_npm_version(package_name)` — Get latest version of a package from npm registry.
- `get_cargo_version(package_name)` — Get latest version of a crate from crates.io.
- `get_rubygems_version(package_name)` — Get latest version of a gem from RubyGems.
- `get_registry_version(registry, package_name)` — Get latest version from specified registry.
- `extract_badge_versions(readme_path)` — Extract version badges from README.md.
- `update_badge_versions(readme_path, new_version)` — Update version badges in README.md to new version.
- `validate_project_versions(project_types, current_version)` — Validate versions across different registries.
- `check_readme_badges(current_version)` — Check if README badges are up to date with current version.
- `format_validation_results(results)` — Format validation results for display.
- `get_git_user_name()` — Get git user.name from git config.
- `get_git_user_email()` — Get git user.email from git config.
- `prompt_for_license()` — Interactive prompt for license selection.
- `initialize_user_config(force)` — Initialize user configuration interactively if not already done.
- `get_user_config()` — Get user configuration, initializing if necessary.
- `show_user_config()` — Display current user configuration.
- `format_push_result(project_types, files, stats, current_version)` — Format push command result as markdown.
- `format_enhanced_summary(commit_title, commit_body, capabilities, roles)` — Format enhanced business-value summary as markdown.
- `format_status_output(version, branch, staged_files, unstaged_files)` — Format status command output as markdown.
- `detect_project_types_deep(root, max_depth)` — Detect project types in *root* and up to *max_depth* subfolder levels.
- `guess_package_name(project_dir, project_type)` — Best-effort guess of the package/module name for scaffold templates.
- `ensure_project_environment(project_dir, project_type, yes)` — Ensure the project environment is properly set up.
- `find_existing_tests(project_dir, project_type)` — Find existing test files for the given project type.
- `scaffold_test(project_dir, project_type, yes)` — Create a sample test file if no tests exist.
- `bootstrap_project(project_dir, project_type, yes)` — Full bootstrap: diagnose & fix config, ensure environment, scaffold tests.
- `bootstrap_all_projects(root, yes)` — Detect all project types (root + 1-level subfolders) and bootstrap each.
- `run_git()` — Run a git command and return the result.
- `run_command(command, capture)` — Run a shell command and return the result.
- `run_git_with_status()` — Run git command with enhanced status display.
- `run_command_tee(command)` — —
- `is_git_repository()` — Check if the current directory is inside a git repository.
- `validate_repo_url(url)` — Validate that a URL looks like a git repository (HTTP/HTTPS/SSH/file).
- `get_remote_url(remote)` — Get the URL of a named remote, or None.
- `list_remotes()` — Return list of (name, url) for all configured remotes.
- `get_remote_branch()` — Get the current branch name.
- `clone_repository(url, target_dir)` — Clone a git repository from a URL.
- `ensure_git_repository(auto)` — Check for a git repo; if missing, interactively offer options.
- `ensure_remote(auto)` — Ensure a git remote is configured. Offers interactive setup if missing.
- `get_staged_files()` — Get list of staged files.
- `get_unstaged_files()` — Get list of unstaged/untracked files.
- `get_working_tree_files()` — Get list of files changed in working tree (unstaged + untracked).
- `get_diff_stats(cached)` — Get additions/deletions per file.
- `get_diff_content(cached, max_lines)` — Get the actual diff content for analysis.
- `read_ticket(path)` — Read TICKET configuration file (key=value).
- `apply_ticket_prefix(title, ticket)` — Apply ticket prefix (from CLI or TICKET file) to commit title.
- `generate_smart_commit_message(cached)` — Generate a smart commit message.
- `get_hook_config(project_dir)` — Get hook configuration.
- `create_precommit_config(project_dir, include_goal)` — Create .pre-commit-config.yaml content.
- `install_hooks(project_dir, force)` — Install Goal pre-commit hooks.
- `uninstall_hooks(project_dir)` — Uninstall Goal pre-commit hooks.
- `run_hooks(project_dir, all_files)` — Run pre-commit hooks manually.
- `load_gitignore(gitignore_path)` — Load .gitignore patterns, returning (ignored_patterns, whitelisted_patterns).
- `save_gitignore(ignored, gitignore_path)` — Save patterns to .gitignore.
- `check_dot_folders(files, config)` — Check for dot folders/files that should be in .gitignore.
- `manage_dot_folders(files, config, dry_run)` — Proactively manage dot folders in .gitignore.
- `detect_tokens_in_content(content, patterns)` — Detect tokens in file content using regex patterns with entropy filtering.
- `get_default_token_patterns()` — Return default regex patterns for token detection.
- `get_file_size_mb(file_path)` — Get file size in megabytes.
- `validate_files(files, max_size_mb, block_large_files, token_patterns)` — Validate files before commit.
- `handle_large_files(large_files)` — Automatically handle large files by adding them to .gitignore and unstaging.
- `validate_staged_files(config)` — Validate staged files using configuration.
- `push(ctx, bump, no_tag, no_changelog)` — Add, commit, tag, and push changes to remote.
- `sync_all_versions_wrapper(new_version, user_config)` — Wrapper to sync versions to all project files.
- `handle_version_sync(new_version, no_version_sync, user_config, yes)` — Sync versions to all project files.
- `get_version_info(current_version, bump)` — Get current and new version info.
- `handle_changelog(new_version, files, commit_msg, config)` — Update changelog.
- `update_changelog_stage(new_version, files, commit_msg, config)` — Stage for updating changelog without git add.
- `handle_dry_run(ctx_obj, project_types, files, stats)` — Handle dry run output.
- `create_tag(new_version, no_tag)` — Create git tag for release.
- `get_commit_message(ctx_obj, files, diff_content, message)` — Generate or use provided commit message.
- `enforce_quality_gates(ctx_obj, commit_msg, detailed_result, files)` — Enforce commit quality gates for auto-generated messages.
- `handle_single_commit(commit_title, commit_body, commit_msg, message)` — Handle single commit (non-split mode).
- `handle_split_commits(ctx_obj, files, ticket, new_version)` — Handle split commits per file group.
- `handle_publish(project_types, new_version, yes, no_publish)` — Publish to package registries.
- `run_git_local()` — Local wrapper for run_git to avoid import issues.
- `show_workflow_preview(files, stats, current_version, new_version)` — Show workflow preview for interactive mode.
- `output_final_summary(ctx_obj, markdown, project_types, files)` — Output final summary in markdown format if requested.
- `execute_push_workflow(ctx_obj, bump, no_tag, no_changelog)` — Execute the complete push workflow.
- `sync_all_versions(new_version, user_config)` — Update version, author, and license in all detected project files.
- `recover(ctx, full, error_file, error_message)` — Recover from git push failures.
- `hooks()` — Manage pre-commit hooks.
- `hooks_install(force)` — Install Goal pre-commit hooks.
- `hooks_uninstall()` — Uninstall Goal pre-commit hooks.
- `hooks_run(all_files)` — Run pre-commit hooks manually.
- `hooks_status()` — Show pre-commit hooks status.
- `validate_cmd(ctx, config, strict, fix)` — Validate goal.yaml configuration file.
- `push_to_remote(branch, tag_name, no_tag, yes)` — Push commits and tags to remote.
- `license()` — Manage project licenses.
- `license_create(license_id, fullname, year, force)` — Create a LICENSE file with the specified license.
- `license_update(license_id, fullname, year)` — Update existing LICENSE file.
- `license_validate()` — Validate the LICENSE file.
- `license_info(license_id)` — Show information about a license.
- `license_check(license1, license2)` — Check compatibility between two licenses.
- `license_list(custom)` — List available license templates.
- `license_template(license_id, file)` — Add or show custom license templates.
- `doctor(ctx, fix, path, todo)` — Diagnose and auto-fix common project configuration issues.
- `authors()` — Manage project authors and team members.
- `authors_list()` — List all project authors.
- `authors_add(name, email, role, alias)` — Add an author to the project.
- `authors_remove(email)` — Remove an author from the project.
- `authors_update(email, name, role, alias)` — Update an author's information.
- `authors_import()` — Import authors from git history.
- `authors_export()` — Export authors to CONTRIBUTORS.md.
- `authors_find(identifier)` — Find an author by name, email, or alias.
- `authors_co_author(name, email)` — Generate a co-author trailer for commit messages.
- `authors_current()` — Show current user's author information.
- `postcommit()` — Manage post-commit actions.
- `postcommit_run()` — Run configured post-commit actions.
- `postcommit_list()` — List configured post-commit actions.
- `postcommit_validate()` — Validate post-commit action configuration.
- `postcommit_info()` — Show information about available actions.
- `commit(ctx, detailed, unstaged, markdown)` — Generate a smart commit message for current changes.
- `fix_summary(ctx, fix, preview, cached)` — Auto-fix commit summary quality issues.
- `validate(ctx, fix, cached)` — Validate commit summary against quality gates.
- `status(ctx, markdown)` — Show current git status and version info.
- `init(ctx, force)` — Initialize goal in current repository (creates VERSION, CHANGELOG.md, and goal.yaml).
- `info()` — Show detailed project information and version status.
- `version(bump_type)` — Bump version and sync across all project files.
- `package_managers(language, available)` — Show detected and available package managers for the current project.
- `check_versions(update_badges)` — Check version consistency across registries and README badges.
- `clone(ctx, url, directory)` — Clone a git repository.
- `bootstrap(yes, path)` — Bootstrap project environments (install deps, scaffold tests).
- `detect_project_types()` — Detect what type(s) of project this is.
- `find_version_files()` — Find all version-containing files in the project.
- `get_version_from_file(filepath, pattern)` — Extract version from a file using regex pattern.
- `get_current_version()` — Get current version from VERSION file or project files.
- `bump_version(version, bump_type)` — Bump version according to semantic versioning.
- `update_version_in_file(filepath, pattern, old_version, new_version)` — Update version in a specific file.
- `update_json_version(filepath, new_version)` — Update version in JSON files (package.json, composer.json).
- `update_project_metadata(filepath, user_config)` — Update author and license in project files based on user config.
- `update_readme_metadata(user_config)` — Update README.md with author and license information.
- `wizard(reset, skip_git, skip_user, skip_project)` — Interactive wizard for complete Goal setup.
- `makefile_has_target(target)` — Check if Makefile has a specific target.
- `publish_project(project_types, version, yes, config)` — Publish project to appropriate package registries.
- `validation()` — Manage custom validation rules.
- `validation_run()` — Run custom validation rules.
- `validation_list()` — List configured validation rules.
- `validation_validate()` — Validate rule configurations.
- `validation_info()` — Show information about available validation rules.
- `publish(ctx, use_make, target, version_arg)` — Publish the current project (optionally using Makefile).
- `push(ctx, bump, no_tag, no_changelog)` — Add, commit, tag, and push changes to remote.
- `config()` — Manage goal configuration.
- `config_show(ctx, key)` — Show configuration value(s).
- `config_validate(ctx, strict, fix)` — Validate goal.yaml configuration.
- `config_update(ctx)` — Update configuration with latest defaults.
- `config_set(ctx, key, value)` — Set a configuration value.
- `config_get(ctx, key)` — Get a configuration value.
- `setup(reset, show_config)` — Setup goal configuration interactively.
- `run_post_commit_actions(project_dir)` — Run post-commit actions.
- `init_config(force)` — Initialize a new goal.yaml configuration file.
- `load_config(config_path)` — Load configuration from file or create default.
- `ensure_config(auto_update)` — Ensure configuration exists and is up-to-date.
- `validate_config_file(config_path, strict)` — Validate a goal.yaml configuration file.
- `validate_config_interactive(config_path)` — Interactively validate and optionally fix configuration.
- `generate_business_summary(files, diff_content, config)` — Convenience function to generate enhanced summary.
- `validate_summary(summary, files, config)` — Validate summary against quality gates.
- `auto_fix_summary(summary, files, config)` — Auto-fix summary issues and return corrected summary.
- `run_custom_validations(project_dir)` — Run custom validation rules.
- `detect_package_managers(project_path)` — Detect available package managers in the given project path.
- `get_package_manager(name)` — Get a specific package manager by name.
- `get_package_managers_by_language(language)` — Get all package managers for a specific language.
- `is_package_manager_available(pm)` — Check if a package manager is available in the system PATH.
- `get_available_package_managers(project_path)` — Get package managers that are both detected in the project and available on the system.
- `get_preferred_package_manager(project_path, language)` — Get the preferred package manager for a project.
- `format_package_manager_command(pm, command_type)` — Format a package manager command with the given parameters.
- `get_package_manager_info(pm)` — Get formatted information about a package manager.
- `list_all_package_managers()` — List all supported package managers with their information.
- `detect_project_language(project_path)` — Detect the primary language(s) of a project based on file extensions.
- `suggest_package_managers(project_path)` — Suggest package managers for a project based on detected languages and available tools.
- `diagnose_rust(project_dir, auto_fix)` — Run all Rust-specific diagnostics.
- `diagnose_ruby(project_dir, auto_fix)` — Run all Ruby-specific diagnostics.
- `diagnose_dotnet(project_dir, auto_fix)` — Run all .NET-specific diagnostics.
- `diagnose_go(project_dir, auto_fix)` — Run all Go-specific diagnostics.
- `add_issues_to_todo(project_dir, issues, todo_file)` — Add issues to TODO.md without duplicates.
- `diagnose_and_report_with_todo(project_dir, project_type, auto_fix, todo_file)` — Diagnose, fix, report, and optionally add issues to TODO.md.
- `diagnose_php(project_dir, auto_fix)` — Run all PHP-specific diagnostics.
- `strip_ansi(text)` — —
- `load_command_modules()` — Import Click command modules so they register against `main`.
- `split_paths_by_type(paths)` — Split file paths into groups (code/docs/ci/examples/other).
- `stage_paths(paths)` — —
- `confirm(prompt, default)` — Ask for user confirmation with Y/n prompt (Enter defaults to Yes).
- `main(ctx, bump, target_version, yes)` — Goal - Automated git push with smart commit messages.
- `diagnose_python(project_dir, auto_fix)` — Run all Python-specific diagnostics.
- `diagnose_java(project_dir, auto_fix)` — Run all Java-specific diagnostics.
- `create_smart_generator(config)` — Factory function to create SmartCommitGenerator.
- `get_project_authors(project_dir)` — Get all authors for a project.
- `add_project_author(name, email, role, alias)` — Add an author to a project.
- `format_co_author_trailer(name, email)` — Format a co-author trailer for git commit messages.
- `parse_co_authors(message)` — Parse co-author trailers from a commit message.
- `add_co_authors_to_message(message, co_authors)` — Add co-author trailers to a commit message.
- `remove_co_authors_from_message(message)` — Remove co-author trailers from a commit message.
- `validate_author_format(author_str)` — Validate and parse an author string.
- `deduplicate_co_authors(co_authors)` — Remove duplicate co-authors from list.
- `get_co_authors_from_command_line(co_author_args)` — Parse co-author arguments from command line.
- `format_commit_message_with_co_authors(title, body, co_authors)` — Format a complete commit message with co-authors.
- `extract_current_author_from_config()` — Extract current author from user config.
- `create_license_file(license_id, fullname, year, force)` — Convenience function to create a LICENSE file.
- `update_license_file(license_id, fullname, year)` — Convenience function to update a LICENSE file.
- `validate_spdx_id(license_id)` — Validate an SPDX license identifier.
- `get_license_info(license_id)` — Get detailed information about a license.
- `check_compatibility(license1, license2)` — Check basic license compatibility between two licenses.
- `get_compatible_licenses(license_id)` — Get a list of licenses compatible with the given license.
- `is_copyleft(license_id)` — Check if a license is copyleft.
- `is_permissive(license_id)` — Check if a license is permissive.
- `run_case()` — —
- `print()` — —
- `main()` — —
- `self()` — —
- `diagnose_nodejs(project_dir, auto_fix)` — Run all Node.js-specific diagnostics.
- `diagnose_project(project_dir, project_type, auto_fix)` — Run diagnostics for a single project directory.
- `diagnose_and_report(project_dir, project_type, auto_fix)` — Diagnose, fix, and print a human-readable report.


## Project Structure

📄 `examples.api-usage.01_basic_api` (1 functions)
📄 `examples.api-usage.02_git_operations` (1 functions)
📄 `examples.api-usage.03_commit_generation` (1 functions)
📄 `examples.api-usage.04_version_validation` (1 functions)
📄 `examples.api-usage.05_programmatic_workflow` (2 functions)
📄 `examples.custom-hooks.post-commit` (5 functions)
📄 `examples.custom-hooks.pre-commit` (4 functions)
📄 `examples.custom-hooks.pre-publish` (5 functions)
📄 `examples.dotnet-project.Calculator` (5 functions, 2 classes)
📄 `examples.git-hooks.install`
📄 `examples.go-project.main` (1 functions)
📄 `examples.java-project.src.main.java.com.example.Main` (2 functions, 1 classes)
📄 `examples.markdown-demo`
📦 `examples.my-new-project.src.my-new-project`
📄 `examples.php-project.src.Example` (1 functions, 1 classes)
📄 `examples.template-generator.generate` (2 functions)
📄 `examples.validation.run_all_validation` (5 functions, 1 classes)
📄 `examples.webhooks.discord-webhook` (2 functions)
📄 `examples.webhooks.slack-webhook` (2 functions)
📦 `goal`
📄 `goal.__main__`
📦 `goal.authors`
📄 `goal.authors.manager` (12 functions, 1 classes)
📄 `goal.authors.utils` (9 functions)
📄 `goal.changelog` (5 functions)
📦 `goal.cli` (10 functions, 1 classes)
📄 `goal.cli.authors_cmd` (10 functions)
📄 `goal.cli.commit_cmd` (5 functions)
📄 `goal.cli.config_cmd` (7 functions)
📄 `goal.cli.config_validate_cmd` (1 functions)
📄 `goal.cli.doctor_cmd` (1 functions)
📄 `goal.cli.hooks_cmd` (5 functions)
📄 `goal.cli.license_cmd` (8 functions)
📄 `goal.cli.postcommit_cmd` (5 functions)
📄 `goal.cli.publish` (8 functions)
📄 `goal.cli.publish_cmd` (2 functions)
📄 `goal.cli.push_cmd` (1 functions)
📄 `goal.cli.recover_cmd` (2 functions)
📄 `goal.cli.utils_cmd` (8 functions)
📄 `goal.cli.validation_cmd` (5 functions)
📄 `goal.cli.version`
📄 `goal.cli.version_sync` (9 functions)
📄 `goal.cli.version_types`
📄 `goal.cli.version_utils` (9 functions)
📄 `goal.cli.wizard_cmd` (7 functions)
📄 `goal.commit_generator`
📦 `goal.config`
📄 `goal.config.constants`
📄 `goal.config.manager` (25 functions, 1 classes)
📄 `goal.config.validation` (15 functions, 2 classes)
📄 `goal.deep_analyzer` (23 functions, 1 classes)
📦 `goal.doctor`
📄 `goal.doctor.core` (2 functions)
📄 `goal.doctor.dotnet` (1 functions)
📄 `goal.doctor.go` (1 functions)
📄 `goal.doctor.java` (1 functions)
📄 `goal.doctor.logging` (2 functions)
📄 `goal.doctor.models` (2 classes)
📄 `goal.doctor.nodejs` (1 functions)
📄 `goal.doctor.php` (1 functions)
📄 `goal.doctor.python` (17 functions, 1 classes)
📄 `goal.doctor.ruby` (1 functions)
📄 `goal.doctor.rust` (1 functions)
📄 `goal.doctor.todo` (5 functions)
📄 `goal.enhanced_summary`
📄 `goal.formatter` (17 functions, 1 classes)
📦 `goal.generator`
📄 `goal.generator.analyzer` (23 functions, 2 classes)
📄 `goal.generator.generator` (24 functions, 1 classes)
📄 `goal.generator.git_ops` (7 functions, 1 classes)
📄 `goal.git_ops` (28 functions)
📦 `goal.hooks`
📄 `goal.hooks.config` (2 functions)
📄 `goal.hooks.manager` (14 functions, 1 classes)
📦 `goal.license`
📄 `goal.license.manager` (10 functions, 1 classes)
📄 `goal.license.spdx` (7 functions)
📄 `goal.package_managers` (12 functions, 1 classes)
📦 `goal.postcommit`
📄 `goal.postcommit.actions` (16 functions, 5 classes)
📄 `goal.postcommit.manager` (7 functions, 1 classes)
📄 `goal.project_bootstrap` (33 functions)
📄 `goal.project_doctor`
📦 `goal.push`
📄 `goal.push.commands` (1 functions)
📄 `goal.push.core` (14 functions, 1 classes)
📦 `goal.push.stages`
📄 `goal.push.stages.changelog` (2 functions)
📄 `goal.push.stages.commit` (6 functions)
📄 `goal.push.stages.dry_run` (4 functions)
📄 `goal.push.stages.publish` (1 functions)
📄 `goal.push.stages.push_remote` (14 functions)
📄 `goal.push.stages.tag` (1 functions)
📄 `goal.push.stages.version` (4 functions)
📦 `goal.recovery`
📄 `goal.recovery.auth` (2 functions, 1 classes)
📄 `goal.recovery.base` (5 functions, 1 classes)
📄 `goal.recovery.corrupted` (2 functions, 1 classes)
📄 `goal.recovery.divergent` (6 functions, 1 classes)
📄 `goal.recovery.exceptions` (9 functions, 9 classes)
📄 `goal.recovery.force_push` (2 functions, 1 classes)
📄 `goal.recovery.large_file` (12 functions, 1 classes)
📄 `goal.recovery.lfs` (2 functions, 1 classes)
📄 `goal.recovery.manager` (14 functions, 1 classes)
📄 `goal.recovery.strategies`
📦 `goal.smart_commit`
📄 `goal.smart_commit.abstraction` (9 functions, 1 classes)
📄 `goal.smart_commit.generator` (22 functions, 1 classes)
📦 `goal.summary` (3 functions)
📄 `goal.summary.generator` (18 functions, 1 classes)
📄 `goal.summary.quality_filter` (16 functions, 1 classes)
📄 `goal.summary.validator` (13 functions, 1 classes)
📄 `goal.toml_validation` (4 functions)
📄 `goal.user_config` (12 functions, 1 classes)
📦 `goal.validation`
📄 `goal.validation.manager` (7 functions, 1 classes)
📄 `goal.validation.rules` (19 functions, 6 classes)
📦 `goal.validators`
📄 `goal.validators.dot_folders` (6 functions)
📄 `goal.validators.exceptions` (3 functions, 4 classes)
📄 `goal.validators.file_validator` (7 functions)
📄 `goal.validators.gitignore` (2 functions)
📄 `goal.validators.tokens` (7 functions)
📄 `goal.version_validation` (15 functions)
📄 `integration.run_docker_matrix`
📄 `integration.run_matrix` (4 functions, 1 classes)
📄 `project`

## Requirements

- Python >= >=3.8
- click >=8.0.0- PyYAML >=6.0- clickmd >=0.1.0- costs >=0.1.21

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/wronai/goal
cd goal

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/wronai/goal/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/wronai/goal/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/wronai/goal/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/wronai/goal/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->