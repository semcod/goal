# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/wronai/goal
- **Primary Language**: python
- **Languages**: python: 114, shell: 5, csharp: 1, go: 1, php: 1
- **Analysis Mode**: static
- **Total Functions**: 725
- **Total Classes**: 64
- **Modules**: 123
- **Entry Points**: 499

## Architecture by Module

### goal.project_bootstrap
- **Functions**: 33
- **File**: `project_bootstrap.py`

### goal.git_ops
- **Functions**: 28
- **File**: `git_ops.py`

### goal.config.manager
- **Functions**: 25
- **Classes**: 1
- **File**: `manager.py`

### goal.generator.generator
- **Functions**: 24
- **Classes**: 1
- **File**: `generator.py`

### goal.deep_analyzer
- **Functions**: 23
- **Classes**: 1
- **File**: `deep_analyzer.py`

### goal.generator.analyzer
- **Functions**: 23
- **Classes**: 2
- **File**: `analyzer.py`

### goal.smart_commit.generator
- **Functions**: 22
- **Classes**: 1
- **File**: `generator.py`

### goal.validators.file_validator
- **Functions**: 20
- **Classes**: 4
- **File**: `file_validator.py`

### goal.validation.rules
- **Functions**: 19
- **Classes**: 6
- **File**: `rules.py`

### goal.summary.generator
- **Functions**: 18
- **Classes**: 1
- **File**: `generator.py`

### goal.formatter
- **Functions**: 17
- **Classes**: 1
- **File**: `formatter.py`

### goal.doctor.python
- **Functions**: 17
- **Classes**: 1
- **File**: `python.py`

### goal.postcommit.actions
- **Functions**: 16
- **Classes**: 5
- **File**: `actions.py`

### goal.summary.quality_filter
- **Functions**: 16
- **Classes**: 1
- **File**: `quality_filter.py`

### goal.config.validation
- **Functions**: 15
- **Classes**: 2
- **File**: `validation.py`

### goal.version_validation
- **Functions**: 14
- **File**: `version_validation.py`

### goal.hooks.manager
- **Functions**: 14
- **Classes**: 1
- **File**: `manager.py`

### goal.recovery.manager
- **Functions**: 14
- **Classes**: 1
- **File**: `manager.py`

### goal.push.core
- **Functions**: 14
- **Classes**: 1
- **File**: `core.py`

### goal.push.stages.push_remote
- **Functions**: 14
- **File**: `push_remote.py`

## Key Entry Points

Main execution flows into the system:

### goal.summary.validator.QualityValidator.auto_fix
> Auto-fix summary issues and return corrected summary.
- **Calls**: summary.copy, self.filter.categorize_files, fixed.get, self.filter.has_banned_words, fixed.get, re.match, fixed.get, len

### goal.cli.commit_cmd.validate
> Validate commit summary against quality gates.
- **Calls**: main.command, click.option, click.option, goal.git_ops.get_staged_files, goal.git_ops.get_diff_stats, ctx.obj.get, CommitMessageGenerator, generator.generate_detailed_message

### examples.api-usage.02_git_operations.main
> Demonstrate git operations.
- **Calls**: integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, goal.git_ops.get_staged_files, integration.run_matrix.print

### goal.recovery.large_file.LargeFileStrategy.recover
> Attempt to recover from large file error.
- **Calls**: click.echo, self._extract_file_paths, click.echo, click.echo, click.echo, click.echo, click.echo, click.prompt

### goal.cli.commit_cmd.fix_summary
> Auto-fix commit summary quality issues.
- **Calls**: main.command, click.option, click.option, click.option, goal.git_ops.get_staged_files, goal.git_ops.get_diff_stats, ctx.obj.get, CommitMessageGenerator

### goal.cli.doctor_cmd.doctor
> Diagnose and auto-fix common project configuration issues.
- **Calls**: main.command, click.option, click.option, click.option, None.resolve, goal.project_bootstrap.detect_project_types_deep, todo_file.exists, None.format

### goal.summary.generator.EnhancedSummaryGenerator.generate_enhanced_summary
> Generate complete enhanced summary with business value focus.
- **Calls**: self.quality_filter.dedupe_files, self.analyzer.generate_functional_summary, self.detect_capabilities, self.quality_filter.prioritize_capabilities, self.detect_file_relations, self.quality_filter.dedupe_relations, self.quality_filter.filter_generic_nodes, self._build_relation_chain

### examples.api-usage.01_basic_api.main
> Run basic API examples.
- **Calls**: integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, goal.cli.version_utils.detect_project_types, integration.run_matrix.print, integration.run_matrix.print, goal.cli.version_utils.get_current_version

