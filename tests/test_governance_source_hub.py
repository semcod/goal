"""Tests for the maintained new-project source-hub health contract."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from goal.governance import delivery


def _hub(tmp_path: Path, *, suites: tuple[str, ...] = ("alpha.test.sh", "beta.test.sh")) -> Path:
    root = tmp_path / "new-project"
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "governance").mkdir()
    (root / "scripts").mkdir()
    (root / "tests").mkdir()
    (root / "governance" / "manifest.default.json").write_text(
        json.dumps({"schema": "test"}), encoding="utf-8"
    )
    (root / "governance" / "package-manifest.json").write_text(
        json.dumps({"schema": "package"}), encoding="utf-8"
    )
    (root / "scripts" / "check_required_checks.py").write_text(
        "print('required checks: PASS')\n", encoding="utf-8"
    )
    workflow_lines = ["jobs:", "  test:", "    steps:"]
    for suite in suites:
        (root / "tests" / suite).write_text(
            "#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"
        )
        workflow_lines.append(f"      - run: bash tests/{suite}")
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "\n".join(workflow_lines) + "\n", encoding="utf-8"
    )
    return root


def test_source_hub_health_validates_json_and_runs_each_declared_check(tmp_path):
    root = _hub(tmp_path)
    commands: list[list[str]] = []

    def runner(command, **_kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(
            command, 0, "check: PASS\n", "expected negative fixture\n"
        )

    result = delivery.run_source_hub_health(root, runner=runner)

    assert result.returncode == 0
    assert result.completed_checks == 3
    assert "GOV-HUB-PASS" in result.stdout
    assert result.stderr == ""
    assert commands[0][-1].endswith("scripts/check_required_checks.py")
    assert [Path(command[-1]).name for command in commands[1:]] == [
        "alpha.test.sh",
        "beta.test.sh",
    ]


def test_source_hub_health_fails_before_execution_for_invalid_json(tmp_path):
    root = _hub(tmp_path)
    (root / "governance" / "broken.json").write_text("{", encoding="utf-8")
    invoked = False

    def runner(*_args, **_kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("runner must not be called")

    result = delivery.run_source_hub_health(root, runner=runner)

    assert result.returncode == 1
    assert "invalid canonical JSON governance/broken.json" in result.stderr
    assert invoked is False


def test_source_hub_health_fails_when_suite_is_not_wired_into_ci(tmp_path):
    root = _hub(tmp_path)
    workflow = root / ".github" / "workflows" / "ci.yml"
    workflow.write_text("jobs: {}\n", encoding="utf-8")

    result = delivery.run_source_hub_health(root)

    assert result.returncode == 1
    assert "CI does not execute source-hub suite(s)" in result.stderr
    assert "tests/alpha.test.sh" in result.stderr


def test_source_hub_health_stops_on_first_failed_suite(tmp_path):
    root = _hub(tmp_path)
    commands: list[list[str]] = []

    def runner(command, **_kwargs):
        commands.append(command)
        returncode = 7 if command[-1].endswith("alpha.test.sh") else 0
        return subprocess.CompletedProcess(command, returncode, "", "suite detail\n")

    result = delivery.run_source_hub_health(root, runner=runner)

    assert result.returncode == 7
    assert result.completed_checks == 1
    assert "source-hub check failed: tests/alpha.test.sh" in result.stderr
    assert all(not command[-1].endswith("beta.test.sh") for command in commands)


def test_source_hub_health_fails_if_successful_check_changes_git_state(tmp_path):
    root = _hub(tmp_path, suites=("alpha.test.sh",))
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)

    def runner(command, **_kwargs):
        if command[-1].endswith("alpha.test.sh"):
            (root / "leaked.tmp").write_text("leak\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    result = delivery.run_source_hub_health(root, runner=runner)

    assert result.returncode == 1
    assert "changed the repository working tree" in result.stderr
