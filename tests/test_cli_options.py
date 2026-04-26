import subprocess
from unittest import mock
from click.testing import CliRunner

import goal.cli as goal_cli
from goal.cli import main


def run_cli(*args):
    return subprocess.run(['python3', '-m', 'goal', *args], capture_output=True, text=True)


def test_push_help_includes_markdown_ascii_split_ticket() -> None:
    res = run_cli('push', '--help')
    assert res.returncode == 0
    out = res.stdout
    assert '--markdown / --ascii' in out
    assert '--split' in out
    assert '--ticket' in out


def test_status_help_includes_markdown_ascii() -> None:
    res = run_cli('status', '--help')
    assert res.returncode == 0
    assert '--markdown / --ascii' in res.stdout


def test_unknown_command_shows_docs_url() -> None:
    res = run_cli('nonexistent_command')
    assert res.returncode == 2
    out = res.output if hasattr(res, 'output') else res.stdout + res.stderr
    assert 'does not exist' in out.lower() or 'not exist' in out.lower()
    assert 'github.com/wronai/goal' in out or 'Documentation:' in out


def test_known_commands_work() -> None:
    res = run_cli('--help')
    assert res.returncode == 0
    assert 'Usage:' in res.stdout


def test_all_help_does_not_fail_when_push_unavailable() -> None:
    runner = CliRunner()
    push_cmd = main.commands.pop('push', None)
    try:
        res = runner.invoke(main, ['-a', '--help'])
    finally:
        if push_cmd is not None:
            main.commands['push'] = push_cmd

    assert res.exit_code == 0
    assert 'Usage:' in res.output


def test_missing_push_command_shows_install_hint() -> None:
    runner = CliRunner()
    push_cmd = main.commands.pop('push', None)
    try:
        res = runner.invoke(main, ['push'])
    finally:
        if push_cmd is not None:
            main.commands['push'] = push_cmd

    assert res.exit_code == 2
    assert 'push' in res.output.lower()
    assert 'force-reinstall' in res.output
    assert '-m pip install -U --force-reinstall goal' in res.output


def test_goal_update_command_prefers_active_venv_python(monkeypatch) -> None:
    monkeypatch.setenv('VIRTUAL_ENV', '/tmp/my venv')

    with mock.patch('goal.cli.os.path.exists', return_value=True):
        cmd = goal_cli._goal_update_command()

    assert '/tmp/my venv/bin/python' in cmd
    assert cmd.endswith('-m pip install -U goal')


def test_version_banner_includes_ready_to_run_update_command(monkeypatch, capsys) -> None:
    monkeypatch.setenv('VIRTUAL_ENV', '/tmp/venv')

    with mock.patch('goal.cli.os.path.exists', return_value=True), \
         mock.patch('goal.version_validation.get_pypi_version', return_value='9999.0.0'):
        goal_cli._show_goal_version_banner()

    out = capsys.readouterr().out
    assert 'Update now:' in out
    assert '/tmp/venv/bin/python' in out
    assert '-m pip install -U goal' in out


def test_warn_goal_binary_mismatch_detects_local_venv_without_active_virtual_env(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.venv' / 'bin').mkdir(parents=True)
    (tmp_path / '.venv' / 'bin' / 'python').write_text('')

    monkeypatch.setattr(goal_cli.goal, '__file__', '/home/tom/.local/lib/python3.13/site-packages/goal/__init__.py')

    goal_cli._warn_goal_binary_mismatch()

    out = capsys.readouterr().out
    assert 'project venv exists at' in out
    assert '.venv/bin/python -m pip install -U goal' in out


def test_warn_goal_binary_mismatch_prefers_local_goal_binary_hint(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.delenv('VIRTUAL_ENV', raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.venv' / 'bin').mkdir(parents=True)
    (tmp_path / '.venv' / 'bin' / 'python').write_text('')
    (tmp_path / '.venv' / 'bin' / 'goal').write_text('')

    monkeypatch.setattr(goal_cli.goal, '__file__', '/home/tom/.local/lib/python3.13/site-packages/goal/__init__.py')

    goal_cli._warn_goal_binary_mismatch()

    out = capsys.readouterr().out
    assert 'Prefer:' in out
    assert '.venv/bin/goal' in out