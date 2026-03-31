# Refactoring Plan — goal

**Source:** code2llm health report 2026-03-31
**Baseline:** 97 files, 18950L, CC̄=5.3, critical=38/658, dups=0, cycles=0

---

## Phase 1 — God Module Split (HIGH, ~1 session)

**Target:** `goal/recovery/strategies.py` (685L, 7 classes, 30 methods, max CC=11)

Split into one file per strategy class under `goal/recovery/`:

| New file | Class | Lines (approx) |
|---|---|---|
| `base.py` | `RecoveryStrategy` (ABC) | ~40 |
| `auth.py` | `AuthErrorStrategy` | ~65 |
| `large_file.py` | `LargeFileStrategy` | ~310 |
| `divergent.py` | `DivergentHistoryStrategy` | ~110 |
| `corrupted.py` | `CorruptedObjectStrategy` | ~45 |
| `lfs.py` | `LFSIssueStrategy` | ~50 |
| `force_push.py` | `ForcePushStrategy` | ~35 |

Update `goal/recovery/__init__.py` to import from new files.
Update `goal/recovery/manager.py` imports.
No public API change — all consumers import from `goal.recovery`.

**Verification:** `python3 -m pytest -q` + `python -c "from goal.recovery import RecoveryManager"`

---

## Phase 2 — Critical CC (CC ≥ 26, HIGH, ~2 sessions)

| # | Function | File | CC | Refactoring Strategy |
|---|---|---|---|---|
| 1 | `short_action_summary` | `generator/analyzer.py` | 34 | Extract tag-detection into a dispatch table / dict mapping |
| 2 | `validate_project_versions` | `version_validation.py` | 30 | Extract per-language validators into a registry dict |
| 3 | `format_enhanced_summary` | `formatter.py` | 29 | Already delegates to `MarkdownFormatter`; extract metric/relation formatting into helpers |
| 4 | `per_file_notes` | `generator/analyzer.py` | 29 | Extract per-extension handlers (`.py`, `.md`, `.sh`) into a handler dict |
| 5 | `ensure_project_environment` | `project_bootstrap.py` | 26 | Extract `_ensure_python_env()` and `_ensure_generic_env()` sub-functions |

**Pattern:** Replace long if/elif chains with **dispatch tables** (dict mapping key → handler). Each handler is a small function with CC ≤ 5.

---

## Phase 3 — High CC (CC 20–25, MEDIUM, ~2 sessions)

| # | Function | File | CC | Strategy |
|---|---|---|---|---|
| 6 | `update_changelog` | `changelog.py` | 24 | Split domain-grouped vs simple entry builders; extract insertion logic |
| 7 | `ensure_git_repository` | `git_ops.py` | 23 | Extract option handlers (`_handle_init_remote`, `_handle_clone`, `_handle_local_init`) |
| 8 | `check_dot_folders` | `validators/file_validator.py` | 23 | Extract whitelist/ignore checks into predicate functions |
| 9 | `_ensure_costs_installed` | `project_bootstrap.py` | 21 | Extract badge generation into `_generate_cost_badge()` |
| 10 | `_ensure_costs_config` | `project_bootstrap.py` | 20 | Extract dep-injection logic into `_add_deps_to_section()` (eliminates duplicate `add_deps`/`add_deps_hatch`) |
| 11 | `guess_package_name` | `project_bootstrap.py` | 20 | Dispatch table keyed by project_type |

---

## Phase 4 — Moderate CC (CC 15–19, MEDIUM, ~2 sessions)

| # | Function | File | CC |
|---|---|---|---|
| 12 | `dry_run` (module) | `push/dry_run.py` | 19 |
| 13 | `validate_files` | `validators/file_validator.py` | 18 |
| 14 | `execute_push_workflow` | `push/core.py` | 17 |
| 15 | `detect_tokens_in_content` | `validators/file_validator.py` | 17 |
| 16 | `commit_cmd` | `cli/commit_cmd.py` | 17 |
| 17 | `_build_summary` | `deep_analyzer.py` | 16 |
| 18 | `_analyze_python_diff` | `deep_analyzer.py` | 15 |
| 19 | `main` | `cli/__init__.py` | 15 |
| 20 | `scaffold_test` | `project_bootstrap.py` | 15 |
| 21 | `_score_by_signals` | `generator/analyzer.py` | 15 |

Most of these are at or near the CC=15 boundary. Prioritize those that also appear in coupling smells.

---

## Phase 5 — Coupling Smells (LOW, ~1 session)

| Package | Smell | Fan-out | Action |
|---|---|---|---|
| `goal.push/` | fan-out=56 | 56 | Already partially split into `push/core.py`, `push/stages/`. Move remaining helpers (cost badge, summary) out of `core.py` into dedicated stage modules. |
| `goal.cli/` | fan-out=67 | 67 | Mostly inherent (CLI must import all commands). Ensure lazy loading via `load_command_modules()`. Low priority. |
| `goal.validators/` | fan-out=11 | 11 | Extract token detection into `validators/token_detector.py`. |

---

## Phase 6 — Quality Gate (LOW)

Once phases 1–4 bring critical count below thresholds, update `pyqual.yaml`:
```yaml
metrics:
  critical_max: 20  # then 10, then 0
```

---

## Ordering & Dependencies

```
Phase 1 (god module) ──────► Phase 2 (critical CC) ──────► Phase 3 (high CC)
                                                                 │
                                                                 ▼
                              Phase 5 (coupling) ◄────── Phase 4 (moderate CC)
                                                                 │
                                                                 ▼
                                                          Phase 6 (gates)
```

Phase 1 is independent — start immediately.
Phases 2–4 are incremental — each function is an isolated commit.
Phase 5 benefits from earlier splits.
Phase 6 is a config-only gate update.

---

## Rules

1. **No public API changes** — all `__init__.py` re-exports stay identical
2. **One function per commit** — easy to bisect
3. **Run `python3 -m pytest -q` after every change**
4. **Keep backward-compat shims** where callers import directly from old locations
5. **No new dependencies** — use only stdlib + existing deps
