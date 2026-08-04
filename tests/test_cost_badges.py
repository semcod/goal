"""Tests for AI cost badge integration in the push workflow."""

from __future__ import annotations

import sys
import types
import importlib.util
from pathlib import Path


def test_update_cost_badges_resyncs_badge_version(tmp_path, monkeypatch):
    """Goal should correct stale version badges after the costs package writes README."""
    module_path = Path(__file__).resolve().parents[1] / "goal/push/stages/costs.py"
    spec = importlib.util.spec_from_file_location("goal_push_stage_costs_test", module_path)
    assert spec is not None and spec.loader is not None
    costs_stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(costs_stage)

    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    fake_costs = types.ModuleType("costs")

    def fake_update_readme_badge(project_dir: Path, _results: dict) -> bool:
        (Path(project_dir) / "README.md").write_text(
            "## AI Cost Tracking\n\n"
            "![Version](https://img.shields.io/badge/version-0.1.31-blue)\n\n"
            "---\n\n",
            encoding="utf-8",
        )
        return True

    fake_costs.update_readme_badge = fake_update_readme_badge
    fake_costs.calculate_human_time = lambda _commits: 0.0

    fake_git_parser = types.ModuleType("costs.git_parser")
    fake_git_parser.get_repo_stats = lambda _path: {}

    monkeypatch.setitem(sys.modules, "costs", fake_costs)
    monkeypatch.setitem(sys.modules, "costs.git_parser", fake_git_parser)
    monkeypatch.setattr(costs_stage, "_compute_ai_costs", lambda *args: (1.23, 7, []))

    updated = costs_stage.update_cost_badges({}, "0.1.351")

    content = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert updated is True
    assert "version-0.1.351-blue" in content
    assert "version-0.1.31-blue" not in content
