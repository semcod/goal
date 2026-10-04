"""Regression coverage for repository-root versus discovered module execution."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from goal.cli import tests as runner
from goal.cli.version_utils import detect_project_types


def marker(root, relative, content=""):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path.parent


def test_polyglot_modules_run_at_manifest_roots_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    marker(tmp_path, "pyproject.toml", '[project]\nname="root"')
    rust = marker(tmp_path, "packages/native/Cargo.toml")
    go = marker(tmp_path, "tools/probe/go.mod")
    gradle = marker(tmp_path, "plugins/ide/build.gradle.kts")
    python = MagicMock(return_value=True)
    monkeypatch.setattr(runner, "_run_root_test", python)
    monkeypatch.setattr(runner, "_ensure_root_pytest_or_mark_failed", lambda *a: True)
    monkeypatch.setattr(
        runner,
        "_build_python_test_command",
        lambda *a: (["python", "-m", "pytest"], True, "python"),
    )
    monkeypatch.setattr(runner, "_run_tests_in_subdirs", lambda *a: True)
    calls = []

    def run(command, **kwargs):
        calls.append((command, Path(kwargs.get("cwd", ".")).resolve()))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.run_tests(detect_project_types()) is True
    python.assert_called_once()
    assert calls == [
        ("cargo test", rust),
        ("go test ./...", go),
        ("gradle test", gradle),
    ]


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("pom.xml", "mvn test"),
        ("build.gradle", "gradle test"),
        ("build.gradle.kts", "gradle test"),
    ],
)
def test_jvm_build_tool_matches_manifest(tmp_path, monkeypatch, filename, expected):
    monkeypatch.chdir(tmp_path)
    project = marker(tmp_path, "modules/jvm/" + filename)
    calls = []
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda cmd, **kw: (
            calls.append((cmd, kw.get("cwd"))) or subprocess.CompletedProcess(cmd, 0)
        ),
    )
    assert runner.run_tests(detect_project_types()) is True
    assert calls == [(expected, project)]


@pytest.mark.parametrize(
    "tool,filename,expected",
    [
        ("gradlew", "build.gradle.kts", "./gradlew test"),
        ("mvnw", "pom.xml", "./mvnw test"),
    ],
)
def test_executable_build_wrapper_preferred(
    tmp_path, monkeypatch, tool, filename, expected
):
    monkeypatch.chdir(tmp_path)
    project = marker(tmp_path, "modules/jvm/" + filename)
    wrapper = project / tool
    wrapper.write_text("#!/bin/sh\nexit 0\n")
    wrapper.chmod(0o755)
    calls = []
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda cmd, **kw: (
            calls.append((cmd, kw.get("cwd"))) or subprocess.CompletedProcess(cmd, 0)
        ),
    )
    assert runner.run_tests(detect_project_types()) is True
    assert calls == [(expected, project)]


def test_nested_failure_aborts_but_remaining_modules_are_tested(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    first = marker(tmp_path, "a/Cargo.toml")
    second = marker(tmp_path, "b/Cargo.toml")
    seen = []

    def run(cmd, **kw):
        seen.append(kw.get("cwd"))
        return subprocess.CompletedProcess(cmd, 23 if kw.get("cwd") == first else 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.run_tests(["rust"]) is False
    assert seen == [first, second]
    assert str(first) in capsys.readouterr().out


def test_custom_strategy_remains_repository_owned(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    marker(tmp_path, "packages/native/Cargo.toml")
    custom = MagicMock(return_value=True)
    monkeypatch.setattr(runner, "_run_root_test", custom)
    assert (
        runner.run_tests(
            ["rust"], {"strategies": {"rust": {"test": "sh scripts/check-all.sh"}}}
        )
        is True
    )
    assert custom.call_args.args[1] == "sh scripts/check-all.sh"


def test_discovery_and_subproject_tests_exclude_foreign_trees(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for prefix in [
        ".worktrees/ticket-foreign",
        "vendor/package",
        "node_modules/dependency",
        "clone",
    ]:
        marker(tmp_path, prefix + "/Cargo.toml")
        marker(
            tmp_path,
            prefix + "/package.json",
            json.dumps({"scripts": {"test": "node test.js"}}),
        )
        marker(tmp_path, prefix + "/pyproject.toml")
        marker(tmp_path, prefix + "/tests/test_bad.py")
    marker(tmp_path, "clone/.git", "gitdir: elsewhere")
    outside = tmp_path.parent / (tmp_path.name + "-external")
    marker(outside, "Cargo.toml")
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    assert detect_project_types() == []
    assert runner._find_nodejs_test_dirs() == []
    assert runner._find_python_test_dirs() == []


def test_all_node_modules_run_even_after_failure_and_beyond_five(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for i in range(7):
        marker(
            tmp_path,
            f"packages/p{i}/package.json",
            json.dumps({"scripts": {"test": "node test.js"}}),
        )
    seen = []
    monkeypatch.setattr(
        runner, "_run_subdir_test", lambda p, c, d: seen.append(d) or len(seen) != 1
    )
    assert runner.run_tests(["nodejs"]) is False
    assert len(seen) == 7


def test_real_shell_observes_nested_cwd_and_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = marker(tmp_path, "modules/native/Cargo.toml")
    tools = tmp_path / "tools-bin"
    tools.mkdir()
    cargo = tools / "cargo"
    cargo.write_text("#!/bin/sh\npwd > observed-cwd\nexit 19\n")
    cargo.chmod(0o755)
    monkeypatch.setenv("PATH", str(tools) + ":/usr/bin:/bin")
    assert runner.run_tests(["rust"]) is False
    assert (project / "observed-cwd").read_text().strip() == str(project)
    assert not (tmp_path / "observed-cwd").exists()


def test_missing_required_tool_fails_at_known_manifest_root(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    project = marker(tmp_path, "native/Cargo.toml")
    monkeypatch.setenv("PATH", str(tmp_path / "empty-tools"))
    assert runner.run_tests(["rust"]) is False
    output = capsys.readouterr().out
    assert str(project) in output
    assert "exit 127" in output
    assert "launcher unavailable" in output


def test_default_root_only_module_is_still_tested(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    marker(tmp_path, "Cargo.toml")
    calls = []
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda cmd, **kw: (
            calls.append((cmd, kw.get("cwd"))) or subprocess.CompletedProcess(cmd, 0)
        ),
    )
    assert runner.run_tests(["rust"]) is True
    assert calls == [("cargo test", tmp_path)]


def test_deep_python_and_node_test_discovery_remains_supported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = "packages/group/nested/deep"
    marker(tmp_path, project + "/pyproject.toml")
    marker(tmp_path, project + "/tests/test_module.py")
    marker(
        tmp_path,
        project + "/package.json",
        json.dumps({"scripts": {"test": "node test.js"}}),
    )
    assert runner._find_python_test_dirs() == [project + "/tests"]
    assert runner._find_nodejs_test_dirs() == [project]


def test_configured_builtin_strategy_routes_to_modules(tmp_path, monkeypatch):
    """Generated goal.yaml defaults are module strategies, not root overrides."""
    monkeypatch.chdir(tmp_path)
    project = marker(tmp_path, "packages/native/Cargo.toml")
    calls = []
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda cmd, **kw: (
            calls.append((cmd, kw.get("cwd"))) or subprocess.CompletedProcess(cmd, 0)
        ),
    )
    assert (
        runner.run_tests(["rust"], {"strategies": {"rust": {"test": "cargo test"}}})
        is True
    )
    assert calls == [("cargo test", project)]
