import os
import subprocess
import pytest
from goal.cli import sync_all_versions
from goal.cli.version import PROJECT_TYPES
from goal.cli.version_utils import bump_version


def test_sync_updates_init_py(tmp_path):
    """Test that sync_all_versions updates __version__ in __init__.py files."""
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Create a dummy project structure
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()

        # valid __init__.py
        init_file = pkg_dir / "__init__.py"
        init_file.write_text('__version__ = "0.1.0"\n')

        # nested __init__.py
        sub_dir = pkg_dir / "sub"
        sub_dir.mkdir()
        sub_init = sub_dir / "__init__.py"
        sub_init.write_text('__version__ = "0.1.0"\n')

        # Create a venv dir (should be ignored)
        venv_dir = tmp_path / ".venv" / "lib" / "site-packages" / "other"
        venv_dir.mkdir(parents=True)
        venv_init = venv_dir / "__init__.py"
        venv_init.write_text('__version__ = "0.1.0"\n')

        # Create a test venv dir (should also be ignored)
        test_venv_dir = tmp_path / ".venv_test" / "lib" / "site-packages" / "another"
        test_venv_dir.mkdir(parents=True)
        test_venv_init = test_venv_dir / "__init__.py"
        test_venv_init.write_text('__version__ = "0.1.0"\n')

        # Create VERSION file required by sync_all_versions
        (tmp_path / "VERSION").write_text("0.1.0\n")

        # Run sync
        # Bypass nfo decorator if present to avoid rich I/O errors during tests
        func = sync_all_versions
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        updated = func("0.2.0")

        # Check results
        assert "mypkg/__init__.py" in updated or str(init_file) in updated
        assert "mypkg/sub/__init__.py" in updated or str(sub_init) in updated

        # Verify content
        assert '__version__ = "0.2.0"' in init_file.read_text()
        assert '__version__ = "0.2.0"' in sub_init.read_text()

        # Verify venv ignored
        assert '__version__ = "0.1.0"' in venv_init.read_text()
        assert '__version__ = "0.1.0"' in test_venv_init.read_text()

    finally:
        os.chdir(old_cwd)


def test_python_publish_command_skips_existing():
    cmd = PROJECT_TYPES["python"]["publish_command"]
    assert "python -m twine upload" in cmd
    assert "--skip-existing" in cmd


def test_sync_updates_setup_py_version(tmp_path, monkeypatch):
    """sync_all_versions must update setup.py because legacy builds read it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "VERSION").write_text("4.0.0\n")
    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\n'
        'setup(name="tellm", version="4.0.0", packages=["tellm"])\n'
    )

    func = sync_all_versions
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    updated = func("4.0.1")

    assert "setup.py" in updated
    assert 'version="4.0.1"' in (tmp_path / "setup.py").read_text()


def test_sync_updates_uv_lock_after_pyproject_version_change(tmp_path, monkeypatch):
    """sync_all_versions refreshes uv.lock and stages it for version commits."""
    old_cwd = os.getcwd()
    calls = []

    def fake_run(cmd, capture_output, text):
        calls.append((cmd, capture_output, text))
        (tmp_path / "uv.lock").write_text("version = '0.2.0'\n")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    try:
        os.chdir(tmp_path)
        (tmp_path / "VERSION").write_text("0.1.0\n")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "0.1.0"\n'
        )
        (tmp_path / "uv.lock").write_text("version = '0.1.0'\n")
        monkeypatch.setattr("goal.cli.version_sync.subprocess.run", fake_run)

        func = sync_all_versions
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        updated = func("0.2.0")

        assert calls == [(["uv", "lock"], True, True)]
        assert "pyproject.toml" in updated
        assert "uv.lock" in updated
        assert 'version = "0.2.0"' in (tmp_path / "pyproject.toml").read_text()
    finally:
        os.chdir(old_cwd)


@pytest.mark.parametrize(
    ("manifest", "manifest_text", "lockfile", "command"),
    [
        (
            "pyproject.toml",
            '[project]\nname = "demo"\nversion = "0.1.0"\n',
            "poetry.lock",
            ["poetry", "lock"],
        ),
        (
            "pyproject.toml",
            '[project]\nname = "demo"\nversion = "0.1.0"\n',
            "pdm.lock",
            ["pdm", "lock"],
        ),
        (
            "package.json",
            '{"name":"demo","version":"0.1.0"}\n',
            "package-lock.json",
            ["npm", "install", "--package-lock-only"],
        ),
        (
            "package.json",
            '{"name":"demo","version":"0.1.0"}\n',
            "pnpm-lock.yaml",
            ["pnpm", "install", "--lockfile-only"],
        ),
        (
            "Cargo.toml",
            '[package]\nname = "demo"\nversion = "0.1.0"\n',
            "Cargo.lock",
            ["cargo", "generate-lockfile"],
        ),
    ],
)
def test_sync_refreshes_detected_dependency_lockfiles(
    tmp_path,
    monkeypatch,
    manifest,
    manifest_text,
    lockfile,
    command,
):
    """sync_all_versions refreshes lockfiles for every supported dependency manager."""
    old_cwd = os.getcwd()
    calls = []

    def fake_run(cmd, capture_output, text):
        calls.append((cmd, capture_output, text))
        (tmp_path / lockfile).write_text(f"{lockfile}: refreshed\n")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    try:
        os.chdir(tmp_path)
        (tmp_path / "VERSION").write_text("0.1.0\n")
        (tmp_path / manifest).write_text(manifest_text)
        (tmp_path / lockfile).write_text(f"{lockfile}: stale\n")
        monkeypatch.setattr("goal.cli.version_sync.subprocess.run", fake_run)

        func = sync_all_versions
        while hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        updated = func("0.2.0")

        assert calls == [(command, True, True)]
        assert manifest in updated
        assert lockfile in updated
    finally:
        os.chdir(old_cwd)


@pytest.mark.parametrize(
    "version,bump_type,expected",
    [
        # clean semver — unchanged behaviour
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
        ("1.0", "patch", "1.0.1"),
        # hyphen pre-release  (was crashing before fix)
        ("0.2.0-rc1", "patch", "0.2.1"),
        ("0.2.0-rc1", "minor", "0.3.0"),
        ("0.2.0-rc1", "major", "1.0.0"),
        ("1.2.3-alpha", "patch", "1.2.4"),
        ("1.2.3-beta.2", "patch", "1.2.4"),
        # PEP 440 inline pre-release
        ("1.0.0rc1", "patch", "1.0.1"),
        ("1.2.3a1", "minor", "1.3.0"),
        ("1.2.3b2", "patch", "1.2.4"),
        # PEP 440 dev / post
        ("1.2.3.dev5", "patch", "1.2.4"),
        ("1.2.3.post1", "patch", "1.2.4"),
        # CalVer with suffix
        ("2024.1.0-rc1", "patch", "2024.1.1"),
    ],
)
def test_bump_version_pre_release_formats(version, bump_type, expected):
    """bump_version must not crash on pre-release suffixes and must strip them."""
    assert bump_version(version, bump_type) == expected
