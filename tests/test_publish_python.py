"""Publication must run inside the selected environment, not its base Python."""

import json
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from goal.cli.publish import _get_python_bin


@pytest.mark.parametrize("selection", ["active", ".venv", "venv", "env"])
def test_selected_python_keeps_virtualenv_isolation(tmp_path, monkeypatch, selection):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    environment = tmp_path / ("external environment" if selection == "active" else selection)
    venv.EnvBuilder(with_pip=False, symlinks=True).create(environment)
    python = environment / "bin" / "python"
    assert python.is_symlink()
    if selection == "active":
        monkeypatch.setenv("VIRTUAL_ENV", str(environment))
        # An active environment takes precedence over an existing project venv.
        venv.EnvBuilder(with_pip=False, symlinks=True).create(tmp_path / ".venv")
    else:
        monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "missing-environment"))
        if selection == ".venv":
            # Project .venv wins even when the lower-priority names exist.
            for name in ("venv", "env"):
                venv.EnvBuilder(with_pip=False, symlinks=True).create(tmp_path / name)
    site_packages = subprocess.check_output(
        [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        text=True,
    ).strip()
    Path(site_packages, "publish_environment_probe.py").write_text("VALUE = 'isolated'\n")
    result = subprocess.check_output(
        [
            _get_python_bin(),
            "-I",
            "-c",
            (
                "import json, sys, publish_environment_probe as probe; "
                "print(json.dumps([sys.prefix, sys.base_prefix, probe.VALUE]))"
            ),
        ],
        text=True,
    )
    prefix, base_prefix, value = json.loads(result)
    assert Path(prefix) == environment
    assert prefix != base_prefix
    assert value == "isolated"


def test_no_virtualenv_uses_running_interpreter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    assert _get_python_bin() == sys.executable


@pytest.mark.parametrize("uv", [None, "/trusted/uv"])
def test_missing_publication_tools_use_exact_environment_and_recheck(tmp_path, monkeypatch, uv):
    from goal.cli import publish

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(publish.shutil, "which", lambda name: uv)
    target = str(tmp_path / "environment with spaces/bin/python")
    installed, calls = set(), []
    lock = tmp_path / "uv.lock"
    lock.write_text("unchanged lock")
    def run(command, **kwargs):
        calls.append((command, kwargs))
        if command[:2] == [target, "-m"] and command[-1] == "--help":
            return subprocess.CompletedProcess(command, 0 if command[2] in installed else 1)
        installed.add(command[-1])
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(publish.subprocess, "run", run)
    assert publish._ensure_publish_deps(target)
    assert installed == {"build", "twine"}
    installs = [command for command, _ in calls if command[-1] != "--help"]
    for command, module in zip(installs, ("build", "twine")):
        assert command == ([uv, "pip", "install", "--python", target, "--quiet", module]
                           if uv else [target, "-m", "pip", "install", "--quiet", module])
    assert len(calls) == 6 and all(options["timeout"] in {30, 120} for _, options in calls)
    assert lock.read_text() == "unchanged lock"


@pytest.mark.parametrize("fault", ["failure", "timeout", "missing", "unverified"])
def test_failed_tool_preparation_stops_without_upload_or_fallback(monkeypatch, capsys, fault):
    from goal.cli import publish

    monkeypatch.setattr(publish.shutil, "which", lambda name: "/trusted/uv")
    installs = []
    def run(command, **kwargs):
        if command[-1] == "--help":
            return subprocess.CompletedProcess(command, 1)
        installs.append(command)
        if fault == "timeout":
            raise subprocess.TimeoutExpired(command, 120, stderr="sensitive-index-fixture")
        if fault == "missing":
            raise OSError("sensitive-index-fixture")
        return subprocess.CompletedProcess(command, 0 if fault == "unverified" else 1,
                                           stderr="sensitive-index-fixture")
    monkeypatch.setattr(publish.subprocess, "run", run)
    assert not publish._ensure_publish_deps("/exact/python")
    assert len(installs) == 1 and installs[0][-1] == "build"
    assert not any(command[:3] == ["/exact/python", "-m", "pip"] for command in installs)
    assert "sensitive-index-fixture" not in capsys.readouterr().out


def test_existing_tools_do_not_install_or_resolve_locks(monkeypatch):
    from goal.cli import publish

    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(publish.subprocess, "run", run)
    monkeypatch.setattr(publish.shutil, "which", lambda name: pytest.fail("must not choose an installer"))
    assert publish._ensure_publish_deps("/selected/python")
    assert calls == [["/selected/python", "-m", module, "--help"] for module in ("build", "twine")]
