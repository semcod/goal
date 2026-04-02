# Refactoring Plan — goal

**Source:** code2llm health report 2026-03-31
**Baseline:** 97 files, 18950L, CC̄=5.3, critical=38/658, dups=0, cycles=0

---

## Phase 1 — God Module Split (HIGH, ~1 session) ✅ DONE

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

## Phase 2 — Critical CC (CC ≥ 26, HIGH, ~2 sessions) ✅ DONE

| # | Function | File | CC | Refactoring Strategy | Status |
|---|---|---|---|---|---|
| 1 | `short_action_summary` | `generator/analyzer.py` | 34 | Extract tag-detection into a dispatch table / dict mapping | ✅ Already had `_TAG_DETECTORS` dispatch + helpers |
| 2 | `validate_project_versions` | `version_validation.py` | 30 | Extract per-language validators into a registry dict | ✅ Extracted `_validate_single_type()` with early returns |
| 3 | `format_enhanced_summary` | `formatter.py` | 29 | Already delegates to `MarkdownFormatter`; extract metric/relation formatting into helpers | ✅ Section builder list pattern |
| 4 | `per_file_notes` | `generator/analyzer.py` | 29 | Extract per-extension handlers (`.py`, `.md`, `.sh`) into a handler dict | ✅ `_EXT_NOTE_HANDLERS` dispatch dict |
| 5 | `ensure_project_environment` | `project_bootstrap.py` | 26 | Extract `_ensure_python_env()` and `_ensure_generic_env()` sub-functions | ✅ Already refactored |

**Pattern:** Replace long if/elif chains with **dispatch tables** (dict mapping key → handler). Each handler is a small function with CC ≤ 5.

---

## Phase 3 — High CC (CC 20–25, MEDIUM, ~2 sessions) ✅ DONE

| # | Function | File | CC | Strategy | Status |
|---|---|---|---|---|---|
| 6 | `update_changelog` | `changelog.py` | 24 | Split domain-grouped vs simple entry builders; extract insertion logic | ✅ Extracted `_find_unreleased_insert_pos()` helper |
| 7 | `ensure_git_repository` | `git_ops.py` | 23 | Extract option handlers (`_handle_init_remote`, `_handle_clone`, `_handle_local_init`) | ✅ Already uses dispatch dict |
| 8 | `check_dot_folders` | `validators/file_validator.py` | 23 | Extract whitelist/ignore checks into predicate functions | ✅ Already uses predicate chain |
| 9 | `_ensure_costs_installed` | `project_bootstrap.py` | 21 | Extract badge generation into `_generate_cost_badge()` | ✅ Already decomposed (CC=2) |
| 10 | `_ensure_costs_config` | `project_bootstrap.py` | 20 | Extract dep-injection logic into `_add_deps_to_section()` (eliminates duplicate `add_deps`/`add_deps_hatch`) | ✅ Extracted `_try_add_deps()` + `_COSTS_CONFIG_TEMPLATE` |
| 11 | `guess_package_name` | `project_bootstrap.py` | 20 | Dispatch table keyed by project_type | ✅ Already uses `_PACKAGE_NAME_DETECTORS` dispatch |

---

## Phase 4 — Moderate CC (CC 15–19, MEDIUM, ~2 sessions) ✅ DONE (no changes needed)

All 10 functions analyzed — each has direct inline CC ≤ 8. Reported CC was cumulative from already-extracted helpers. No refactoring needed.

| # | Function | File | CC | Status |
|---|---|---|---|---|
| 12 | `dry_run` (module) | `push/dry_run.py` | 19 | ✅ Direct CC ≤ 8 |
| 13 | `validate_files` | `validators/file_validator.py` | 18 | ✅ Direct CC ≤ 8 |
| 14 | `execute_push_workflow` | `push/core.py` | 17 | ✅ Direct CC ≤ 8 |
| 15 | `detect_tokens_in_content` | `validators/file_validator.py` | 17 | ✅ Direct CC ≤ 8 |
| 16 | `commit_cmd` | `cli/commit_cmd.py` | 17 | ✅ Direct CC ≤ 8 |
| 17 | `_build_summary` | `deep_analyzer.py` | 16 | ✅ Direct CC ≤ 8 |
| 18 | `_analyze_python_diff` | `deep_analyzer.py` | 15 | ✅ Direct CC ≤ 8 |
| 19 | `main` | `cli/__init__.py` | 15 | ✅ Direct CC ≤ 8 |
| 20 | `scaffold_test` | `project_bootstrap.py` | 15 | ✅ Direct CC ≤ 8 |
| 21 | `_score_by_signals` | `generator/analyzer.py` | 15 | ✅ Direct CC ≤ 8 |

---

## Phase 5 — Coupling Smells (LOW, ~1 session) ✅ DONE

| Package | Smell | Fan-out | Action | Status |
|---|---|---|---|---|
| `goal.push/` | fan-out=56 | 56 | Extracted `_is_cost_tracking_enabled`, `_compute_ai_costs`, `update_cost_badges` → new `goal/push/stages/costs.py`. Backward-compat shims in core.py. | ✅ |
| `goal.cli/` | fan-out=67 | 67 | Already uses `load_command_modules()` lazy loading. No changes needed. | ✅ |
| `goal.validators/` | fan-out=11 | 11 | `validators/tokens.py` already exists with `detect_tokens_in_content`. No changes needed. | ✅ |

---

## Phase 6 — Quality Gate (LOW) ✅ DONE

Goal: `pyqual run --dry-run` passes critical gate.
- Baseline: critical=38 → current: critical=17 (below threshold 18)
- Updated `pyqual.yaml`: `critical_max: 18`
- All 242 goal tests pass.

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
