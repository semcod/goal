"""A skipped test stage is not evidence that tests executed successfully."""
from unittest.mock import patch

import click
import pytest
import yaml

from goal import formatter
from goal.push.stages.test import run_test_stage


def stage(project_types, *, yes=True, context=None):
    context = {} if context is None else context
    result = run_test_stage(project_types, yes, False, context, [], {}, "1", "1", "test", "")
    return result, context


@pytest.mark.parametrize("yes", [False, True])
def test_empty_selection_does_not_run_commands_or_read_stale_junit(tmp_path, monkeypatch, capsys, yes):
    monkeypatch.chdir(tmp_path)
    stale = tmp_path / ".goal_test_report.xml"
    stale.write_text('<testsuite><testcase name="old" time="37"/></testsuite>')
    context = {"test_details": {"status": "passed", "slow_tests": [{"name": "previous"}]}}
    with patch("goal.push.stages.test.run_tests") as runner, patch(
        "goal.cli.tests.get_test_execution_details"
    ) as details, patch("goal.push.stages.test.confirm") as confirm:
        result, context = stage([], yes=yes, context=context)
    assert result == ("No project tests selected", 0)
    assert context["test_details"] == {
        "status": "not_selected", "wall_time": 0.0, "total_test_time": 0.0,
        "startup_overhead": 0.0, "slow_tests": [],
    }
    runner.assert_not_called();details.assert_not_called();confirm.assert_not_called()
    output = capsys.readouterr().out
    assert "No project tests selected" in output and "delivery checks" in output
    assert "All tests passed" not in output and "Tests passed" not in output
    assert stale.read_text() == '<testsuite><testcase name="old" time="37"/></testsuite>'


def test_explicit_opt_out_clears_previous_metrics(capsys):
    with patch("goal.push.stages.test.confirm", return_value=False), patch(
        "goal.push.stages.test.run_tests"
    ) as runner, patch("goal.cli.tests.get_test_execution_details") as details:
        result, context = stage(["python"], yes=False)
    assert result == ("Tests skipped", 0)
    assert context["test_details"]["status"] == "skipped"
    assert context["test_details"]["slow_tests"] == []
    runner.assert_not_called();details.assert_not_called()
    assert "passed" not in capsys.readouterr().out


@pytest.mark.parametrize("success", [True, False])
@pytest.mark.parametrize("yes", [True, False])
def test_selected_project_preserves_real_runner_outcome(success, yes):
    metrics = {"wall_time": 2.0, "total_test_time": 1.0, "startup_overhead": 1.0, "slow_tests": []}
    with patch("goal.push.stages.test.confirm", return_value=True), patch(
        "goal.push.stages.test.run_tests", return_value=success
    ) as runner, patch("goal.cli.tests.get_test_execution_details", return_value=metrics.copy()):
        result, context = stage(["python"], yes=yes)
    assert result == ("Tests passed" if success else "Tests failed", 0 if success else 1)
    assert context["test_details"] == {**metrics, "status": "passed" if success else "failed"}
    assert runner.call_args.args == (["python"],)


@pytest.mark.parametrize("status", ["not_selected", "skipped"])
@pytest.mark.parametrize("mode", ["yaml", "markdown"])
def test_final_reports_keep_unexecuted_status(status, mode, capsys):
    from goal.push.core import output_final_summary
    details = {"status": status, "wall_time": 0.0, "total_test_time": 0.0,
               "startup_overhead": 0.0, "slow_tests": []}
    output_final_summary(
        ctx_obj={"yes": True, "markdown": mode == "markdown", "test_details": details},
        markdown=mode == "markdown", project_types=[], files=[], stats={}, current_version="1",
        new_version="1", commit_msg="test: report", commit_body=None, test_exit_code=0,
        publish_success=False, no_tag=True, publish_skip_reason="no_registry_project_types",
    )
    output = capsys.readouterr().out
    if mode == "yaml":
        payload = output.split("=== GOAL RESULT (YAML) ===\n", 1)[1].rsplit("==========================", 1)[0]
        assert yaml.safe_load(payload)["goal_summary"]["test_execution"]["status"] == status
    else:
        assert f"**Status:** {status}" in output
    assert "Tests passed" not in output and "Ran tests" not in output


@pytest.mark.parametrize("exit_code,details,types,expected", [
    (0, {}, [], "not_selected"), (0, {}, ["python"], "passed"),
    (1, {"status": "not_selected"}, [], "failed"),
    (0, {"status": "failed"}, [], "failed"),
    (0, {"status": {}}, [], "unknown"),
])
def test_status_projection_preserves_failure_and_legacy_typed_callers(exit_code, details, types, expected):
    assert formatter.resolve_test_execution_status(exit_code, details, types) == expected


def test_empty_project_selection_cannot_bypass_required_delivery_gate():
    from goal.governance.delivery import DeliveryPolicy
    from goal.push import core
    policy = DeliveryPolicy("pull-request", True, ("pull-request",), "origin", "main", True)
    context = {"yes": True, "markdown": False, "config": {}, "user_config": {},
               "delivery_mode": "pull-request", "all_flags": True}
    with patch("goal.governance.delivery.resolve_delivery_policy", return_value=policy), patch(
        "goal.governance.delivery.validate_delivery_ready",
        side_effect=click.ClickException("declared delivery check failed"),
    ) as gate, patch("goal.push.core._detect_project_types", return_value=[]), patch(
        "goal.push.core.run_test_stage"
    ) as tests, patch("goal.push.core._handle_commit_phase") as commit, patch(
        "goal.governance.delivery.deliver_pull_request"
    ) as publish, pytest.raises(click.ClickException, match="declared delivery check failed"):
        core.execute_push_workflow(
            ctx_obj=context, bump="patch", no_tag=True, no_changelog=True, no_version_sync=True,
            message=None, dry_run=False, yes=True, markdown=False, split=False,
            ticket="ticket-234", abstraction=None, todo=False,
        )
    gate.assert_called_once();tests.assert_not_called();commit.assert_not_called();publish.assert_not_called()
