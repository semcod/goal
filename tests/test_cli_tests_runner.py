from pathlib import Path
from unittest.mock import MagicMock, patch


from goal.cli import tests as cli_tests


def test_find_python_test_dirs_deduplicates_project_roots_and_prefers_tests_dir(
    tmp_path, monkeypatch
):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="root"\nversion="0.1.0"\n'
    )

    svc_a = tmp_path / "svc_a"
    (svc_a / "tests").mkdir(parents=True)
    (svc_a / "src").mkdir(parents=True)
    (svc_a / "pyproject.toml").write_text('[project]\nname="svc-a"\nversion="0.1.0"\n')
    (svc_a / "tests" / "test_one.py").write_text("def test_one():\n    assert True\n")
    (svc_a / "src" / "test_internal.py").write_text(
        "def test_internal():\n    assert True\n"
    )

    svc_b = tmp_path / "svc_b"
    (svc_b / "src").mkdir(parents=True)
    (svc_b / "pyproject.toml").write_text('[project]\nname="svc-b"\nversion="0.1.0"\n')
    (svc_b / "src" / "test_two.py").write_text("def test_two():\n    assert True\n")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_root.py").write_text(
        "def test_root():\n    assert True\n"
    )

    monkeypatch.chdir(tmp_path)
    dirs = cli_tests._find_python_test_dirs()

    assert set(dirs) == {"svc_a/tests", "svc_b"}


def test_resolve_project_python_returns_absolute_project_python():
    with patch(
        "goal.cli.tests._find_python_bin", return_value="svc_a/.venv/bin/python"
    ):
        resolved = cli_tests._resolve_project_python(Path("svc_a"), "/fallback/python")

    assert resolved.endswith("svc_a/.venv/bin/python")
    assert Path(resolved).is_absolute()


def test_ensure_pytest_for_project_tries_multiple_install_strategies():
    with patch("goal.cli.tests.subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1),  # import pytest check
            MagicMock(returncode=1),  # install -e .[dev]
            MagicMock(returncode=0),  # install -e .
            MagicMock(returncode=0),  # verify import pytest
        ]

        ok = cli_tests._ensure_pytest_for_project(Path("/repo/svc"), "/usr/bin/python3")

    assert ok is True

    calls = [call.args[0] for call in mock_run.call_args_list]
    assert calls[0] == ["/usr/bin/python3", "-c", "import pytest"]
    assert calls[1] == ["/usr/bin/python3", "-m", "pip", "install", "-e", ".[dev]"]
    assert calls[2] == ["/usr/bin/python3", "-m", "pip", "install", "-e", "."]
    assert calls[3] == ["/usr/bin/python3", "-c", "import pytest"]


def test_local_venv_preferred_over_stale_active_venv_for_root_run(monkeypatch):
    """A VIRTUAL_ENV left active from an unrelated project must not override
    the current project's own venv, or `goal test`/`goal push` silently runs
    the wrong project's tests with the wrong interpreter."""
    monkeypatch.setenv("VIRTUAL_ENV", "/tmp/venv-active")

    with (
        patch("goal.cli.tests.Path.exists", return_value=True),
        patch(
            "goal.cli.tests._find_python_bin",
            return_value="/tmp/other/.venv/bin/python",
        ) as mock_find_python_bin,
        patch("goal.cli.tests._find_python_test_dirs", return_value=[]),
        patch("goal.cli.tests.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        assert cli_tests.run_tests(["python"]) is True

    mock_find_python_bin.assert_called_once()
    commands = [call.args[0] for call in mock_run.call_args_list]
    assert ["/tmp/other/.venv/bin/python", "-c", "import pytest"] in commands
    assert ["/tmp/other/.venv/bin/python", "-m", "pytest"] in commands


def test_run_tests_uses_configured_python_strategy_and_skips_subdir_scan():
    config = MagicMock()
    config.get_strategy.return_value = {
        "test": "pytest tests/ -v --ignore=my-api --ignore=test-api-qwen"
    }

    with (
        patch("goal.cli.tests.run_command") as mock_run_command,
        patch("goal.cli.tests._run_tests_in_subdirs") as mock_run_subdirs,
        patch("goal.cli.tests.subprocess.run") as mock_subprocess_run,
    ):
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),  # import pytest check
            MagicMock(returncode=0),  # actual pytest run
        ]

        assert cli_tests.run_tests(["python"], config=config) is True

    mock_run_command.assert_not_called()
    mock_run_subdirs.assert_not_called()
    commands = [call.args[0] for call in mock_subprocess_run.call_args_list]
    assert len(commands) == 2

    check_cmd, run_cmd = commands
    assert check_cmd[1:] == ["-c", "import pytest"]
    assert run_cmd[1:4] == ["-m", "pytest", "tests/"]
    assert "--ignore=my-api" in run_cmd
    assert "--ignore=test-api-qwen" in run_cmd
    assert check_cmd[0] == run_cmd[0]


