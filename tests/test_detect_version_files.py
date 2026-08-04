"""Regression tests for GoalConfig._detect_version_files().

The detector used to recurse into venv/site-packages and target a dependency's
__init__.py (e.g. cryptography), bumping the dependency instead of the project.
"""

import os
from pathlib import Path

from goal.config.manager import GoalConfig


def _detect_in(tmp_path: Path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        cfg = GoalConfig.__new__(GoalConfig)  # skip __init__ / file IO
        return GoalConfig._detect_version_files(cfg)
    finally:
        os.chdir(cwd)


def test_skips_venv_and_site_packages(tmp_path):
    dep = tmp_path / "venv/lib/python3.13/site-packages/cryptography"
    dep.mkdir(parents=True)
    (dep / "__init__.py").write_text('__version__ = "44.0.0"\n')

    pkg = tmp_path / "src/myproj"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('__version__ = "1.2.3"\n')
    (tmp_path / "VERSION").write_text("1.2.3\n")

    files = _detect_in(tmp_path)

    assert not any("venv" in f or "site-packages" in f for f in files)
    assert "src/myproj/__init__.py:__version__" in files
    assert "VERSION" in files


def test_skips_build_and_node_modules(tmp_path):
    for vendored in ("build/lib/pkg", "node_modules/x/y", "dist/pkg"):
        d = tmp_path / vendored
        d.mkdir(parents=True)
        (d / "__init__.py").write_text('__version__ = "9.9.9"\n')

    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('__version__ = "0.1.0"\n')

    files = _detect_in(tmp_path)

    assert all(
        not any(bad in f for bad in ("build", "node_modules", "dist")) for f in files
    )
    assert "app/__init__.py:__version__" in files


def test_monorepo_detects_nested_manifest(tmp_path):
    # Root is a node package; the Python package lives in a subdir (urirun case).
    (tmp_path / "package.json").write_text('{"version": "0.3.10"}\n')
    (tmp_path / "VERSION").write_text("0.3.10\n")
    nested = tmp_path / "adapters/python"
    nested.mkdir(parents=True)
    (nested / "pyproject.toml").write_text('[project]\nversion = "0.3.10"\n')
    # a vendored copy that must be ignored
    vend = tmp_path / "node_modules/dep"
    vend.mkdir(parents=True)
    (vend / "pyproject.toml").write_text('[project]\nversion = "9.9.9"\n')

    files = _detect_in(tmp_path)

    assert "package.json:version" in files
    assert "adapters/python/pyproject.toml:version" in files
    assert not any("node_modules" in f for f in files)


def test_skips_example_and_fixture_manifests(tmp_path):
    # The project's own manifest must win over fixtures under examples/.
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n')
    for fixture in ("examples/node-app", "samples/crate", "fixtures/py"):
        d = tmp_path / fixture
        d.mkdir(parents=True)
        (d / "package.json").write_text('{"version": "9.9.9"}\n')
        (d / "Cargo.toml").write_text('version = "9.9.9"\n')

    files = _detect_in(tmp_path)

    assert "pyproject.toml:version" in files
    assert not any(
        any(bad in f for bad in ("examples", "samples", "fixtures")) for f in files
    )


def test_prefers_shallowest_package(tmp_path):
    deep = tmp_path / "a/b/c/deeppkg"
    deep.mkdir(parents=True)
    (deep / "__init__.py").write_text('__version__ = "2.0.0"\n')
    shallow = tmp_path / "rootpkg"
    shallow.mkdir()
    (shallow / "__init__.py").write_text('__version__ = "2.0.0"\n')

    files = _detect_in(tmp_path)
    init_entries = [f for f in files if ":__version__" in f]

    assert init_entries == ["rootpkg/__init__.py:__version__"]