### goal.cli.wizard_cmd.wizard
> Interactive wizard for complete Goal setup.
- **Calls**: main.command, click.option, click.option, click.option, click.option, click.echo, click.echo, click.echo

### goal.doctor.python.PythonDiagnostics.check_py011_version_consistency
> PY011: Check for consistent version across all config files.
- **Calls**: re.search, version_match.group, setup_py.exists, re.search, version_file.exists, Issue, self.issues.append, setup_py.read_text

### goal.recovery.large_file.LargeFileStrategy._remove_from_history
> Remove files from git history using filter-repo.
- **Calls**: click.echo, self.run_git, click.echo, click.style, subprocess.run, None.stdout.strip, click.echo, subprocess.run

### examples.api-usage.04_version_validation.main
> Demonstrate version validation.
- **Calls**: integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, goal.cli.version_utils.get_current_version, integration.run_matrix.print, integration.run_matrix.print, goal.version_validation.get_pypi_version

### goal.deep_analyzer.CodeChangeAnalyzer._analyze_python_diff
> Analyze Python code changes using AST.
- **Calls**: self._extract_python_entities, self._extract_python_entities, goal.user_config.UserConfig.set, goal.user_config.UserConfig.set, sum, sum, self._detect_value_indicators, old_entities.keys

### goal.doctor.python.PythonDiagnostics.check_py010_project_name_consistency
> PY010: Check for consistent project name across all config files.
- **Calls**: re.search, name_match.group, setup_py.exists, goal_yaml.exists, Issue, self.issues.append, setup_py.read_text, re.search

### goal.cli.commit_cmd.commit
> Generate a smart commit message for current changes.
- **Calls**: main.command, click.option, click.option, click.option, click.option, click.option, click.option, goal.git_ops.get_staged_files

### goal.smart_commit.generator.SmartCommitGenerator.generate_functional_body
> Generate a functional, human-readable commit body.
- **Calls**: analysis.get, analysis.get, analysis.get, analysis.get, analysis.get, analysis.get, analysis.get, parts.append

### goal.summary.generator.EnhancedSummaryGenerator.calculate_quality_metrics
> Calculate quality metrics for the changes.
- **Calls**: analysis.get, len, analysis.get, aggregated.get, min, min, min, min

### goal.doctor.python.PythonDiagnostics.check_py009_string_authors
> PY009: Check for authors in deprecated string format (PEP 621 requires objects).

Note: Skip this check for Poetry projects which require string forma
- **Calls**: re.search, re.search, authors_match.group, re.compile, None.splitlines, Issue, self.issues.append, line.strip

### goal.recovery.divergent.DivergentHistoryStrategy.recover
> Attempt to recover from divergent history.
- **Calls**: click.echo, self.run_git_with_output, click.echo, click.style, click.echo, self.run_git, click.echo, self.run_git_with_output

### goal.smart_commit.abstraction.CodeAbstraction.extract_entities
> Extract code entities (functions, classes, etc.) from diff.
- **Calls**: self.get_language, self.code_parsers.get, parser.get, parser.get, parser.get, goal.user_config.UserConfig.set, None.strip, any

### goal.config.validation.ConfigValidator._validate_project_section
> Validate project configuration.
- **Calls**: self.config.get, project.get, project.get, project.get, self.warnings.append, isinstance, self.errors.append, isinstance

### goal.config.validation.ConfigValidator._validate_git_section
> Validate git configuration.
- **Calls**: self.config.get, git.get, commit.get, commit.get, commit.get, git.get, remote.get, remote.get

### goal.cli.main
> Goal - Automated git push with smart commit messages.
- **Calls**: click.group, click.option, click.option, click.version_option, click.option, click.option, click.option, click.option

### goal.smart_commit.generator.SmartCommitGenerator._generate_functional_summary
> Generate a human-readable functional summary of changes.
- **Calls**: analysis.get, analysis.get, analysis.get, analysis.get, analysis.get, None.join, parts.append, parts.append

### examples.custom-hooks.pre-commit.main
> Run all pre-commit checks.
- **Calls**: integration.run_matrix.print, integration.run_matrix.print, examples.custom-hooks.pre-commit.check_secrets, integration.run_matrix.print, examples.custom-hooks.pre-commit.check_file_sizes, integration.run_matrix.print, examples.custom-hooks.pre-commit.run_tests, integration.run_matrix.print