def test_rewrite_bash_pytest_for_uv_converts_goal_yaml_style_command():
    from goal.cli.tests import _rewrite_bash_pytest_for_uv

    cmd = "bash -lc './.venv/bin/python -m pytest tests/ -v'"
    with patch("goal.cli.tests._pytest_importable", return_value=False):
        assert (
            _rewrite_bash_pytest_for_uv(cmd, has_uv=True, python_bin="/usr/bin/python3")
            == "uv run pytest tests/ -v"
        )
    with patch("goal.cli.tests._pytest_importable", return_value=True):
        assert (
            _rewrite_bash_pytest_for_uv(
                cmd, has_uv=True, python_bin="/tmp/venv/bin/python"
            )
            is None
        )
    assert (
        _rewrite_bash_pytest_for_uv(cmd, has_uv=False, python_bin="/usr/bin/python3")
        is None
    )


def test_build_python_test_command_prefers_venv_pytest_when_importable(monkeypatch):
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)

    with (
        patch(
            "goal.cli.tests._find_python_bin",
            return_value="/tmp/project/.venv/bin/python",
        ),
        patch("goal.cli.tests._pytest_importable", return_value=True),
        patch("shutil.which", return_value="/usr/bin/uv"),
    ):
        cmd, use_subprocess, python_bin = cli_tests._build_python_test_command(
            "pytest tests/ -v", "pytest tests/ -v"
        )

    assert cmd[:3] == ["/tmp/project/.venv/bin/python", "-m", "pytest"]
    assert use_subprocess is True
    assert python_bin == "/tmp/project/.venv/bin/python"


def test_display_test_error_names_path_exit_code_and_shows_tail(capsys):
    """A failing subproject must be named with its exit code, and the runner's
    tail (not its head) must be printed — otherwise the culprit is invisible
    among green collection/dot output and costs an hour of bisection."""
    from subprocess import CompletedProcess

    from goal.cli.tests import _FAILURE_TAIL_LINES, _display_test_error

    # Lots of leading "green" collection noise, real failure only at the end.
    head_lines = [f"collected line {i}" for i in range(40)]
    tail_marker = "FAILED tests/test_x.py::test_y"
    summary = "1 failed in 0.05s"
    stdout = "\n".join(head_lines + [tail_marker, summary]) + "\n"
    result = CompletedProcess(
        args=["pytest"], returncode=1, stdout=stdout, stderr="a warning\n"
    )

    _display_test_error(result, "svc_a/tests", "python")

    captured = capsys.readouterr().out
    # The culprit is named with its exit code.
    assert "failed in: svc_a/tests (exit 1)" in captured
    # The tail (with the real failure) is shown.
    assert tail_marker in captured
    assert summary in captured
    assert "a warning" in captured
    # Exactly the last n lines of stdout survive; the head is dropped.
    # Compare as whole stripped lines — "collected line 1" is a substring of
    # "collected line 18", so substring checks would lie.
    all_lines = head_lines + [tail_marker, summary]
    n = _FAILURE_TAIL_LINES
    rendered = [ln.strip() for ln in captured.splitlines()]
    for line in all_lines[-n:]:
        assert line in rendered
    for line in all_lines[:-n]:
        assert line not in rendered


