"""Regression tests for the push/core.py split (STARTER-018).

``goal/push/core.py`` was flagged as a large/hot module. Cohesive helpers were
already extracted into sibling submodules (``preview.py``, ``tickets.py``,
``stages/costs.py``). These tests lock in the behavior of the extracted units
*and* the re-export contract that lets callers keep importing them from
``goal.push.core`` (and ``goal.push``), so the dedup of the in-core copies is a
behavior-preserving change.
"""

import sys
from pathlib import Path

# Add project root to path (matches other push test modules)
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# show_workflow_preview — rendering math and dual-format output
# ---------------------------------------------------------------------------


def test_show_workflow_preview_plain_format(capsys):
    from goal.push.core import show_workflow_preview

    files = ["a.py", "b.py"]
    # adds/dels tuples per file
    stats = {"a.py": (10, 2), "b.py": (5, 3)}

    show_workflow_preview(
        files=files,
        stats=stats,
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="feat: thing",
        commit_body=None,
        markdown=False,
        ctx_obj={},
    )

    out = capsys.readouterr().out
    assert "=== GOAL Workflow ===" in out  # plain header
    assert "Will commit 2 files" in out
    # NET = (10+5) - (2+3) = 15 - 5 = 10
    assert "NET 10" in out
    # deletion pct = 5 / 20 = 25%
    assert "25% churn deletions" in out
    assert "1.0.0 -> 1.1.0" in out


def test_show_workflow_preview_markdown_format(capsys):
    from goal.push.core import show_workflow_preview

    show_workflow_preview(
        files=["a.py"],
        stats={"a.py": (4, 1)},
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="fix: x",
        commit_body="body line",
        markdown=True,
        ctx_obj={},
    )

    out = capsys.readouterr().out
    assert "## GOAL Workflow Preview" in out  # markdown header
    assert "**Files:** 1" in out
    assert "**Version:** 1.0.0 → 1.1.0" in out
    assert "**Commit:** `fix: x`" in out
    assert "```" in out  # commit body fenced


def test_show_workflow_preview_markdown_via_ctx_obj(capsys):
    """markdown flag can also be driven by ctx_obj['markdown']."""
    from goal.push.core import show_workflow_preview

    show_workflow_preview(
        files=["a.py"],
        stats={"a.py": (1, 0)},
        current_version="1.0.0",
        new_version="1.0.0",
        commit_msg="x",
        commit_body=None,
        markdown=False,
        ctx_obj={"markdown": True},
    )

    assert "## GOAL Workflow Preview" in capsys.readouterr().out


def test_show_workflow_preview_handles_empty_stats(capsys):
    """No divisions-by-zero when nothing is staged."""
    from goal.push.core import show_workflow_preview

    show_workflow_preview(
        files=[],
        stats={},
        current_version="1.0.0",
        new_version="1.0.0",
        commit_msg="x",
        commit_body=None,
        markdown=False,
        ctx_obj={},
    )

    out = capsys.readouterr().out
    assert "NET 0" in out
    assert "0% churn deletions" in out


# ---------------------------------------------------------------------------
# _build_publish_summary — pure leaf helper, all four branches
# ---------------------------------------------------------------------------


def test_build_publish_summary_passed():
    from goal.push.core import _build_publish_summary

    assert _build_publish_summary(
        publish_success=True,
        publish_required=True,
        publish_skip_reason=None,
    ) == {"status": "passed"}


def test_build_publish_summary_skipped_with_reason():
    from goal.push.core import _build_publish_summary

    assert _build_publish_summary(
        publish_success=False,
        publish_required=False,
        publish_skip_reason="no_package_source_changes",
    ) == {"status": "skipped", "reason": "no_package_source_changes"}


def test_build_publish_summary_failed():
    from goal.push.core import _build_publish_summary

    assert _build_publish_summary(
        publish_success=False,
        publish_required=True,
        publish_skip_reason=None,
    ) == {"status": "failed"}


def test_build_publish_summary_skipped_default():
    from goal.push.core import _build_publish_summary

    assert _build_publish_summary(
        publish_success=False,
        publish_required=False,
        publish_skip_reason=None,
    ) == {"status": "skipped"}


# ---------------------------------------------------------------------------
# add_slow_test_tickets_to_planfile — threshold, dedupe, idempotency
# ---------------------------------------------------------------------------


