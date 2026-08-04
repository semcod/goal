"""Detect and repair a venv whose pyvenv.cfg disagrees with its own interpreter.

pip (2025.x+) eagerly imports ``ctypes`` during ``install`` (via a vendored
rich fallback module). If a venv's ``pyvenv.cfg`` declares a different
``home``/``version`` than what its own ``bin/python`` symlink actually
resolves to, the stdlib's compiled ``_ctypes`` extension gets loaded from the
*declared* base prefix into a process built from a *different* CPython
build -- a hard ABI mismatch that reliably segfaults on the very first
``import ctypes``, taking down ``pip install`` (or anything else that
imports ctypes) with it.

This shows up as ``pip`` (or any subprocess in that venv) dying with
SIGSEGV for no apparent reason -- not a bug in whatever package is being
installed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Dict, Optional


def _read_pyvenv_cfg(cfg_path: str) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    with open(cfg_path, encoding="utf-8") as fh:
        for line in fh:
            if "=" in line:
                key, _, value = line.partition("=")
                cfg[key.strip()] = value.strip()
    return cfg


def _write_pyvenv_cfg(cfg_path: str, cfg: Dict[str, str]) -> None:
    lines = [f"{key} = {value}" for key, value in cfg.items()]
    with open(cfg_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _resolve_real_python(prefix: str) -> Optional[str]:
    """Absolute, symlink-resolved path of the venv's actual interpreter binary."""
    for name in ("python3", "python"):
        candidate = os.path.join(prefix, "bin", name)
        if os.path.exists(candidate):
            return os.path.realpath(candidate)
    return None


def _probe_version(python_bin: str) -> Optional[str]:
    """Ask a Python binary for its own version. Does not touch ctypes."""
    try:
        result = subprocess.run(
            [python_bin, "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _versions_match(declared: str, actual: str) -> bool:
    declared_parts = declared.split(".")
    actual_parts = actual.split(".")[: len(declared_parts)]
    return declared_parts == actual_parts


def diagnose(prefix: Optional[str] = None) -> Optional[str]:
    """Return a human explanation when `prefix` (default: sys.prefix) is a
    venv whose pyvenv.cfg mismatches its own interpreter. None when healthy,
    not a venv, or the check itself can't run (missing files, no venv here).
    """
    prefix = prefix or sys.prefix
    cfg_path = os.path.join(prefix, "pyvenv.cfg")
    if not os.path.exists(cfg_path):
        return None

    try:
        cfg = _read_pyvenv_cfg(cfg_path)
    except OSError:
        return None

    real_target = _resolve_real_python(prefix)
    if not real_target:
        return None

    actual_version = _probe_version(real_target)
    declared_version = cfg.get("version", "")
    if not declared_version or not actual_version:
        return None

    if _versions_match(declared_version, actual_version):
        return None

    return (
        f"Wykryto niespójne środowisko venv: {cfg_path} deklaruje Python "
        f"{declared_version} (home={cfg.get('home', '?')}), ale {prefix}/bin/python3 "
        f"faktycznie wskazuje na {real_target} (Python {actual_version}). "
        "Skompilowane moduły stdlib (np. ctypes) ładują się wtedy z niepasującej "
        "wersji i segfaultują przy pierwszym imporcie."
    )


def _verify_ctypes_imports(prefix: str) -> bool:
    python_bin = os.path.join(prefix, "bin", "python3")
    try:
        result = subprocess.run(
            [python_bin, "-c", "import ctypes"],
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def repair(prefix: Optional[str] = None) -> bool:
    """Rewrite pyvenv.cfg's home/version/executable to match what the venv's
    own bin/python actually resolves to.

    Minimally invasive: only rewrites the 3 metadata fields (backing up the
    original file to ``pyvenv.cfg.bak`` first) so stdlib resolution is fixed
    without touching, reinstalling, or losing any installed site-packages.
    Returns True only once a post-repair ``import ctypes`` actually succeeds.
    """
    prefix = prefix or sys.prefix
    cfg_path = os.path.join(prefix, "pyvenv.cfg")
    if not os.path.exists(cfg_path):
        return False

    real_target = _resolve_real_python(prefix)
    if not real_target:
        return False

    actual_version = _probe_version(real_target)
    if not actual_version:
        return False

    try:
        cfg = _read_pyvenv_cfg(cfg_path)
    except OSError:
        return False

    backup_path = cfg_path + ".bak"
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(cfg_path, backup_path)
        except OSError:
            return False

    cfg["home"] = os.path.dirname(real_target)
    cfg["version"] = actual_version
    cfg["executable"] = real_target

    try:
        _write_pyvenv_cfg(cfg_path, cfg)
    except OSError:
        return False

    return _verify_ctypes_imports(prefix)