### examples.api-usage.03_commit_generation.main
> Demonstrate commit message generation.
- **Calls**: integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print, goal.git_ops.get_staged_files, goal.git_ops.get_diff_content, integration.run_matrix.print, integration.run_matrix.print, integration.run_matrix.print

### goal.recovery.manager.RecoveryManager.recover_from_push_failure
> Attempt to recover from a git push failure.
- **Calls**: click.echo, self._create_backup, click.style, self._identify_strategy, click.echo, strategy.recover, click.echo, click.echo

### goal.cli.recover_cmd.recover
> Recover from git push failures.

This command automatically detects and attempts to recover from common
git push failures including:

- Authentication
- **Calls**: main.command, click.option, click.option, click.option, click.option, click.option, os.getcwd, goal.cli.recover_cmd._get_error_output

### goal.doctor.nodejs.diagnose_nodejs
> Run all Node.js-specific diagnostics.
- **Calls**: json.dumps, data.get, json.dumps, pkg_json.exists, json.loads, data.get, issues.append, data.get

### goal.doctor.python.diagnose_python
> Run all Python-specific diagnostics.
- **Calls**: pyproject.read_text, PythonDiagnostics, diag.check_py002_build_system, diag.check_py003_license_classifiers, diag.check_py004_deprecated_backends, diag.check_py005_license_table, diag.check_py006_duplicate_authors, diag.check_py007_requires_python

## Process Flows

Key execution flows identified:

### Flow 1: auto_fix
```
auto_fix [goal.summary.validator.QualityValidator]
```

### Flow 2: validate
```
validate [goal.cli.commit_cmd]
  └─ →> get_staged_files
      └─> run_git
  └─ →> get_diff_stats
      └─> run_git
      └─> run_git
```

### Flow 3: main
```
main [examples.api-usage.02_git_operations]
  └─ →> print
  └─ →> print
```

### Flow 4: recover
```
recover [goal.recovery.large_file.LargeFileStrategy]
```

### Flow 5: fix_summary
```
fix_summary [goal.cli.commit_cmd]
  └─ →> get_staged_files
      └─> run_git
```

### Flow 6: doctor
```
doctor [goal.cli.doctor_cmd]
```

### Flow 7: generate_enhanced_summary
```
generate_enhanced_summary [goal.summary.generator.EnhancedSummaryGenerator]
```

### Flow 8: wizard
```
wizard [goal.cli.wizard_cmd]
```

### Flow 9: check_py011_version_consistency
```
check_py011_version_consistency [goal.doctor.python.PythonDiagnostics]
```

### Flow 10: _remove_from_history
```
_remove_from_history [goal.recovery.large_file.LargeFileStrategy]
```

## Key Classes

### goal.deep_analyzer.CodeChangeAnalyzer
> Analyzes code changes to extract functional meaning.
- **Methods**: 23
- **Key Methods**: goal.deep_analyzer.CodeChangeAnalyzer.__init__, goal.deep_analyzer.CodeChangeAnalyzer.analyze_file_diff, goal.deep_analyzer.CodeChangeAnalyzer._detect_language, goal.deep_analyzer.CodeChangeAnalyzer._analyze_python_diff, goal.deep_analyzer.CodeChangeAnalyzer._detect_value_indicators, goal.deep_analyzer.CodeChangeAnalyzer._extract_python_entities, goal.deep_analyzer.CodeChangeAnalyzer._get_decorator_name, goal.deep_analyzer.CodeChangeAnalyzer._calculate_complexity, goal.deep_analyzer.CodeChangeAnalyzer._analyze_js_diff, goal.deep_analyzer.CodeChangeAnalyzer._analyze_generic_diff

### goal.generator.generator.CommitMessageGenerator
> Generate conventional commit messages using diff analysis and lightweight classification.
- **Methods**: 23
- **Key Methods**: goal.generator.generator.CommitMessageGenerator.__init__, goal.generator.generator.CommitMessageGenerator.get_diff_stats, goal.generator.generator.CommitMessageGenerator.get_name_status, goal.generator.generator.CommitMessageGenerator.get_numstat_map, goal.generator.generator.CommitMessageGenerator.get_changed_files, goal.generator.generator.CommitMessageGenerator.get_diff_content, goal.generator.generator.CommitMessageGenerator.classify_change_type, goal.generator.generator.CommitMessageGenerator.detect_scope, goal.generator.generator.CommitMessageGenerator.extract_functions_changed, goal.generator.generator.CommitMessageGenerator._short_action_summary

