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


def test_active_venv_python_is_preferred_for_root_run(monkeypatch):
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

    mock_find_python_bin.assert_not_called()
    commands = [call.args[0] for call in mock_run.call_args_list]
    assert ["/tmp/venv-active/bin/python", "-c", "import pytest"] in commands
    assert ["/tmp/venv-active/bin/python", "-m", "pytest"] in commands


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
    assert _rewrite_bash_pytest_for_uv(cmd, has_uv=True) == "uv run pytest tests/ -v"
    assert _rewrite_bash_pytest_for_uv(cmd, has_uv=False) is None


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
