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


def test_commit_help_includes_ticket():
    res = run_cli("commit", "--help")
    assert res.returncode == 0
    assert "--ticket" in res.stdout