### goal.config.manager.GoalConfig
> Manages goal.yaml configuration file.
- **Methods**: 22
- **Key Methods**: goal.config.manager.GoalConfig.__init__, goal.config.manager.GoalConfig._find_config, goal.config.manager.GoalConfig._find_git_root, goal.config.manager.GoalConfig.exists, goal.config.manager.GoalConfig.load, goal.config.manager.GoalConfig._get_default_config, goal.config.manager.GoalConfig._deep_copy, goal.config.manager.GoalConfig._merge_configs, goal.config.manager.GoalConfig._detect_project_name, goal.config.manager.GoalConfig._detect_project_types

### goal.smart_commit.generator.SmartCommitGenerator
> Generates smart commit messages using code abstraction.
- **Methods**: 22
- **Key Methods**: goal.smart_commit.generator.SmartCommitGenerator.__init__, goal.smart_commit.generator.SmartCommitGenerator.deep_analyzer, goal.smart_commit.generator.SmartCommitGenerator._analyze_file_diffs, goal.smart_commit.generator.SmartCommitGenerator._merge_deep_analysis, goal.smart_commit.generator.SmartCommitGenerator.analyze_changes, goal.smart_commit.generator.SmartCommitGenerator._summarize_features, goal.smart_commit.generator.SmartCommitGenerator._summarize_entities, goal.smart_commit.generator.SmartCommitGenerator._generate_functional_summary, goal.smart_commit.generator.SmartCommitGenerator._get_staged_files, goal.smart_commit.generator.SmartCommitGenerator._get_file_diff

### goal.summary.generator.EnhancedSummaryGenerator
> Generate business-value focused commit summaries.
- **Methods**: 18
- **Key Methods**: goal.summary.generator.EnhancedSummaryGenerator.__init__, goal.summary.generator.EnhancedSummaryGenerator.map_entity_to_role, goal.summary.generator.EnhancedSummaryGenerator.detect_capabilities, goal.summary.generator.EnhancedSummaryGenerator.detect_file_relations, goal.summary.generator.EnhancedSummaryGenerator._infer_domain, goal.summary.generator.EnhancedSummaryGenerator._build_relation_chain, goal.summary.generator.EnhancedSummaryGenerator._render_relations_ascii, goal.summary.generator.EnhancedSummaryGenerator.calculate_quality_metrics, goal.summary.generator.EnhancedSummaryGenerator.generate_value_title, goal.summary.generator.EnhancedSummaryGenerator.generate_enhanced_summary

### goal.summary.quality_filter.SummaryQualityFilter
> Filter noise and improve summary quality.
- **Methods**: 16
- **Key Methods**: goal.summary.quality_filter.SummaryQualityFilter.__init__, goal.summary.quality_filter.SummaryQualityFilter.is_noise, goal.summary.quality_filter.SummaryQualityFilter.filter_entities, goal.summary.quality_filter.SummaryQualityFilter.has_banned_words, goal.summary.quality_filter.SummaryQualityFilter.classify_intent, goal.summary.quality_filter.SummaryQualityFilter.prioritize_capabilities, goal.summary.quality_filter.SummaryQualityFilter.format_complexity_delta, goal.summary.quality_filter.SummaryQualityFilter.dedupe_relations, goal.summary.quality_filter.SummaryQualityFilter.dedupe_files, goal.summary.quality_filter.SummaryQualityFilter.categorize_files

### goal.doctor.python.PythonDiagnostics
> Container for Python diagnostic checks with shared state.
- **Methods**: 16
- **Key Methods**: goal.doctor.python.PythonDiagnostics.__init__, goal.doctor.python.PythonDiagnostics.check_py001_missing_config, goal.doctor.python.PythonDiagnostics.check_py002_build_system, goal.doctor.python.PythonDiagnostics.check_py003_license_classifiers, goal.doctor.python.PythonDiagnostics.check_py004_deprecated_backends, goal.doctor.python.PythonDiagnostics.check_py005_license_table, goal.doctor.python.PythonDiagnostics.check_py006_duplicate_authors, goal.doctor.python.PythonDiagnostics.check_py007_requires_python, goal.doctor.python.PythonDiagnostics.check_py008_empty_classifiers, goal.doctor.python.PythonDiagnostics.check_py009_string_authors

