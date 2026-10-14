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


def test_source_hub_health_emits_proportional_progress(tmp_path):
    root = _hub(tmp_path)
    progress_messages: list[str] = []

    def runner(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, "", "")

    result = delivery.run_source_hub_health(
        root,
        runner=runner,
        on_progress=progress_messages.append,
    )

    assert result.returncode == 0
    assert any("validating 2 canonical JSON documents" in m for m in progress_messages)
    assert any("[1/3]" in m and "check_required_checks.py" in m for m in progress_messages)
    assert any("[2/3]" in m and "alpha.test.sh" in m for m in progress_messages)
    assert any("[3/3]" in m and "beta.test.sh" in m for m in progress_messages)
    assert any("passed" in m for m in progress_messages)


def test_source_hub_health_handles_timeout_gracefully(tmp_path):
    root = _hub(tmp_path)

    def runner(command, **_kwargs):
        if command[-1].endswith("alpha.test.sh"):
            raise subprocess.TimeoutExpired(
                cmd=command,
                timeout=10.0,
                output="partial stdout\n",
                stderr="partial stderr\n",
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    result = delivery.run_source_hub_health(root, runner=runner, timeout=10.0)

    assert result.returncode == 124
    assert result.completed_checks == 1
    assert "partial stdout" in result.stdout
    assert "GOV-HUB-001: source-hub check timed out after 10.0s: tests/alpha.test.sh" in result.stderr


def test_source_hub_health_deterministic_cache_reuse_and_invalidation(tmp_path, monkeypatch):
    root = _hub(tmp_path, suites=("alpha.test.sh",))
    # Setup git repo with ignored .subactor/cache
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / ".subactor").mkdir(parents=True)
    (root / ".subactor" / ".gitignore").write_text("/cache/\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "init"], cwd=root, check=True)

    calls: list[list[str]] = []

    def runner(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "pass\n", "")

    # 1. First run: cache miss, runner executes
    result1 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result1.returncode == 0
    assert result1.cached is False
    assert len(calls) == 2  # check_required_checks + alpha.test.sh
    cache_file = root / ".subactor" / "cache" / "source-hub-health.json"
    assert cache_file.is_file()

    # 2. Second run: cache hit, runner not called
    result2 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result2.returncode == 0
    assert result2.cached is True
    assert len(calls) == 2  # No new calls

    # 3. Invalidation by JSON modification
    (root / "governance" / "manifest.default.json").write_text(
        json.dumps({"schema": "test-modified"}), encoding="utf-8"
    )
    result3 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result3.returncode == 0
    assert result3.cached is False
    assert len(calls) == 4  # Ran again

    # 4. Invalidation by suite script modification
    (root / "tests" / "alpha.test.sh").write_text(
        "#!/usr/bin/env bash\necho modified\nexit 0\n", encoding="utf-8"
    )
    result4 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result4.returncode == 0
    assert result4.cached is False
    assert len(calls) == 6

    # 5. Invalidation by dirty git status (e.g. untracked or modified file)
    (root / "newfile.txt").write_text("hello\n", encoding="utf-8")
    result5 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result5.returncode == 0
    assert result5.cached is False
    assert len(calls) == 8

    # Clean up dirty file and commit changes so it's clean again
    (root / "newfile.txt").unlink()
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "update"], cwd=root, check=True)

    # Now verify cache hit again
    result6 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result6.cached is False
    assert len(calls) == 10
    result7 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result7.cached is True
    assert len(calls) == 10

    # 6. Bypass via environment variable GOAL_NO_PREFLIGHT_CACHE=1
    monkeypatch.setenv("GOAL_NO_PREFLIGHT_CACHE", "1")
    result8 = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result8.cached is False
    assert len(calls) == 12


def test_source_hub_health_never_caches_failures(tmp_path):
    root = _hub(tmp_path, suites=("alpha.test.sh",))
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / ".subactor").mkdir(parents=True)
    (root / ".subactor" / ".gitignore").write_text("/cache/\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)

    def runner(command, **_kwargs):
        returncode = 1 if command[-1].endswith("alpha.test.sh") else 0
        return subprocess.CompletedProcess(command, returncode, "", "failed\n")

    result = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result.returncode == 1
    cache_file = root / ".subactor" / "cache" / "source-hub-health.json"
    assert not cache_file.exists()


def test_source_hub_health_preserves_untracked_hygiene_when_cache_not_ignored(tmp_path):
    root = _hub(tmp_path, suites=("alpha.test.sh",))
    # Repository where .subactor is NOT gitignored
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "init"], cwd=root, check=True)

    def runner(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, "", "")

    result = delivery.run_source_hub_health(root, runner=runner, use_cache=True)
    assert result.returncode == 0
    # Must NOT have created untracked cache file
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert status.stdout.strip() == ""


def test_validate_delivery_ready_deduplication(tmp_path, monkeypatch):
    root = _hub(tmp_path)
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "init"], cwd=root, check=True)

    delivery.clear_delivery_gate_cache()
    gate_calls = []
    monkeypatch.setattr(
        delivery,
        "_governance_gate",
        lambda candidate, **_kwargs: gate_calls.append(candidate),
    )

    policy = delivery.DeliveryPolicy(
        mode="direct-main",
        require_goal_a=False,
        allowed_modes=("direct-main",),
        remote="origin",
        base_branch="main" if subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True).stdout.strip() == "main" else subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True).stdout.strip(),
        require_clean_governance=True,
    )

    # 1. First call: gate is executed
    delivery.validate_delivery_ready(policy, cwd=root)
    assert len(gate_calls) == 1

    # 2. Second call without repo change: gate is NOT executed again
    delivery.validate_delivery_ready(policy, cwd=root)
    assert len(gate_calls) == 1

    # 3. Modify working tree: gate IS executed again
    (root / "untracked.txt").write_text("test\n", encoding="utf-8")
    delivery.validate_delivery_ready(policy, cwd=root)
    assert len(gate_calls) == 2

