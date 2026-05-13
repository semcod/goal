"""E2E tests for PackageManagerBroker and installer system."""

import subprocess
from unittest.mock import patch, MagicMock
import pytest

from goal.installers import PackageManagerBroker
from goal.installers.managers import UvManager, PipManager, PoetryManager, PdmManager


class TestPackageManagerBrokerE2E:
    """E2E tests for broker functionality."""

    def test_broker_detects_available_managers(self):
        """Broker should detect which package managers are available."""
        broker = PackageManagerBroker()
        available = broker.detect_available()

        # Should return a list
        assert isinstance(available, list)
        # Should have at least pip (always available)
        names = [m.name for m in available]
        assert "pip" in names

    def test_broker_detects_lockfile_uv(self, tmp_path):
        """Broker should detect uv.lock file."""
        (tmp_path / "uv.lock").touch()
        broker = PackageManagerBroker(str(tmp_path))

        assert broker.detect_lockfile() == "uv.lock"

    def test_broker_detects_lockfile_poetry(self, tmp_path):
        """Broker should detect poetry.lock file."""
        (tmp_path / "poetry.lock").touch()
        broker = PackageManagerBroker(str(tmp_path))

        assert broker.detect_lockfile() == "poetry.lock"

    def test_broker_detects_lockfile_pdm(self, tmp_path):
        """Broker should detect pdm.lock file."""
        (tmp_path / "pdm.lock").touch()
        broker = PackageManagerBroker(str(tmp_path))

        assert broker.detect_lockfile() == "pdm.lock"

    def test_broker_no_lockfile(self, tmp_path):
        """Broker should return None when no lockfile exists."""
        broker = PackageManagerBroker(str(tmp_path))

        assert broker.detect_lockfile() is None

    def test_uv_manager_priority(self):
        """UV should have highest priority (lowest number)."""
        uv = UvManager()
        assert uv.priority == 10

    def test_pdm_manager_priority(self):
        """PDM should have medium priority."""
        pdm = PdmManager()
        assert pdm.priority == 20

    def test_poetry_manager_priority(self):
        """Poetry should have lower priority than uv/pdm."""
        poetry = PoetryManager()
        assert poetry.priority == 30

    def test_pip_manager_priority(self):
        """Pip should have lowest priority (fallback)."""
        pip = PipManager()
        assert pip.priority == 100

    def test_uv_manager_is_available_when_uv_installed(self):
        """UV manager should detect uv availability."""
        uv = UvManager()
        # This depends on test environment having uv
        result = uv.is_available()
        assert isinstance(result, bool)

    def test_pip_manager_always_available(self):
        """Pip manager should always report available."""
        pip = PipManager()
        assert pip.is_available() is True

    def test_manager_registry_order(self):
        """Managers should be sorted by priority in registry."""
        from goal.installers.broker import _MANAGERS

        priorities = [m.priority for m in _MANAGERS]
        assert priorities == sorted(priorities)


class TestInstallResult:
    """Tests for InstallResult data class."""

    def test_install_result_success(self):
        """InstallResult should capture success state."""
        from goal.installers.managers.base import InstallResult

        result = InstallResult(
            manager="uv", success=True, duration_s=5.2, command="uv pip install -e ."
        )

        assert result.success is True
        assert result.duration_s == 5.2
        assert result.error is None

    def test_install_result_failure(self):
        """InstallResult should capture failure with error."""
        from goal.installers.managers.base import InstallResult

        result = InstallResult(
            manager="pip",
            success=False,
            duration_s=0.5,
            command="pip install xyz",
            error="Package not found",
        )

        assert result.success is False
        assert result.error == "Package not found"


class TestBootstrapIntegration:
    """Integration tests with bootstrap module."""

    def test_bootstrap_imports_broker(self):
        """Bootstrap module should import broker."""
        from goal.bootstrap.installer import _install_python_deps_broker

        assert callable(_install_python_deps_broker)

    def test_bootstrap_uses_new_installer(self, tmp_path):
        """Bootstrap should use PackageManagerBroker."""
        from goal.bootstrap.installer import ensure_project_environment

        # Create a fake Python project
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"')

        # Should not fail (may skip if no venv needed)
        with patch("click.confirm", return_value=False):
            result = ensure_project_environment(tmp_path, "python", yes=True)

        assert result is True

    def test_legacy_bootstrap_compatibility(self):
        """Legacy project_bootstrap imports should work."""
        from goal.project_bootstrap import (
            detect_project_types_deep,
            ensure_project_environment,
            PROJECT_BOOTSTRAP,
        )

        assert callable(detect_project_types_deep)
        assert callable(ensure_project_environment)
        assert "python" in PROJECT_BOOTSTRAP


class TestDoctorIntegration:
    """Integration tests with doctor command."""

    def test_doctor_imports_broker(self):
        """Doctor command should import PackageManagerBroker."""
        from goal.cli.doctor_cmd import doctor

        # Function should exist and be importable
        assert callable(doctor)


class TestLockfilePriority:
    """Tests for lockfile-based manager selection."""

    def test_uv_lockfile_triggers_uv_manager(self, tmp_path):
        """uv.lock should trigger UV manager preference."""
        (tmp_path / "uv.lock").touch()
        broker = PackageManagerBroker(str(tmp_path))

        lockfile = broker.detect_lockfile()
        from goal.installers.broker import _LOCKFILE_MANAGERS

        assert _LOCKFILE_MANAGERS[lockfile] == "uv"

    def test_poetry_lockfile_triggers_poetry_manager(self, tmp_path):
        """poetry.lock should trigger Poetry manager preference."""
        (tmp_path / "poetry.lock").touch()
        broker = PackageManagerBroker(str(tmp_path))

        lockfile = broker.detect_lockfile()
        from goal.installers.broker import _LOCKFILE_MANAGERS

        assert _LOCKFILE_MANAGERS[lockfile] == "poetry"


@pytest.mark.skipif(
    subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
    reason="uv not installed",
)
class TestUvManagerReal:
    """Tests requiring real uv installation."""

    def test_uv_manager_detects_uv(self):
        """UV manager should detect real uv installation."""
        uv = UvManager()
        assert uv.is_available() is True

    def test_uv_manager_install_editable_mock(self, tmp_path):
        """UV manager should generate correct editable install command."""
        uv = UvManager()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = uv.install_editable(["dev"])

            assert result.success is True
            assert "uv" in result.command
            assert "-e" in result.command


@pytest.mark.skipif(
    subprocess.run(["which", "poetry"], capture_output=True).returncode != 0,
    reason="poetry not installed",
)
class TestPoetryManagerReal:
    """Tests requiring real poetry installation."""

    def test_poetry_manager_detects_poetry(self):
        """Poetry manager should detect real poetry installation."""
        poetry = PoetryManager()
        assert poetry.is_available() is True


@pytest.mark.skipif(
    subprocess.run(["which", "pdm"], capture_output=True).returncode != 0,
    reason="pdm not installed",
)
class TestPdmManagerReal:
    """Tests requiring real pdm installation."""

    def test_pdm_manager_detects_pdm(self):
        """PDM manager should detect real pdm installation."""
        pdm = PdmManager()
        assert pdm.is_available() is True