### goal.generator.analyzer.ChangeAnalyzer
> Analyze git changes to classify type, detect scope, and extract functions.
- **Methods**: 14
- **Key Methods**: goal.generator.analyzer.ChangeAnalyzer.classify_change_type, goal.generator.analyzer.ChangeAnalyzer._detect_signals, goal.generator.analyzer.ChangeAnalyzer._has_package_code, goal.generator.analyzer.ChangeAnalyzer._is_docs_only, goal.generator.analyzer.ChangeAnalyzer._is_ci_only, goal.generator.analyzer.ChangeAnalyzer._has_new_goal_python_file, goal.generator.analyzer.ChangeAnalyzer._score_by_file_patterns, goal.generator.analyzer.ChangeAnalyzer._score_by_diff_content, goal.generator.analyzer.ChangeAnalyzer._score_by_statistics, goal.generator.analyzer.ChangeAnalyzer._score_by_signals

### goal.recovery.manager.RecoveryManager
> Manages the recovery process for failed git pushes.
- **Methods**: 14
- **Key Methods**: goal.recovery.manager.RecoveryManager.__init__, goal.recovery.manager.RecoveryManager._ensure_recovery_dir, goal.recovery.manager.RecoveryManager.run_git, goal.recovery.manager.RecoveryManager.recover_from_push_failure, goal.recovery.manager.RecoveryManager._identify_strategy, goal.recovery.manager.RecoveryManager._create_backup, goal.recovery.manager.RecoveryManager._cleanup_backup, goal.recovery.manager.RecoveryManager._rollback_to_backup, goal.recovery.manager.RecoveryManager._attempt_push, goal.recovery.manager.RecoveryManager.setup_clean_clone

### goal.summary.validator.QualityValidator
> Validate commit summary against quality gates.
- **Methods**: 13
- **Key Methods**: goal.summary.validator.QualityValidator.__init__, goal.summary.validator.QualityValidator.validate, goal.summary.validator.QualityValidator._extract_intent, goal.summary.validator.QualityValidator._validate_title, goal.summary.validator.QualityValidator._validate_intent, goal.summary.validator.QualityValidator._validate_metrics, goal.summary.validator.QualityValidator._validate_relations, goal.summary.validator.QualityValidator._validate_files, goal.summary.validator.QualityValidator._validate_capabilities, goal.summary.validator.QualityValidator._validate_body

### goal.hooks.manager.HooksManager
> Manages pre-commit hooks for Goal.
- **Methods**: 11
- **Key Methods**: goal.hooks.manager.HooksManager.__init__, goal.hooks.manager.HooksManager.is_precommit_installed, goal.hooks.manager.HooksManager.is_hooks_configured, goal.hooks.manager.HooksManager.install_precommit, goal.hooks.manager.HooksManager.create_hook_script, goal.hooks.manager.HooksManager.create_precommit_config, goal.hooks.manager.HooksManager.install_hooks, goal.hooks.manager.HooksManager.uninstall_hooks, goal.hooks.manager.HooksManager.run_validation, goal.hooks.manager.HooksManager.run_hooks

### goal.recovery.large_file.LargeFileStrategy
> Handles large file errors.
- **Methods**: 11
- **Key Methods**: goal.recovery.large_file.LargeFileStrategy.__init__, goal.recovery.large_file.LargeFileStrategy.can_handle, goal.recovery.large_file.LargeFileStrategy.recover, goal.recovery.large_file.LargeFileStrategy._files_in_history, goal.recovery.large_file.LargeFileStrategy._remove_from_history, goal.recovery.large_file.LargeFileStrategy._extract_file_paths, goal.recovery.large_file.LargeFileStrategy._find_large_files, goal.recovery.large_file.LargeFileStrategy._get_file_size_mb, goal.recovery.large_file.LargeFileStrategy._remove_large_files, goal.recovery.large_file.LargeFileStrategy._move_to_lfs
- **Inherits**: RecoveryStrategy

### goal.config.validation.ConfigValidator
> Validates Goal configuration files.
- **Methods**: 11
- **Key Methods**: goal.config.validation.ConfigValidator.__init__, goal.config.validation.ConfigValidator.validate, goal.config.validation.ConfigValidator._validate_required_sections, goal.config.validation.ConfigValidator._validate_project_section, goal.config.validation.ConfigValidator._validate_git_section, goal.config.validation.ConfigValidator._validate_versioning_section, goal.config.validation.ConfigValidator._validate_publishing_section, goal.config.validation.ConfigValidator._check_bool, goal.config.validation.ConfigValidator._check_numeric, goal.config.validation.ConfigValidator._validate_advanced_section

