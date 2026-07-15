import subprocess
import sys
from unittest import mock
from click.testing import CliRunner

import goal.cli as goal_cli
from goal.cli import main


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "goal", *args], capture_output=True, text=True
    )


def test_push_help_includes_markdown_ascii_split_ticket() -> None:
    res = run_cli("push", "--help")
    assert res.returncode == 0
    out = res.stdout
    assert "--markdown / --ascii" in out
    assert "--split" in out
    assert "--ticket" in out


def test_status_help_includes_markdown_ascii() -> None:
    res = run_cli("status", "--help")
    assert res.returncode == 0
    assert "--markdown / --ascii" in res.stdout


def test_unknown_command_shows_docs_url() -> None:
    res = run_cli("nonexistent_command")
    assert res.returncode == 2
    out = res.output if hasattr(res, "output") else res.stdout + res.stderr
    assert "does not exist" in out.lower() or "not exist" in out.lower()
    assert "github.com/wronai/goal" in out or "Documentation:" in out


def test_known_commands_work() -> None:
    res = run_cli("--help")
    assert res.returncode == 0
    assert "Usage:" in res.stdout


def test_all_help_does_not_fail_when_push_unavailable() -> None:
    runner = CliRunner()
    push_cmd = main.commands.pop("push", None)
    try:
        res = runner.invoke(main, ["-a", "--help"])
    finally:
        if push_cmd is not None:
            main.commands["push"] = push_cmd

    assert res.exit_code == 0
    assert "Usage:" in res.output


def test_missing_push_command_shows_install_hint() -> None:
    runner = CliRunner()
    push_cmd = main.commands.pop("push", None)
    try:
        res = runner.invoke(main, ["push"])
    finally:
        if push_cmd is not None:
            main.commands["push"] = push_cmd

    assert res.exit_code == 2
    assert "push" in res.output.lower()
    assert "force-reinstall" in res.output
    assert "-m pip install -U --force-reinstall goal" in res.output


def test_goal_update_command_prefers_active_venv_python(monkeypatch) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/tmp/my venv")

    with mock.patch("goal.cli.os.path.exists", return_value=True):
        cmd = goal_cli._goal_update_command()

    assert "/tmp/my venv/bin/python" in cmd
    assert cmd.endswith("-m pip install -U goal")


def test_version_banner_includes_ready_to_run_update_command(
    monkeypatch, capsys
) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/tmp/venv")

    with (
        mock.patch("goal.cli.os.path.exists", return_value=True),
        mock.patch("goal.cli._is_dev_install", return_value=False),
        mock.patch("goal.version_validation.get_pypi_version", return_value="9999.0.0"),
    ):
        goal_cli._show_goal_version_banner()

    out = capsys.readouterr().out
    assert "Update now:" in out
    assert "/tmp/venv/bin/python" in out
    assert "-m pip install -U goal" in out


def test_warn_goal_binary_mismatch_detects_local_venv_without_active_virtual_env(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("")

    monkeypatch.setattr(
        goal_cli.goal,
        "__file__",
        "/home/tom/.local/lib/python3.13/site-packages/goal/__init__.py",
    )

    goal_cli._warn_goal_binary_mismatch()

    out = capsys.readouterr().out
    assert "project venv exists at" in out
    assert ".venv/bin/python -m pip install -U goal" in out


def test_warn_goal_binary_mismatch_prefers_local_goal_binary_hint(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("")
    (tmp_path / ".venv" / "bin" / "goal").write_text("")

    monkeypatch.setattr(
        goal_cli.goal,
        "__file__",
        "/home/tom/.local/lib/python3.13/site-packages/goal/__init__.py",
    )

    goal_cli._warn_goal_binary_mismatch()

    out = capsys.readouterr().out
    assert "Prefer:" in out
    assert ".venv/bin/goal" in out


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr=stderr)


def test_auto_update_goal_retries_with_no_cache_dir_after_crash(monkeypatch, capsys) -> None:
    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if len(calls) == 1:
            return _completed(-11)  # SIGSEGV on first attempt
        return _completed(0)

    monkeypatch.setattr(goal_cli, "_run_pip_update", fake_run)

    ok = goal_cli._auto_update_goal("1.0.0", "2.0.0")

    assert ok is True
    assert len(calls) == 2
    assert "--no-cache-dir" not in calls[0]
    assert "--no-cache-dir" in calls[1]
    assert "retrying" in capsys.readouterr().out.lower()


def test_auto_update_goal_reports_diagnosis_after_persistent_crash(monkeypatch, capsys) -> None:
    monkeypatch.setattr(goal_cli, "_run_pip_update", lambda cmd: _completed(-11))
    monkeypatch.setattr(
        goal_cli, "_diagnose_broken_python_env", lambda: "broken venv: mismatched pyvenv.cfg"
    )

    ok = goal_cli._auto_update_goal("1.0.0", "2.0.0")

    out = capsys.readouterr().out
    assert ok is False
    assert "signal 11" in out or "sygna" in out
    assert "broken venv: mismatched pyvenv.cfg" in out


def test_auto_update_goal_reports_stderr_for_normal_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        goal_cli, "_run_pip_update", lambda cmd: _completed(1, stderr="no matching distribution")
    )

    ok = goal_cli._auto_update_goal("1.0.0", "2.0.0")

    out = capsys.readouterr().out
    assert ok is False
    assert "no matching distribution" in out


def test_maybe_self_update_skips_when_noninteractive_without_yes(monkeypatch) -> None:
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    called = []
    monkeypatch.setattr(goal_cli, "_auto_update_goal", lambda *a: called.append(a))

    goal_cli._maybe_self_update("9.9.9", yes=False)

    assert called == []


def test_maybe_self_update_skips_when_no_newer_version(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(goal_cli, "_auto_update_goal", lambda *a: called.append(a))

    goal_cli._maybe_self_update(None, yes=True)

    assert called == []


def test_maybe_self_update_runs_without_prompt_when_yes(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(goal_cli, "_auto_update_goal", lambda *a: called.append(a))
    # A stray confirm() would fail the test (no input available in CI).
    monkeypatch.setattr(
        goal_cli.click,
        "confirm",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not prompt")),
    )

    goal_cli._maybe_self_update("9.9.9", yes=True)

    assert len(called) == 1


def test_diagnose_broken_python_env_detects_version_mismatch(monkeypatch, tmp_path) -> None:
    venv_dir = tmp_path / "venv"
    (venv_dir / "bin").mkdir(parents=True)
    (venv_dir / "bin" / "python3").write_text("")
    (venv_dir / "pyvenv.cfg").write_text("home = /some/other/python/bin\nversion = 9.99.99\n")

    monkeypatch.setattr(goal_cli.sys, "prefix", str(venv_dir))
    monkeypatch.setattr(goal_cli.sys, "base_prefix", "/usr")

    diagnosis = goal_cli._diagnose_broken_python_env()

    assert diagnosis is not None
    assert "niespójne środowisko venv" in diagnosis
    assert "9.99.99" in diagnosis


def test_diagnose_broken_python_env_returns_none_outside_venv(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(goal_cli.sys, "prefix", "/usr")
    monkeypatch.setattr(goal_cli.sys, "base_prefix", "/usr")

    assert goal_cli._diagnose_broken_python_env() is None
