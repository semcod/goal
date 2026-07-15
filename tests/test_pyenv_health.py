"""Tests for goal.pyenv_health: detect + repair a venv whose pyvenv.cfg
disagrees with what its own bin/python actually resolves to (the cause of a
hard segfault on `import ctypes` and, downstream, any pip install)."""

from __future__ import annotations

import os
import sys
from unittest import mock

from goal import pyenv_health


def _make_fake_venv(tmp_path, declared_version: str, real_version: str):
    """A venv dir with bin/python3 (a real interpreter symlink target isn't
    needed since `_probe_version`/`_verify_ctypes_imports` are mocked in
    these tests) and a pyvenv.cfg declaring `declared_version`.
    """
    venv_dir = tmp_path / "venv"
    (venv_dir / "bin").mkdir(parents=True)
    python_bin = venv_dir / "bin" / "python3"
    python_bin.write_text("")
    (venv_dir / "pyvenv.cfg").write_text(
        f"home = /some/other/python/bin\nversion = {declared_version}\n"
        "include-system-site-packages = false\n"
    )
    return venv_dir


def test_diagnose_detects_version_mismatch(tmp_path, monkeypatch) -> None:
    venv_dir = _make_fake_venv(tmp_path, declared_version="9.99.99", real_version="3.13.7")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: "3.13.7")

    diagnosis = pyenv_health.diagnose(str(venv_dir))

    assert diagnosis is not None
    assert "niespójne środowisko venv" in diagnosis
    assert "9.99.99" in diagnosis
    assert "3.13.7" in diagnosis


def test_diagnose_returns_none_when_versions_match(tmp_path, monkeypatch) -> None:
    venv_dir = _make_fake_venv(tmp_path, declared_version="3.13.7", real_version="3.13.7")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: "3.13.7")

    assert pyenv_health.diagnose(str(venv_dir)) is None


def test_diagnose_returns_none_when_declared_version_is_abbreviated(
    tmp_path, monkeypatch
) -> None:
    """pyvenv.cfg sometimes only declares 'major.minor' -- that's not a
    mismatch as long as the actual patch version shares the same prefix."""
    venv_dir = _make_fake_venv(tmp_path, declared_version="3.13", real_version="3.13.9")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: "3.13.9")

    assert pyenv_health.diagnose(str(venv_dir)) is None


def test_diagnose_returns_none_for_nonexistent_prefix(tmp_path) -> None:
    assert pyenv_health.diagnose(str(tmp_path / "does-not-exist")) is None


def test_diagnose_returns_none_when_probe_fails(tmp_path, monkeypatch) -> None:
    venv_dir = _make_fake_venv(tmp_path, declared_version="9.99.99", real_version="3.13.7")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: None)

    assert pyenv_health.diagnose(str(venv_dir)) is None


def test_repair_rewrites_cfg_and_backs_up_original(tmp_path, monkeypatch) -> None:
    venv_dir = _make_fake_venv(tmp_path, declared_version="9.99.99", real_version="3.13.7")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: "3.13.7")
    monkeypatch.setattr(pyenv_health, "_verify_ctypes_imports", lambda prefix: True)

    ok = pyenv_health.repair(str(venv_dir))

    assert ok is True
    cfg_path = venv_dir / "pyvenv.cfg"
    backup_path = venv_dir / "pyvenv.cfg.bak"
    assert backup_path.exists()
    assert "version = 9.99.99" in backup_path.read_text()

    new_cfg = cfg_path.read_text()
    assert "version = 3.13.7" in new_cfg
    real_python = os.path.realpath(str(venv_dir / "bin" / "python3"))
    assert f"executable = {real_python}" in new_cfg
    assert f"home = {os.path.dirname(real_python)}" in new_cfg


def test_repair_does_not_clobber_existing_backup(tmp_path, monkeypatch) -> None:
    venv_dir = _make_fake_venv(tmp_path, declared_version="9.99.99", real_version="3.13.7")
    (venv_dir / "pyvenv.cfg.bak").write_text("version = ORIGINAL\n")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: "3.13.7")
    monkeypatch.setattr(pyenv_health, "_verify_ctypes_imports", lambda prefix: True)

    pyenv_health.repair(str(venv_dir))

    assert "ORIGINAL" in (venv_dir / "pyvenv.cfg.bak").read_text()


def test_repair_returns_false_when_post_repair_verification_fails(
    tmp_path, monkeypatch
) -> None:
    venv_dir = _make_fake_venv(tmp_path, declared_version="9.99.99", real_version="3.13.7")
    monkeypatch.setattr(pyenv_health, "_probe_version", lambda python_bin: "3.13.7")
    monkeypatch.setattr(pyenv_health, "_verify_ctypes_imports", lambda prefix: False)

    assert pyenv_health.repair(str(venv_dir)) is False


def test_repair_returns_false_for_nonexistent_prefix(tmp_path) -> None:
    assert pyenv_health.repair(str(tmp_path / "does-not-exist")) is False


def test_versions_match_helper() -> None:
    assert pyenv_health._versions_match("3.13", "3.13.7")
    assert pyenv_health._versions_match("3.13.7", "3.13.7")
    assert not pyenv_health._versions_match("3.13.12", "3.13.7")
    assert not pyenv_health._versions_match("3.12", "3.13.7")