### goal.authors.manager.AuthorsManager
> Manages project authors and team members.
- **Methods**: 10
- **Key Methods**: goal.authors.manager.AuthorsManager.__init__, goal.authors.manager.AuthorsManager.get_authors, goal.authors.manager.AuthorsManager.add_author, goal.authors.manager.AuthorsManager.remove_author, goal.authors.manager.AuthorsManager.update_author, goal.authors.manager.AuthorsManager.find_author, goal.authors.manager.AuthorsManager.list_authors, goal.authors.manager.AuthorsManager.get_current_author, goal.authors.manager.AuthorsManager.import_from_git, goal.authors.manager.AuthorsManager.export_to_contributors

### goal.generator.analyzer.ContentAnalyzer
> Analyze content for short summaries and per-file notes.
- **Methods**: 9
- **Key Methods**: goal.generator.analyzer.ContentAnalyzer.short_action_summary, goal.generator.analyzer.ContentAnalyzer._detect_tags, goal.generator.analyzer.ContentAnalyzer._summary_from_tags, goal.generator.analyzer.ContentAnalyzer._summary_from_paths, goal.generator.analyzer.ContentAnalyzer.per_file_notes, goal.generator.analyzer.ContentAnalyzer._get_added_lines, goal.generator.analyzer.ContentAnalyzer._notes_python, goal.generator.analyzer.ContentAnalyzer._notes_docs, goal.generator.analyzer.ContentAnalyzer._notes_shell

### goal.smart_commit.abstraction.CodeAbstraction
> Extracts meaningful abstractions from code changes.
- **Methods**: 9
- **Key Methods**: goal.smart_commit.abstraction.CodeAbstraction.__init__, goal.smart_commit.abstraction.CodeAbstraction.get_domain, goal.smart_commit.abstraction.CodeAbstraction.get_language, goal.smart_commit.abstraction.CodeAbstraction.extract_entities, goal.smart_commit.abstraction.CodeAbstraction.extract_markdown_topics, goal.smart_commit.abstraction.CodeAbstraction.infer_benefit, goal.smart_commit.abstraction.CodeAbstraction.detect_features, goal.smart_commit.abstraction.CodeAbstraction.determine_abstraction_level, goal.smart_commit.abstraction.CodeAbstraction.get_action_verb

### goal.formatter.MarkdownFormatter
> Formats Goal output as structured markdown for LLM consumption.
- **Methods**: 8
- **Key Methods**: goal.formatter.MarkdownFormatter.__init__, goal.formatter.MarkdownFormatter.add_header, goal.formatter.MarkdownFormatter.add_metadata, goal.formatter.MarkdownFormatter.add_section, goal.formatter.MarkdownFormatter.add_list, goal.formatter.MarkdownFormatter.add_command_output, goal.formatter.MarkdownFormatter.add_summary, goal.formatter.MarkdownFormatter.render

### goal.license.manager.LicenseManager
> Manages license operations including template handling and file creation.
- **Methods**: 8
- **Key Methods**: goal.license.manager.LicenseManager.__init__, goal.license.manager.LicenseManager.get_available_licenses, goal.license.manager.LicenseManager.get_license_template, goal.license.manager.LicenseManager.add_custom_template, goal.license.manager.LicenseManager.create_license_file, goal.license.manager.LicenseManager.update_license_file, goal.license.manager.LicenseManager._detect_license_type, goal.license.manager.LicenseManager.validate_license_file

### goal.generator.git_ops.GitDiffOperations
> Git diff operations with caching.
- **Methods**: 7
- **Key Methods**: goal.generator.git_ops.GitDiffOperations.__init__, goal.generator.git_ops.GitDiffOperations.get_diff_stats, goal.generator.git_ops.GitDiffOperations.get_name_status, goal.generator.git_ops.GitDiffOperations.get_numstat_map, goal.generator.git_ops.GitDiffOperations.get_changed_files, goal.generator.git_ops.GitDiffOperations.get_diff_content, goal.generator.git_ops.GitDiffOperations.clear_cache

### goal.user_config.UserConfig
> Manages user-specific configuration stored in ~/.goal
- **Methods**: 6
- **Key Methods**: goal.user_config.UserConfig.__init__, goal.user_config.UserConfig._load, goal.user_config.UserConfig._save, goal.user_config.UserConfig.get, goal.user_config.UserConfig.set, goal.user_config.UserConfig.is_initialized

## Data Transformation Functions

Key functions that process and transform data:

### goal.toml_validation.validate_toml_file
> Validate a TOML file and return helpful error message if invalid.

Args:
    filepath: Path to the T
- **Output to**: goal.toml_validation.get_tomllib, filepath.read_text, filepath.exists, hasattr, tomllib.loads

### goal.toml_validation.validate_project_toml_files
> Validate all common TOML files in a project.

