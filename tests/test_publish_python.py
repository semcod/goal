"""Publication must run inside the selected environment, not its base Python."""

import json
import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from goal.cli.publish import _get_python_bin


@pytest.mark.skipif(os.name == "nt", reason="POSIX virtualenv executable layout")
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