def _write_empty_planfile(tmp_path):
    planfile = tmp_path / "project" / "planfile-tickets.yaml"
    planfile.parent.mkdir()
    planfile.write_text("tickets: []\n")
    return planfile


def test_slow_test_threshold_filters_out_fast_tests(tmp_path, monkeypatch):
    """Tests under the 1.0s threshold must NOT create tickets (STARTER-018
    guard against flooding the planfile with subprocess-startup noise)."""
    import yaml

    from goal.push.core import add_slow_test_tickets_to_planfile

    monkeypatch.chdir(tmp_path)
    planfile = _write_empty_planfile(tmp_path)
    # os.path.exists is consulted to map classname->file; stub to True.
    monkeypatch.setattr("os.path.exists", lambda _: True)

    details = {
        "slow_tests": [
            {"classname": "tests.x", "name": "slow", "duration": 2.5},
            {"classname": "tests.y", "name": "fast", "duration": 0.6},
        ],
        "startup_overhead": 0.0,
    }

    added = add_slow_test_tickets_to_planfile(details)

    assert len(added) == 1
    assert "slow" in added[0]
    data = yaml.safe_load(planfile.read_text())
    assert len(data["tickets"]) == 1


def test_slow_test_ticket_dedup_is_idempotent(tmp_path, monkeypatch):
    """Re-running on the same details must not duplicate the ticket."""
    import yaml

    from goal.push.core import add_slow_test_tickets_to_planfile

    monkeypatch.chdir(tmp_path)
    planfile = _write_empty_planfile(tmp_path)
    monkeypatch.setattr("os.path.exists", lambda _: True)

    details = {
        "slow_tests": [
            {"classname": "tests.a", "name": "t", "duration": 1.5},
        ],
        "startup_overhead": 0.0,
    }

    add_slow_test_tickets_to_planfile(details)
    second = add_slow_test_tickets_to_planfile(details)

    assert second == []  # nothing added on the second pass
    data = yaml.safe_load(planfile.read_text())
    assert len(data["tickets"]) == 1


def test_slow_test_startup_overhead_ticket(tmp_path, monkeypatch):
    """A startup_overhead above 3.0s adds the dedicated overhead ticket."""
    import yaml

    from goal.push.core import add_slow_test_tickets_to_planfile

    monkeypatch.chdir(tmp_path)
    planfile = _write_empty_planfile(tmp_path)
    monkeypatch.setattr("os.path.exists", lambda _: True)

    details = {"slow_tests": [], "startup_overhead": 4.2}

    added = add_slow_test_tickets_to_planfile(details)

    assert added == ["Address high test suite startup overhead"]
    data = yaml.safe_load(planfile.read_text())
    assert data["tickets"][0]["priority"] == "high"
    assert "startup-overhead" in data["tickets"][0]["labels"]


def test_slow_test_no_planfile_returns_empty(tmp_path, monkeypatch):
    from goal.push.core import add_slow_test_tickets_to_planfile

    monkeypatch.chdir(tmp_path)
    # No planfile-tickets.yaml present at all.
    assert add_slow_test_tickets_to_planfile({"slow_tests": []}) == []


# ---------------------------------------------------------------------------
# Re-export contract — core re-exports the extracted submodule symbols
# ---------------------------------------------------------------------------


def test_core_reexports_preview_symbol():
    """core.show_workflow_preview must be the same object as the extracted
    preview.show_workflow_preview (no divergent duplicate)."""
    from goal.push import core, preview

    assert core.show_workflow_preview is preview.show_workflow_preview


def test_core_reexports_tickets_symbol():
    """core.add_slow_test_tickets_to_planfile must be the same object as the
    extracted tickets.add_slow_test_tickets_to_planfile."""
    from goal.push import core, tickets

    assert (
        core.add_slow_test_tickets_to_planfile
        is tickets.add_slow_test_tickets_to_planfile
    )


def test_package_reexports_preview_symbol():
    """The push package __init__ must still re-export the preview symbol."""
    from goal.push import show_workflow_preview
    from goal.push.preview import show_workflow_preview as direct

    assert show_workflow_preview is direct


# ---------------------------------------------------------------------------
# PushContext — thin wrapper used as the click context object
# ---------------------------------------------------------------------------


def test_push_context_get_returns_value_and_default():
    from goal.push.core import PushContext

    ctx = PushContext({"yes": True, "markdown": False})

    assert ctx.get("yes") is True
    assert ctx.get("missing") is None
    assert ctx.get("missing", "fallback") == "fallback"