Args:
    project_dir: Project directory to check
    
- **Output to**: Path, toml_file.exists, goal.toml_validation.validate_toml_file, errors.append

### goal.version_validation.validate_project_versions
> Validate versions across different registries.

Returns:
    Dict with validation results for each p
- **Output to**: _VERSION_VALIDATORS.get, getattr, getattr, detect_fn, fetch_fn

### goal.version_validation.format_validation_results
> Format validation results for display.
- **Output to**: results.items, messages.append, messages.append, messages.append, messages.append

### goal.formatter.format_push_result
> Format push command result as markdown.
- **Output to**: MarkdownFormatter, formatter.add_metadata, formatter.add_header, goal.formatter._build_functional_overview, formatter.add_section

### goal.formatter._format_complexity_metric
> Format complexity change as a single metric line, or None.
- **Output to**: metrics.get, metrics.get, abs

### goal.formatter._format_metrics_section
> Build the Impact Metrics section content.
- **Output to**: goal.formatter._format_complexity_metric, lines.append, None.join, lines.append, metrics.get

### goal.formatter._format_relations_section
> Build the Relations section content, or None if empty.
- **Output to**: relations.get, relations.get

### goal.formatter.format_enhanced_summary
> Format enhanced business-value summary as markdown.
- **Output to**: MarkdownFormatter, formatter.add_metadata, formatter.add_header, sum, sum

### goal.formatter.format_status_output
> Format status command output as markdown.
- **Output to**: MarkdownFormatter, formatter.add_header, None.strip, formatter.add_section, formatter.add_list

### goal.project_bootstrap._validate_pfix_env
> Validate that OPENROUTER_API_KEY is configured in .env.

Shows error message if key is missing or em
- **Output to**: goal.project_bootstrap._find_openrouter_api_key, click.echo, click.echo, click.echo, click.echo

### goal.git_ops.validate_repo_url
> Validate that a URL looks like a git repository (HTTP/HTTPS/SSH/file).
- **Output to**: url.strip, re.match, re.match, re.match

### goal.validators.file_validator.validate_files
> Validate files before commit.

Args:
    files: List of file paths to validate
    max_size_mb: Maxi
- **Output to**: goal.validators.file_validator._is_excluded, goal.validators.file_validator.get_file_size_mb, goal.validators.file_validator.handle_large_files, os.path.exists, large_files_found.append

### goal.validators.file_validator.validate_staged_files
> Validate staged files using configuration.

This is a convenience function that extracts validation 
- **Output to**: goal.git_ops.get_staged_files, goal.validators.file_validator.manage_dot_folders, goal.git_ops.get_staged_files, goal.validators.file_validator.validate_files, config.get

### goal.push.stages.dry_run._format_markdown_dry_run
> Return markdown-formatted dry-run output.
- **Output to**: goal.formatter.format_push_result, detailed_result.get, goal.formatter.format_enhanced_summary, detailed_result.get, detailed_result.get

### goal.push.core._validate_staged_files
> Validate staged files for security issues.
- **Output to**: goal.validators.file_validator.validate_staged_files, click.echo, ctx_obj.get, click.echo, click.echo

### goal.cli.config_validate_cmd.validate_cmd
> Validate goal.yaml configuration file.

Checks that the configuration file is valid, complete, and f
- **Output to**: click.command, click.option, click.option, click.option, click.echo

### goal.cli.license_cmd.license_validate
> Validate the LICENSE file.
- **Output to**: license.command, LicenseManager, manager.validate_license_file, click.echo, click.echo

### goal.cli.postcommit_cmd.postcommit_validate
> Validate post-commit action configuration.
- **Output to**: postcommit.command, PostCommitManager, click.echo, click.echo, manager.validate_actions

### goal.cli.commit_cmd.validate
> Validate commit summary against quality gates.
- **Output to**: main.command, click.option, click.option, goal.git_ops.get_staged_files, goal.git_ops.get_diff_stats

### goal.cli.validation_cmd.validation_validate
> Validate rule configurations.
- **Output to**: validation.command, ValidationRuleManager, click.echo, click.echo, manager.validate_config

### goal.cli.config_cmd.config_validate
> Validate goal.yaml configuration.

Checks that the configuration file is valid, complete, and follow
- **Output to**: config.command, click.option, click.option, click.echo, click.style

### goal.postcommit.manager.PostCommitManager.validate_actions
> Validate all configured actions.

Returns:
    True if all actions are valid
- **Output to**: self.get_config, action_config.get, action_class, click.echo, action.validate_config

