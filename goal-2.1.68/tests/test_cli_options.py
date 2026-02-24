import subprocess


def run_cli(*args):
    return subprocess.run(
        ["python3", "-m", "goal.cli", *args],
        capture_output=True,
        text=True,
    )


def test_push_help_includes_markdown_ascii_split_ticket():
    res = run_cli("push", "--help")
    assert res.returncode == 0
    out = res.stdout
    assert "--markdown / --ascii" in out
    assert "--split" in out
    assert "--ticket" in out


def test_status_help_includes_markdown_ascii():
    res = run_cli("status", "--help")
    assert res.returncode == 0
    assert "--markdown / --ascii" in res.stdout


def test_unknown_command_shows_docs_url():
    res = run_cli("nonexistent_command")
    assert res.returncode == 2
    out = res.output if hasattr(res, 'output') else res.stdout + res.stderr
    # The requested command should be mentioned
    assert "does not exist" in out.lower() or "not exist" in out.lower()
    # Documentation URL should be shown
    assert "github.com/wronai/goal" in out or "Documentation:" in out


def test_known_commands_work():
    res = run_cli("--help")
    assert res.returncode == 0
    assert "Usage:" in res.stdout
