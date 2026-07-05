"""Tests for goal.bootstrap.installer._ensure_python_test_dependency.

This is a near-duplicate of goal.project_bootstrap._ensure_python_test_dependency
(see tests/test_project_bootstrap.py::TestPythonTestDependency for the full
scenario coverage and the 2026-07-06 regression writeup) -- both copies got
the same addopts-blindness bug and the same fix, so both get dedicated
coverage rather than assuming one implies the other.
"""

from __future__ import annotations

from unittest import mock

from goal.bootstrap.installer import _ensure_python_test_dependency


class TestPythonTestDependency:
    def test_already_installed_pytest_with_working_addopts_is_fast_path(self, tmp_path):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0, stdout="9.0.0", stderr=""),  # import pytest OK
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # addopts check OK
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/python3", "pytest")
                is True
            )
        assert mock_run.call_count == 2

    def test_pytest_importable_but_addopts_broken_triggers_dev_extras_reinstall(
        self, tmp_path
    ):
        """2026-07-06 regression: `import pytest` succeeding is not enough --
        pyproject.toml's own `addopts` (e.g. `-n auto`) can need a plugin
        that lives under [project.optional-dependencies] dev, which a bare
        `pip install pytest` never installs. Must escalate to a full
        editable+dev reinstall, then re-verify before reporting ready."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0, stdout="9.0.0", stderr=""),  # import pytest OK
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),  # addopts check: broken
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # pip install pytest (no-op fix)
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),  # addopts check: still broken
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # dev-extras reinstall
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # addopts check: fixed
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/python3", "pytest")
                is True
            )

        assert mock_run.call_args_list[4].args[0] == [
            "/usr/bin/python3",
            "-m",
            "pip",
            "install",
            "-e",
            ".[dev]",
        ]
        assert mock_run.call_count == 6

    def test_addopts_still_broken_after_dev_extras_reinstall_reports_failure(
        self, tmp_path
    ):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0, stdout="9.0.0", stderr=""),
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),
                mock.MagicMock(returncode=0, stdout="", stderr=""),
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),
                mock.MagicMock(returncode=0, stdout="", stderr=""),
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/python3", "pytest")
                is False
            )

    def test_non_pytest_test_dep_skips_addopts_check(self, tmp_path):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0, stdout="1.0.0", stderr=""),
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/node", "jest")
                is True
            )
        assert mock_run.call_count == 1