### goal.postcommit.actions.PostCommitAction.validate_config
> Validate action configuration.

### goal.postcommit.actions.NotificationAction.validate_config

## Behavioral Patterns

### state_machine_CodeChangeAnalyzer
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: goal.deep_analyzer.CodeChangeAnalyzer.__init__, goal.deep_analyzer.CodeChangeAnalyzer.analyze_file_diff, goal.deep_analyzer.CodeChangeAnalyzer._detect_language, goal.deep_analyzer.CodeChangeAnalyzer._analyze_python_diff, goal.deep_analyzer.CodeChangeAnalyzer._detect_value_indicators

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `goal.summary.validator.QualityValidator.auto_fix` - 59 calls
- `goal.user_config.initialize_user_config` - 52 calls
- `goal.cli.commit_cmd.validate` - 45 calls
- `goal.push.core.execute_push_workflow` - 42 calls
- `goal.push.stages.push_remote.push_to_remote` - 41 calls
- `examples.api-usage.02_git_operations.main` - 38 calls
- `goal.recovery.large_file.LargeFileStrategy.recover` - 38 calls
- `goal.cli.commit_cmd.fix_summary` - 38 calls
- `goal.cli.doctor_cmd.doctor` - 36 calls
- `goal.summary.generator.EnhancedSummaryGenerator.generate_enhanced_summary` - 36 calls
- `examples.api-usage.01_basic_api.main` - 34 calls
- `goal.cli.wizard_cmd.wizard` - 34 calls
- `goal.doctor.python.PythonDiagnostics.check_py011_version_consistency` - 34 calls
- `goal.user_config.show_user_config` - 31 calls
- `examples.api-usage.04_version_validation.main` - 30 calls
- `goal.doctor.python.PythonDiagnostics.check_py010_project_name_consistency` - 28 calls
- `goal.cli.commit_cmd.commit` - 27 calls
- `goal.smart_commit.generator.SmartCommitGenerator.generate_functional_body` - 27 calls
- `goal.summary.generator.EnhancedSummaryGenerator.calculate_quality_metrics` - 26 calls
- `goal.doctor.python.PythonDiagnostics.check_py009_string_authors` - 26 calls
- `goal.user_config.prompt_for_license` - 25 calls
- `goal.recovery.divergent.DivergentHistoryStrategy.recover` - 25 calls
- `goal.cli.version_utils.update_project_metadata` - 25 calls
- `goal.config.validation.validate_config_file` - 25 calls
- `goal.smart_commit.abstraction.CodeAbstraction.extract_entities` - 25 calls
- `goal.cli.main` - 24 calls
- `examples.custom-hooks.pre-commit.main` - 23 calls
- `examples.api-usage.03_commit_generation.main` - 23 calls
- `examples.template-generator.generate.generate_project` - 23 calls
- `goal.formatter.format_enhanced_summary` - 23 calls
- `goal.git_ops.ensure_remote` - 23 calls
- `goal.recovery.manager.RecoveryManager.recover_from_push_failure` - 23 calls
- `goal.cli.recover_cmd.recover` - 23 calls
- `goal.cli.version_utils.update_readme_metadata` - 23 calls
- `goal.doctor.nodejs.diagnose_nodejs` - 23 calls
- `goal.doctor.python.diagnose_python` - 23 calls
- `goal.recovery.auth.AuthErrorStrategy.recover` - 22 calls
- `goal.push.stages.commit.handle_split_commits` - 22 calls
- `goal.push.core.show_workflow_preview` - 22 calls
- `goal.config.validation.validate_config_interactive` - 22 calls

## System Interactions

How components interact:

```mermaid
graph TD
    auto_fix --> copy
    auto_fix --> categorize_files
    auto_fix --> get
    auto_fix --> has_banned_words
    validate --> command
    validate --> option
    validate --> get_staged_files
    validate --> get_diff_stats
    main --> print
    recover --> echo
    recover --> _extract_file_paths
    fix_summary --> command
    fix_summary --> option
    fix_summary --> get_staged_files
    doctor --> command
    doctor --> option
    doctor --> resolve
    generate_enhanced_su --> dedupe_files
    generate_enhanced_su --> generate_functional_
    generate_enhanced_su --> detect_capabilities
    generate_enhanced_su --> prioritize_capabilit
    generate_enhanced_su --> detect_file_relation
    main --> detect_project_types
    wizard --> command
    wizard --> option
    check_py011_version_ --> search
    check_py011_version_ --> group
    check_py011_version_ --> exists
    _remove_from_history --> echo
    _remove_from_history --> run_git
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.