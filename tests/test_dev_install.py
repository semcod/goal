"""Tests for dev-install detection and wheel-shadows-editable warning."""

import goal
from goal.cli import (
    _editable_goal_markers,
    _is_dev_install,
    _warn_wheel_shadows_editable,
)


def test_dev_install_true_for_source_checkout(monkeypatch):
    monkeypatch.setattr(goal, "__file__", "/home/u/github/proj/goal/goal/__init__.py")
    assert _is_dev_install() is True


def test_dev_install_false_for_wheel(monkeypatch):
    monkeypatch.setattr(
        goal, "__file__", "/venv/lib/python3.13/site-packages/goal/__init__.py"
    )
    assert _is_dev_install() is False


def test_editable_markers_detected(tmp_path):
    (tmp_path / "__editable__.goal-2.1.0.pth").write_text("")
    assert _editable_goal_markers(str(tmp_path))


def test_no_markers_when_absent(tmp_path):
    assert _editable_goal_markers(str(tmp_path)) == []


def test_warn_when_wheel_shadows_editable(tmp_path, monkeypatch, capsys):
    site = tmp_path / "lib" / "python3.13" / "site-packages"
    (site / "goal").mkdir(parents=True)
    (site / "goal" / "__init__.py").write_text("")
    (site / "__editable__.goal-2.1.0.pth").write_text("")  # dev install also present
    monkeypatch.setattr(goal, "__file__", str(site / "goal" / "__init__.py"))

    _warn_wheel_shadows_editable()

    out = capsys.readouterr().out
    assert "shadowing your source changes" in out
    assert "pip install -e" in out


def test_no_warn_when_running_from_source(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(goal, "__file__", str(tmp_path / "goal" / "__init__.py"))
    _warn_wheel_shadows_editable()
    assert capsys.readouterr().out == ""
