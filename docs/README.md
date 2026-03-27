<!-- code2docs:start --># goal

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.8-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-420-green)
> **420** functions | **41** classes | **75** files | CC̄ = 5.8

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
    ├── cli/    ├── enhanced_summary    ├── config/    ├── commit_generator    ├── changelog    ├── version_validation    ├── user_config├── goal/    ├── __main__    ├── smart_commit/    ├── project_bootstrap    ├── formatter    ├── project_doctor    ├── deep_analyzer    ├── git_ops    ├── generator/        ├── git_ops    ├── validators/        ├── analyzer        ├── exceptions        ├── generator        ├── file_validator    ├── recovery/        ├── commands    ├── push/        ├── manager        ├── recover_cmd        ├── core        ├── doctor_cmd        ├── strategies        ├── commit_cmd        ├── version        ├── utils_cmd        ├── publish_cmd        ├── push_cmd        ├── publish        ├── config_cmd        ├── constants        ├── manager        ├── validator    ├── summary/        ├── generator        ├── rust        ├── ruby        ├── quality_filter    ├── package_managers        ├── dotnet    ├── doctor/        ├── go        ├── todo        ├── logging        ├── php        ├── models        ├── java        ├── abstraction        ├── generator            ├── version            ├── changelog            ├── commit            ├── dry_run            ├── tag        ├── stages/            ├── push_remote            ├── publish├── project    ├── markdown-demo    ├── run_docker_matrix    ├── run_matrix        ├── install        ├── nodejs        ├── python        ├── core```

## API Overview

### Classes

- **`UserConfig`** — Manages user-specific configuration stored in ~/.goal
- **`MarkdownFormatter`** — Formats Goal output as structured markdown for LLM consumption.
- **`CodeChangeAnalyzer`** — Analyzes code changes to extract functional meaning.
- **`GitDiffOperations`** — Git diff operations with caching.
- **`ChangeAnalyzer`** — Analyze git changes to classify type, detect scope, and extract functions.
- **`ContentAnalyzer`** — Analyze content for short summaries and per-file notes.
- **`RecoveryError`** — Base exception for all recovery operations.
- **`AuthError`** — Raised when authentication fails.
- **`LargeFileError`** — Raised when large files block the push.
- **`DivergentHistoryError`** — Raised when local and remote histories have diverged.
- **`CorruptedObjectError`** — Raised when git objects are corrupted.
- **`LFSIssueError`** — Raised when Git LFS has issues.
- **`RollbackError`** — Raised when rollback operation fails.
- **`NetworkError`** — Raised when network connectivity issues occur.
- **`QuotaExceededError`** — Raised when GitHub API quota is exceeded.
- **`CommitMessageGenerator`** — Generate conventional commit messages using diff analysis and lightweight classification.
- **`ValidationError`** — Base validation error.
- **`FileSizeError`** — Error for files exceeding size limit.
- **`TokenDetectedError`** — Error when API tokens are detected in files.
- **`DotFolderError`** — Error when dot folders are detected that should be in .gitignore.
- **`RecoveryManager`** — Manages the recovery process for failed git pushes.
- **`PushContext`** — Context object wrapper for push command.
- **`RecoveryStrategy`** — Base class for all recovery strategies.
- **`AuthErrorStrategy`** — Handles authentication errors.
- **`LargeFileStrategy`** — Handles large file errors.
- **`DivergentHistoryStrategy`** — Handles divergent history errors.
- **`CorruptedObjectStrategy`** — Handles corrupted git objects.
- **`LFSIssueStrategy`** — Handles Git LFS issues.
- **`ForcePushStrategy`** — Handles force push recovery scenarios.
- **`GoalConfig`** — Manages goal.yaml configuration file.
- **`QualityValidator`** — Validate commit summary against quality gates.
- **`EnhancedSummaryGenerator`** — Generate business-value focused commit summaries.
- **`SummaryQualityFilter`** — Filter noise and improve summary quality.
- **`PackageManager`** — Package manager configuration and capabilities.
- **`GoalGroup`** — Custom Click Group that shows docs URL for unknown commands (like Poetry),
- **`Issue`** — A single diagnosed issue.
- **`DoctorReport`** — Aggregated report from a doctor run.
- **`CodeAbstraction`** — Extracts meaningful abstractions from code changes.
- **`SmartCommitGenerator`** — Generates smart commit messages using code abstraction.
- **`App`** — —
- **`PythonDiagnostics`** — Container for Python diagnostic checks with shared state.

### Functions

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
- `detect_project_types_deep(root, max_depth)` — Detect project types in *root* and up to *max_depth* subfolder levels.
- `guess_package_name(project_dir, project_type)` — Best-effort guess of the package/module name for scaffold templates.
- `ensure_project_environment(project_dir, project_type, yes)` — Ensure the project environment is properly set up.
- `find_existing_tests(project_dir, project_type)` — Find existing test files for the given project type.
- `scaffold_test(project_dir, project_type, yes)` — Create a sample test file if no tests exist.
- `bootstrap_project(project_dir, project_type, yes)` — Full bootstrap: diagnose & fix config, ensure environment, scaffold tests.
- `bootstrap_all_projects(root, yes)` — Detect all project types (root + 1-level subfolders) and bootstrap each.
- `format_push_result(project_types, files, stats, current_version)` — Format push command result as markdown.
- `format_enhanced_summary(commit_title, commit_body, capabilities, roles)` — Format enhanced business-value summary as markdown.
- `format_status_output(version, branch, staged_files, unstaged_files)` — Format status command output as markdown.
- `run_git()` — Run a git command and return the result.
- `run_command(command, capture)` — Run a shell command and return the result.
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
- `get_diff_content(cached)` — Get the actual diff content for analysis.
- `read_ticket(path)` — Read TICKET configuration file (key=value).
- `apply_ticket_prefix(title, ticket)` — Apply ticket prefix (from CLI or TICKET file) to commit title.
- `generate_smart_commit_message(cached)` — Generate a smart commit message.
- `get_file_size_mb(file_path)` — Get file size in megabytes.
- `detect_tokens_in_content(content, patterns)` — Detect tokens in file content using regex patterns.
- `load_gitignore(gitignore_path)` — Load .gitignore patterns, returning (ignored_patterns, whitelisted_patterns).
- `save_gitignore(ignored, gitignore_path)` — Save patterns to .gitignore.
- `check_dot_folders(files, config)` — Check for dot folders/files that should be in .gitignore.
- `manage_dot_folders(files, config, dry_run)` — Proactively manage dot folders in .gitignore.
- `validate_files(files, max_size_mb, block_large_files, token_patterns)` — Validate files before commit.
- `validate_staged_files(config)` — Validate staged files using configuration.
- `push(ctx, bump, no_tag, no_changelog)` — Add, commit, tag, and push changes to remote.
- `recover(ctx, full, error_file, error_message)` — Recover from git push failures.
- `run_git_local()` — Local wrapper for run_git to avoid import issues.
- `show_workflow_preview(files, stats, current_version, new_version)` — Show workflow preview for interactive mode.
- `output_final_summary(ctx_obj, markdown, project_types, files)` — Output final summary in markdown format if requested.
- `execute_push_workflow(ctx_obj, bump, no_tag, no_changelog)` — Execute the complete push workflow.
- `doctor(ctx, fix, path, todo)` — Diagnose and auto-fix common project configuration issues.
- `commit(ctx, detailed, unstaged, markdown)` — Generate a smart commit message for current changes.
- `fix_summary(ctx, fix, preview, cached)` — Auto-fix commit summary quality issues.
- `validate(ctx, fix, cached)` — Validate commit summary against quality gates.
- `detect_project_types()` — Detect what type(s) of project this is.
- `find_version_files()` — Find all version-containing files in the project.
- `get_version_from_file(filepath, pattern)` — Extract version from a file using regex pattern.
- `get_current_version()` — Get current version from VERSION file or project files.
- `bump_version(version, bump_type)` — Bump version according to semantic versioning.
- `update_version_in_file(filepath, pattern, old_version, new_version)` — Update version in a specific file.
- `update_json_version(filepath, new_version)` — Update version in JSON files (package.json, composer.json).
- `update_project_metadata(filepath, user_config)` — Update author and license in project files based on user config.
- `update_readme_metadata(user_config)` — Update license badges and author info in README.md based on user config.
- `sync_all_versions(new_version, user_config)` — Update version, author, and license in all detected project files.
- `status(ctx, markdown)` — Show current git status and version info.
- `init(ctx, force)` — Initialize goal in current repository (creates VERSION, CHANGELOG.md, and goal.yaml).
- `info()` — Show detailed project information and version status.
- `version(bump_type)` — Bump version and sync across all project files.
- `package_managers(language, available)` — Show detected and available package managers for the current project.
- `check_versions(update_badges)` — Check version consistency across registries and README badges.
- `clone(ctx, url, directory)` — Clone a git repository.
- `bootstrap(yes, path)` — Bootstrap project environments (install deps, scaffold tests).
- `publish(ctx, use_make, target, version_arg)` — Publish the current project (optionally using Makefile).
- `push(ctx, bump, no_tag, no_changelog)` — Add, commit, tag, and push changes to remote.
- `makefile_has_target(target)` — Check if Makefile has a specific target.
- `publish_project(project_types, version, yes)` — Publish project to appropriate package registries.
- `config()` — Manage goal configuration.
- `config_show(ctx, key)` — Show configuration value(s).
- `config_validate(ctx)` — Validate goal.yaml configuration.
- `config_update(ctx)` — Update configuration with latest defaults.
- `config_set(ctx, key, value)` — Set a configuration value.
- `config_get(ctx, key)` — Get a configuration value.
- `setup(reset, show_config)` — Setup goal configuration interactively.
- `init_config(force)` — Initialize a new goal.yaml configuration file.
- `load_config(config_path)` — Load configuration from file or create default.
- `ensure_config(auto_update)` — Ensure configuration exists and is up-to-date.
- `generate_business_summary(files, diff_content, config)` — Convenience function to generate enhanced summary.
- `validate_summary(summary, files, config)` — Validate summary against quality gates.
- `auto_fix_summary(summary, files, config)` — Auto-fix summary issues and return corrected summary.
- `diagnose_rust(project_dir, auto_fix)` — Run all Rust-specific diagnostics.
- `diagnose_ruby(project_dir, auto_fix)` — Run all Ruby-specific diagnostics.
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
- `diagnose_dotnet(project_dir, auto_fix)` — Run all .NET-specific diagnostics.
- `diagnose_go(project_dir, auto_fix)` — Run all Go-specific diagnostics.
- `add_issues_to_todo(project_dir, issues, todo_file)` — Add issues to TODO.md without duplicates.
- `diagnose_and_report_with_todo(project_dir, project_type, auto_fix, todo_file)` — Diagnose, fix, report, and optionally add issues to TODO.md.
- `diagnose_php(project_dir, auto_fix)` — Run all PHP-specific diagnostics.
- `strip_ansi(text)` — —
- `split_paths_by_type(paths)` — Split file paths into groups (code/docs/ci/examples/other).
- `stage_paths(paths)` — —
- `confirm(prompt, default)` — Ask for user confirmation with Y/n prompt (Enter defaults to Yes).
- `main(ctx, bump, version, yes)` — Goal - Automated git push with smart commit messages.
- `diagnose_java(project_dir, auto_fix)` — Run all Java-specific diagnostics.
- `create_smart_generator(config)` — Factory function to create SmartCommitGenerator.
- `sync_all_versions_wrapper(new_version, user_config)` — Wrapper to sync versions to all project files.
- `handle_version_sync(new_version, no_version_sync, user_config, yes)` — Sync versions to all project files.
- `get_version_info(current_version, bump)` — Get current and new version info.
- `handle_changelog(new_version, files, commit_msg, config)` — Update changelog.
- `update_changelog_stage(new_version, files, commit_msg, config)` — Stage for updating changelog without git add.
- `get_commit_message(ctx_obj, files, diff_content, message)` — Generate or use provided commit message.
- `enforce_quality_gates(ctx_obj, commit_msg, detailed_result, files)` — Enforce commit quality gates for auto-generated messages.
- `handle_single_commit(commit_title, commit_body, commit_msg, message)` — Handle single commit (non-split mode).
- `handle_split_commits(ctx_obj, files, ticket, new_version)` — Handle split commits per file group.
- `handle_dry_run(ctx_obj, project_types, files, stats)` — Handle dry run output.
- `create_tag(new_version, no_tag)` — Create git tag for release.
- `push_to_remote(branch, tag_name, no_tag, yes)` — Push commits and tags to remote.
- `handle_publish(project_types, new_version, yes)` — Publish to package registries.
- `run_case()` — —
- `print()` — —
- `main()` — —
- `self()` — —
- `diagnose_nodejs(project_dir, auto_fix)` — Run all Node.js-specific diagnostics.
- `diagnose_python(project_dir, auto_fix)` — Run all Python-specific diagnostics.
- `diagnose_project(project_dir, project_type, auto_fix)` — Run diagnostics for a single project directory.
- `diagnose_and_report(project_dir, project_type, auto_fix)` — Diagnose, fix, and print a human-readable report.


## Project Structure

📄 `examples.git-hooks.install`
📄 `examples.markdown-demo`
📦 `goal`
📄 `goal.__main__`
📄 `goal.changelog` (1 functions)
📦 `goal.cli` (9 functions, 1 classes)
📄 `goal.cli.commit_cmd` (3 functions)
📄 `goal.cli.config_cmd` (7 functions)
📄 `goal.cli.doctor_cmd` (1 functions)
📄 `goal.cli.publish` (4 functions)
📄 `goal.cli.publish_cmd` (1 functions)
📄 `goal.cli.push_cmd` (1 functions)
📄 `goal.cli.recover_cmd` (2 functions)
📄 `goal.cli.utils_cmd` (8 functions)
📄 `goal.cli.version` (19 functions)
📄 `goal.commit_generator`
📦 `goal.config`
📄 `goal.config.constants`
📄 `goal.config.manager` (25 functions, 1 classes)
📄 `goal.deep_analyzer` (22 functions, 1 classes)
📦 `goal.doctor`
📄 `goal.doctor.core` (2 functions)
📄 `goal.doctor.dotnet` (1 functions)
📄 `goal.doctor.go` (1 functions)
📄 `goal.doctor.java` (1 functions)
📄 `goal.doctor.logging` (2 functions)
📄 `goal.doctor.models` (2 classes)
📄 `goal.doctor.nodejs` (1 functions)
📄 `goal.doctor.php` (1 functions)
📄 `goal.doctor.python` (16 functions, 1 classes)
📄 `goal.doctor.ruby` (1 functions)
📄 `goal.doctor.rust` (1 functions)
📄 `goal.doctor.todo` (5 functions)
📄 `goal.enhanced_summary`
📄 `goal.formatter` (14 functions, 1 classes)
📦 `goal.generator`
📄 `goal.generator.analyzer` (16 functions, 2 classes)
📄 `goal.generator.generator` (24 functions, 1 classes)
📄 `goal.generator.git_ops` (7 functions, 1 classes)
📄 `goal.git_ops` (22 functions)
📄 `goal.package_managers` (12 functions, 1 classes)
📄 `goal.project_bootstrap` (9 functions)
📄 `goal.project_doctor`
📦 `goal.push`
📄 `goal.push.commands` (1 functions)
📄 `goal.push.core` (6 functions, 1 classes)
📦 `goal.push.stages`
📄 `goal.push.stages.changelog` (2 functions)
📄 `goal.push.stages.commit` (4 functions)
📄 `goal.push.stages.dry_run` (1 functions)
📄 `goal.push.stages.publish` (1 functions)
📄 `goal.push.stages.push_remote` (2 functions)
📄 `goal.push.stages.tag` (1 functions)
📄 `goal.push.stages.version` (4 functions)
📦 `goal.recovery`
📄 `goal.recovery.exceptions` (9 functions, 9 classes)
📄 `goal.recovery.manager` (14 functions, 1 classes)
📄 `goal.recovery.strategies` (27 functions, 7 classes)
📦 `goal.smart_commit`
📄 `goal.smart_commit.abstraction` (9 functions, 1 classes)
📄 `goal.smart_commit.generator` (18 functions, 1 classes)
📦 `goal.summary` (3 functions)
📄 `goal.summary.generator` (16 functions, 1 classes)
📄 `goal.summary.quality_filter` (14 functions, 1 classes)
📄 `goal.summary.validator` (13 functions, 1 classes)
📄 `goal.user_config` (12 functions, 1 classes)
📦 `goal.validators`
📄 `goal.validators.file_validator` (11 functions, 4 classes)
📄 `goal.version_validation` (10 functions)
📄 `integration.run_docker_matrix`
📄 `integration.run_matrix` (4 functions, 1 classes)
📄 `project`

## Requirements

- Python >= >=3.8
- click >=8.0.0- PyYAML >=6.0

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