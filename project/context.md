# System Architecture Analysis

## Overview

- **Project**: goal
- **Language**: python
- **Files**: 48
- **Lines**: 13352
- **Functions**: 356
- **Classes**: 20
- **Avg CC**: 6.0
- **Critical (CC≥10)**: 68

## Architecture

### goal/ (13 files, 3445L, 102 functions)

- `version_validation.py` — 301L, 10 methods, CC↑30
- `formatter.py` — 402L, 14 methods, CC↑29
- `project_bootstrap.py` — 589L, 9 methods, CC↑25
- `changelog.py` — 125L, 1 methods, CC↑24
- `git_ops.py` — 473L, 22 methods, CC↑23
- _8 more files_

### goal/cli/ (9 files, 1816L, 52 functions)

- `version.py` — 730L, 18 methods, CC↑33
- `__init__.py` — 206L, 9 methods, CC↑14
- `commit_cmd.py` — 187L, 3 methods, CC↑13
- `publish.py` — 136L, 4 methods, CC↑13
- `doctor_cmd.py` — 99L, 1 methods, CC↑12
- _4 more files_

### goal/config/ (3 files, 824L, 25 functions)

- `manager.py` — 449L, 25 methods, CC↑10
- `__init__.py` — 24L, 0 methods, CC↑0
- `constants.py` — 351L, 0 methods, CC↑0

### goal/doctor/ (13 files, 1097L, 32 functions)

- `python.py` — 486L, 16 methods, CC↑17
- `nodejs.py` — 77L, 1 methods, CC↑13
- `todo.py` — 127L, 5 methods, CC↑9
- `core.py` — 87L, 2 methods, CC↑8
- `php.py` — 45L, 1 methods, CC↑7
- _8 more files_

### goal/generator/ (4 files, 965L, 47 functions)

- `analyzer.py` — 396L, 16 methods, CC↑34
- `generator.py` — 384L, 24 methods, CC↑12
- `git_ops.py` — 171L, 7 methods, CC↑11
- `__init__.py` — 14L, 0 methods, CC↑0

### goal/push/ (3 files, 368L, 7 functions)

- `core.py` — 271L, 6 methods, CC↑29
- `commands.py` — 41L, 1 methods, CC↑1
- `__init__.py` — 56L, 0 methods, CC↑0

### goal/push/stages/ (8 files, 534L, 14 functions)

- `dry_run.py` — 98L, 1 methods, CC↑19
- `commit.py` — 213L, 4 methods, CC↑17
- `push_remote.py` — 56L, 1 methods, CC↑12
- `publish.py` — 31L, 1 methods, CC↑5
- `tag.py` — 28L, 1 methods, CC↑4
- _3 more files_

### goal/smart_commit/ (3 files, 807L, 27 functions)

- `generator.py` — 524L, 18 methods, CC↑24
- `abstraction.py` — 269L, 9 methods, CC↑20
- `__init__.py` — 14L, 0 methods, CC↑0

### goal/summary/ (4 files, 1355L, 46 functions)

- `generator.py` — 675L, 16 methods, CC↑26
- `quality_filter.py` — 328L, 14 methods, CC↑25
- `validator.py` — 310L, 13 methods, CC↑19
- `__init__.py` — 42L, 3 methods, CC↑2

### integration/ (2 files, 221L, 4 functions)

- `run_docker_matrix.sh` — 5L, 0 methods, CC↑0
- `run_matrix.sh` — 216L, 4 methods, CC↑0

### root/ (1 files, 14L, 0 functions)

- `project.sh` — 14L, 0 methods, CC↑0

## Key Exports

- **ChangeAnalyzer** (class, CC̄=6.1)
  - `_score_by_signals` CC=15 ⚠ split
- **ContentAnalyzer** (class, CC̄=31.5)
  - `short_action_summary` CC=34 ⚠ split
  - `per_file_notes` CC=29 ⚠ split
- **update_project_metadata** (function, CC=26) ⚠ split
- **sync_all_versions** (function, CC=33) ⚠ split
- **validate_project_versions** (function, CC=30) ⚠ split
- **format_enhanced_summary** (function, CC=29) ⚠ split
- **execute_push_workflow** (function, CC=29) ⚠ split
- **EnhancedSummaryGenerator** (class, CC̄=9.4)
  - `generate_value_title` CC=19 ⚠ split
  - `_format_changes_section` CC=26 ⚠ split
- **guess_package_name** (function, CC=20) ⚠ split
- **ensure_project_environment** (function, CC=25) ⚠ split
- **scaffold_test** (function, CC=15) ⚠ split
- **SummaryQualityFilter** (class, CC̄=7.6)
  - `classify_intent_smart` CC=25 ⚠ split
- **update_changelog** (function, CC=24) ⚠ split
- **SmartCommitGenerator** (class, CC̄=8.0)
  - `analyze_changes` CC=24 ⚠ split
  - `_generate_functional_summary` CC=22 ⚠ split
- **ensure_git_repository** (function, CC=23) ⚠ split
- **CodeAbstraction** (class, CC̄=7.6)
  - `extract_entities` CC=20 ⚠ split
- **handle_dry_run** (function, CC=19) ⚠ split
- **QualityValidator** (class, CC̄=5.5)
  - `auto_fix` CC=19 ⚠ split
- **PythonDiagnostics** (class, CC̄=6.4)
  - `check_py011_version_consistency` CC=17 ⚠ split
- **enforce_quality_gates** (function, CC=15) ⚠ split
- **handle_split_commits** (function, CC=17) ⚠ split
- **CodeChangeAnalyzer** (class, CC̄=6.5)
  - `_analyze_python_diff` CC=15 ⚠ split
  - `_build_summary` CC=16 ⚠ split
- **GitDiffOperations** (class, CC̄=6.4)

## Hotspots (High Fan-Out)

- **execute_push_workflow** — fan-out=35: Execute the complete push workflow.
- **QualityValidator.auto_fix** — fan-out=27: Auto-fix summary issues and return corrected summary.
- **SmartCommitGenerator.analyze_changes** — fan-out=27: Analysis pipeline, 27 stages
- **EnhancedSummaryGenerator.generate_enhanced_summary** — fan-out=24: Generate complete enhanced summary with business value focus.
- **update_changelog** — fan-out=23: Update CHANGELOG.md with new version and changes.

Args:
    version: New versio
- **guess_package_name** — fan-out=22: Best-effort guess of the package/module name for scaffold templates.
- **PythonDiagnostics.check_py011_version_consistency** — fan-out=21: PY011: Check for consistent version across all config files.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split ensure_project_environment (CC=25 → target CC<10) | high | low |
| 2 | Split validate_project_versions (CC=30 → target CC<10) | high | low |
| 3 | Split format_enhanced_summary (CC=29 → target CC<10) | high | low |
| 4 | Split ContentAnalyzer.short_action_summary (CC=34 → target CC<10) | high | low |
| 5 | Split ContentAnalyzer.per_file_notes (CC=29 → target CC<10) | high | low |
| 6 | Split execute_push_workflow (CC=29 → target CC<10) | high | low |
| 7 | Split update_project_metadata (CC=26 → target CC<10) | high | low |
| 8 | Split sync_all_versions (CC=33 → target CC<10) | high | low |
| 9 | Split EnhancedSummaryGenerator._format_changes_section (CC=26 → target CC<10) | high | low |
| 10 | Split SummaryQualityFilter.classify_intent_smart (CC=25 → target CC<10) | high | low |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

