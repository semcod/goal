"""Governed badge opt-out must not install the optional tracking dependency."""
from pathlib import Path
from unittest.mock import Mock

import pytest

from goal.bootstrap import costs_badge


def test_read_only_badge_optout_runs_no_dependency_probe(monkeypatch):
    monkeypatch.setenv("GOAL_BOOTSTRAP_READ_ONLY", "1")
    monkeypatch.setenv("GOAL_SKIP_COSTS_BADGE", "1")
    run = Mock(side_effect=AssertionError("optional dependency subprocess"))
    install = Mock(side_effect=AssertionError("optional network installation"))
    monkeypatch.setattr(costs_badge.subprocess, "run", run)
    monkeypatch.setattr(costs_badge, "_install_costs_requirement", install)
    assert costs_badge._install_costs_package(Path("."), "python")
    run.assert_not_called()
    install.assert_not_called()


@pytest.mark.parametrize("flags", [(), ("GOAL_SKIP_COSTS_BADGE",), ("GOAL_BOOTSTRAP_READ_ONLY",)])
def test_other_bootstrap_modes_still_check_costs(monkeypatch, flags):
    for flag in ("GOAL_SKIP_COSTS_BADGE", "GOAL_BOOTSTRAP_READ_ONLY"):
        monkeypatch.delenv(flag, raising=False)
    for flag in flags:
        monkeypatch.setenv(flag, "1")
    run = Mock(return_value=Mock(returncode=0, stdout="0.2.1\n"))
    monkeypatch.setattr(costs_badge.subprocess, "run", run)
    assert costs_badge._install_costs_package(Path("."), "python")
    run.assert_called_once()