def test_run_tests_names_project_type_on_unexpected_exception(monkeypatch, capsys):
    """run_tests() must not silently swallow an exception raised before any
    subprocess test even ran (e.g. a bug in strategy/config resolution) --
    otherwise the top-level 'Tests failed' has zero diagnostic value and
    every individual subproject looks green because none of them actually
    ran (2026-07-03 incident: an hour of manual bisection to find nothing,
    because the real failure was in aggregation, not in any subproject)."""
    monkeypatch.setattr(
        cli_tests,
        "_run_project_type_tests",
        MagicMock(side_effect=KeyError("test_command")),
    )

    success = cli_tests.run_tests(["python"], config=None)

    assert success is False
    captured = capsys.readouterr().out
    assert "failed in: python" in captured
    assert "KeyError" in captured
    assert "test_command" in captured


def test_run_tests_still_succeeds_when_no_exception(monkeypatch):
    monkeypatch.setattr(cli_tests, "_run_project_type_tests", MagicMock(return_value=True))
    assert cli_tests.run_tests(["python"], config=None) is True


def test_tail_returns_last_n_lines_and_handles_empty():
    from goal.cli.tests import _tail

    assert _tail(None) == ""
    assert _tail("") == ""
    assert _tail("only one line") == "only one line"
    text = "\n".join(str(i) for i in range(10))
    assert _tail(text, n=3) == "7\n8\n9"


def test_get_test_execution_details_and_planfile_update(tmp_path, monkeypatch):
    import yaml
    from goal.cli.tests import get_test_execution_details
    from goal.push.core import add_slow_test_tickets_to_planfile

    # Create dummy XML test report
    report_xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="0" failures="0" skipped="0" tests="2" time="3.5">
    <testcase classname="tests.test_slow" name="test_one" time="1.2" />
    <testcase classname="tests.test_fast" name="test_two" time="0.1" />
  </testsuite>
</testsuites>
"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".goal_test_report.xml").write_text(report_xml)

    # Set mock wall time
    monkeypatch.setattr("goal.cli.tests._last_test_wall_time", 4.0)

    # Retrieve test details
    details = get_test_execution_details()

    assert details["wall_time"] == 4.0
    assert abs(details["total_test_time"] - 1.3) < 1e-5  # 1.2 + 0.1
    assert abs(details["startup_overhead"] - 2.7) < 1e-5  # 4.0 - 1.3
    assert len(details["slow_tests"]) == 2
    assert details["slow_tests"][0]["name"] == "test_one"
    assert details["slow_tests"][0]["duration"] == 1.2

    # Check XML cleanup
    assert not (tmp_path / ".goal_test_report.xml").exists()

    # Now verify planfile update logic
    planfile = tmp_path / "project" / "planfile-tickets.yaml"
    planfile.parent.mkdir()
    planfile.write_text("tickets: []\n")

    # Let's mock os.path.exists to return true for test files
    monkeypatch.setattr("os.path.exists", lambda x: True)

    added = add_slow_test_tickets_to_planfile(details)

    assert "Address slow test: tests.test_slow.test_one" in added

    # Read the updated planfile
    data = yaml.safe_load(planfile.read_text())
    assert len(data["tickets"]) == 1
    assert data["tickets"][0]["title"] == "Address slow test: tests.test_slow.test_one"
    assert data["tickets"][0]["priority"] == "medium"
    assert data["tickets"][0]["labels"] == ["llm-ready", "test-optimization", "slow-test"]
