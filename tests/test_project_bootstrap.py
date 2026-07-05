"""Tests for project environment bootstrapping and test scaffolding."""

import os
import sys
import types
from unittest import mock

import pytest
from click.testing import CliRunner

from goal.project_bootstrap import (
    PROJECT_BOOTSTRAP,
    detect_project_types_deep,
    guess_package_name,
    find_existing_tests,
    scaffold_test,
    ensure_project_environment,
    bootstrap_project,
    bootstrap_all_projects,
    _match_marker,
    _find_openrouter_api_key,
    _find_git_root,
    _ensure_costs_installed,
    _ensure_python_test_dependency,
    _ensure_pfix_installed,
    _validate_pfix_env,
    _ensure_pfix_env,
)
from goal.bootstrap.costs_badge import _install_costs_package
from goal.cli import main


# ---------------------------------------------------------------------------
# _match_marker
# ---------------------------------------------------------------------------


class TestMatchMarker:
    def test_exact_file(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        assert _match_marker(tmp_path, "pyproject.toml") is True
        assert _match_marker(tmp_path, "setup.py") is False

    def test_glob_pattern(self, tmp_path):
        (tmp_path / "myapp.csproj").write_text("<Project/>")
        assert _match_marker(tmp_path, "*.csproj") is True
        assert _match_marker(tmp_path, "*.fsproj") is False


# ---------------------------------------------------------------------------
# detect_project_types_deep
# ---------------------------------------------------------------------------


class TestDetectProjectTypesDeep:
    def test_root_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        result = detect_project_types_deep(tmp_path)
        assert "python" in result
        assert tmp_path.resolve() in result["python"]

    def test_subfolder_nodejs(self, tmp_path):
        sub = tmp_path / "frontend"
        sub.mkdir()
        (sub / "package.json").write_text('{"name": "app"}')
        result = detect_project_types_deep(tmp_path)
        assert "nodejs" in result
        assert sub.resolve() in result["nodejs"]

    def test_ignores_hidden_dirs(self, tmp_path):
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "pyproject.toml").write_text("[project]")
        result = detect_project_types_deep(tmp_path)
        assert "python" not in result

    def test_multiple_types(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        sub = tmp_path / "api"
        sub.mkdir()
        (sub / "go.mod").write_text("module example.com/api")
        result = detect_project_types_deep(tmp_path)
        assert "python" in result
        assert "go" in result

    def test_empty_dir(self, tmp_path):
        result = detect_project_types_deep(tmp_path)
        assert result == {}

    def test_rust_in_subfolder(self, tmp_path):
        sub = tmp_path / "engine"
        sub.mkdir()
        (sub / "Cargo.toml").write_text('[package]\nname = "engine"')
        result = detect_project_types_deep(tmp_path)
        assert "rust" in result

    def test_java_gradle(self, tmp_path):
        (tmp_path / "build.gradle").write_text("apply plugin: 'java'")
        result = detect_project_types_deep(tmp_path)
        assert "java" in result

    def test_dotnet_csproj(self, tmp_path):
        (tmp_path / "App.csproj").write_text("<Project/>")
        result = detect_project_types_deep(tmp_path)
        assert "dotnet" in result


# ---------------------------------------------------------------------------
# guess_package_name
# ---------------------------------------------------------------------------


class TestGuessPackageName:
    def test_python_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('name = "my-cool-lib"')
        assert guess_package_name(tmp_path, "python") == "my_cool_lib"

    def test_nodejs_from_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "@org/my-app"}')
        assert guess_package_name(tmp_path, "nodejs") == "my-app"

    def test_rust_from_cargo(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "my_crate"')
        assert guess_package_name(tmp_path, "rust") == "my_crate"

    def test_go_from_gomod(self, tmp_path):
        (tmp_path / "go.mod").write_text("module github.com/user/mymod")
        assert guess_package_name(tmp_path, "go") == "mymod"

    def test_fallback_to_dirname(self, tmp_path):
        assert guess_package_name(tmp_path, "php") == tmp_path.name.replace("-", "_")

    def test_test_harness_uses_directory_name(self, tmp_path):
        tests_proj = tmp_path / "tests"
        tests_proj.mkdir()
        (tests_proj / "pyproject.toml").write_text('name = "myapp-tests"')
        assert guess_package_name(tests_proj, "python") == "tests"


# ---------------------------------------------------------------------------
# find_existing_tests
# ---------------------------------------------------------------------------


class TestFindExistingTests:
    def test_finds_python_tests(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("def test_x(): pass")
        (tests_dir / "helper.py").write_text("# not a test")
        found = find_existing_tests(tmp_path, "python")
        assert len(found) == 1
        assert found[0].name == "test_main.py"

    def test_finds_nodejs_tests(self, tmp_path):
        test_dir = tmp_path / "__tests__"
        test_dir.mkdir()
        (test_dir / "app.test.js").write_text("test('x', () => {})")
        found = find_existing_tests(tmp_path, "nodejs")
        assert len(found) == 1

    def test_no_tests_returns_empty(self, tmp_path):
        assert find_existing_tests(tmp_path, "python") == []

    def test_finds_go_tests(self, tmp_path):
        (tmp_path / "main_test.go").write_text("package main")
        found = find_existing_tests(tmp_path, "go")
        assert len(found) == 1

    def test_finds_ruby_specs(self, tmp_path):
        spec_dir = tmp_path / "spec"
        spec_dir.mkdir()
        (spec_dir / "app_spec.rb").write_text("RSpec.describe 'x' do; end")
        found = find_existing_tests(tmp_path, "ruby")
        assert len(found) == 1


# ---------------------------------------------------------------------------
# scaffold_test
# ---------------------------------------------------------------------------


class TestScaffoldTest:
    def test_creates_python_test(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('name = "mylib"')
        created = scaffold_test(tmp_path, "python", yes=True)
        assert created is not None
        assert created.exists()
        assert "test_mylib.py" in created.name
        content = created.read_text()
        assert "import mylib" in content

    def test_creates_nodejs_test(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "myapp"}')
        created = scaffold_test(tmp_path, "nodejs", yes=True)
        assert created is not None
        assert created.exists()
        assert "myapp.test.js" in created.name

    def test_creates_rust_test(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "mycrate"')
        created = scaffold_test(tmp_path, "rust", yes=True)
        assert created is not None
        assert "placeholder_test.rs" in created.name

    def test_creates_go_test(self, tmp_path):
        (tmp_path / "go.mod").write_text("module example.com/mymod")
        created = scaffold_test(tmp_path, "go", yes=True)
        assert created is not None
        assert "placeholder_test.go" in created.name

    def test_creates_ruby_spec(self, tmp_path):
        (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'")
        created = scaffold_test(tmp_path, "ruby", yes=True)
        assert created is not None
        content = created.read_text()
        assert "RSpec.describe" in content

    def test_creates_php_test(self, tmp_path):
        (tmp_path / "composer.json").write_text('{"name": "vendor/pkg"}')
        created = scaffold_test(tmp_path, "php", yes=True)
        assert created is not None
        assert "PlaceholderTest.php" in created.name

    def test_creates_dotnet_test(self, tmp_path):
        (tmp_path / "App.csproj").write_text("<Project/>")
        created = scaffold_test(tmp_path, "dotnet", yes=True)
        assert created is not None
        assert "PlaceholderTest.cs" in created.name

    def test_creates_java_test(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project/>")
        created = scaffold_test(tmp_path, "java", yes=True)
        assert created is not None
        assert "PlaceholderTest.java" in created.name

    def test_skips_when_tests_exist(self, tmp_path):
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_existing.py").write_text("def test_x(): pass")
        created = scaffold_test(tmp_path, "python", yes=True)
        assert created is None

    def test_scaffold_in_tests_project_avoids_nested_dir(self, tmp_path):
        tests_proj = tmp_path / "tests"
        tests_proj.mkdir()
        (tests_proj / "pyproject.toml").write_text('name = "myapp-tests"')
        created = scaffold_test(tests_proj, "python", yes=True)
        assert created is not None
        assert created.parent == tests_proj
        assert "import tests" in created.read_text()

    def test_skips_unknown_type(self, tmp_path):
        created = scaffold_test(tmp_path, "unknown_lang", yes=True)
        assert created is None

    def test_interactive_decline(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('name = "mylib"')
        with mock.patch("click.confirm", return_value=False):
            created = scaffold_test(tmp_path, "python", yes=False)
        assert created is None


# ---------------------------------------------------------------------------
# ensure_project_environment (Python)
# ---------------------------------------------------------------------------


class TestEnsureProjectEnvironmentPython:
    def test_creates_venv_and_installs(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testpkg"\nversion = "0.1.0"'
        )
        # Mock subprocess to avoid slow venv creation and pip installs
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="3.9.0", stderr=""
            )
            result = ensure_project_environment(tmp_path, "python", yes=True)
            assert result is True
            # Verify venv creation was attempted
            venv_calls = [
                call
                for call in mock_run.call_args_list
                if "-m" in str(call) and "venv" in str(call)
            ]
            assert len(venv_calls) >= 1

    def test_skips_if_venv_exists(self, tmp_path):
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        (tmp_path / ".venv" / "bin" / "python").write_text("#!/bin/sh")
        (tmp_path / ".venv" / "bin" / "python").chmod(0o755)
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="3.9.0", stderr=""
            )
            result = ensure_project_environment(tmp_path, "python", yes=True)
            assert result is True
            # Should not create venv (no call with -m venv), but pip upgrade is still called
            calls_args = [call.args[0] for call in mock_run.call_args_list if call.args]
            venv_module_calls = [
                args for args in calls_args if "-m" in args and "venv" in args
            ]
            assert len(venv_module_calls) == 0, (
                "venv creation should be skipped when .venv exists"
            )

    def test_interactive_decline(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"')
        with mock.patch("click.confirm", return_value=False):
            result = ensure_project_environment(tmp_path, "python", yes=False)
        assert result is True  # declined is not a failure
        assert not (tmp_path / ".venv").exists()


# ---------------------------------------------------------------------------
# ensure_project_environment (generic / non-Python)
# ---------------------------------------------------------------------------


class TestEnsureProjectEnvironmentGeneric:
    def test_unknown_type_returns_true(self, tmp_path):
        assert ensure_project_environment(tmp_path, "unknown_lang") is True

    def test_nodejs_with_missing_npm(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "x"}')
        with mock.patch("shutil.which", return_value=None):
            result = ensure_project_environment(tmp_path, "nodejs", yes=True)
        assert result is True  # skips gracefully


# ---------------------------------------------------------------------------
# OpenRouter / pfix env discovery
# ---------------------------------------------------------------------------


class TestOpenRouterEnvDiscovery:
    def test_finds_parent_env_over_blank_local_env(self, tmp_path):
        root_env = tmp_path / ".env"
        root_env.write_text(
            "OPENROUTER_API_KEY=sk-or-v1-root-key\nLLM_MODEL=openrouter/qwen/qwen3-coder-next\n",
            encoding="utf-8",
        )

        sub = tmp_path / "my-api"
        sub.mkdir()
        (sub / ".env").write_text("OPENROUTER_API_KEY=\n", encoding="utf-8")

        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            env_file, api_key = _find_openrouter_api_key(sub)

        assert env_file == root_env
        assert api_key == "sk-or-v1-root-key"
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            assert _validate_pfix_env(sub) is True

    def test_does_not_create_local_env_when_parent_key_exists(self, tmp_path):
        root_env = tmp_path / ".env"
        root_env.write_text(
            "OPENROUTER_API_KEY=sk-or-v1-root-key\n",
            encoding="utf-8",
        )

        sub = tmp_path / "my-api"
        sub.mkdir()

        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            assert _ensure_pfix_env(sub) is True

        assert not (sub / ".env").exists()

    def test_creates_llm_model_template_when_no_api_key_exists(self, tmp_path):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True):
            assert _ensure_pfix_env(tmp_path) is True

        env_text = (tmp_path / ".env").read_text(encoding="utf-8")
        example_text = (tmp_path / ".env.example").read_text(encoding="utf-8")

        assert "LLM_MODEL=openrouter/qwen/qwen3-coder-next" in env_text
        assert "LLM_MODEL=openrouter/qwen/qwen3-coder-next" in example_text
        assert "PFIX_MODEL" not in env_text
        assert "PFIX_MODEL" not in example_text


# ---------------------------------------------------------------------------
# Python test dependency installation
# ---------------------------------------------------------------------------


class TestPythonTestDependency:
    def test_installs_missing_pytest(self, tmp_path):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=1, stdout="", stderr="ModuleNotFoundError"),  # import fails
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # pip install pytest
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # addopts check after install
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/python3", "pytest")
                is True
            )

        assert mock_run.call_args_list[0].args[0] == [
            "/usr/bin/python3",
            "-c",
            "import pytest; print(pytest.__version__)",
        ]
        assert mock_run.call_args_list[1].args[0] == [
            "/usr/bin/python3",
            "-m",
            "pip",
            "install",
            "pytest",
        ]
        assert mock_run.call_args_list[2].args[0] == [
            "/usr/bin/python3",
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ]
        assert mock_run.call_count == 3

    def test_pytest_importable_but_addopts_broken_triggers_dev_extras_reinstall(
        self, tmp_path
    ):
        """2026-07-06 regression: `import pytest` succeeding is not enough --
        pyproject.toml's own `addopts` (e.g. `-n auto`) can need a plugin
        that lives under [project.optional-dependencies] dev, which a bare
        `uv sync`/`pip install pytest` never installs. Must escalate to a
        full editable+dev reinstall, then re-verify before reporting ready.
        """
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
                mock.MagicMock(returncode=0, stdout="9.0.0", stderr=""),  # import pytest OK
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),  # addopts check: broken
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # pip install pytest (no-op fix)
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),  # addopts check: still broken
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # dev-extras reinstall
                mock.MagicMock(
                    returncode=4, stdout="", stderr="error: unrecognized arguments: -n"
                ),  # addopts check: still broken even after dev extras
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/python3", "pytest")
                is False
            )

    def test_already_installed_pytest_with_working_addopts_is_fast_path(self, tmp_path):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0, stdout="9.0.0", stderr=""),  # import pytest OK
                mock.MagicMock(returncode=0, stdout="", stderr=""),  # addopts smoke test OK
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/python3", "pytest")
                is True
            )
        assert mock_run.call_count == 2

    def test_non_pytest_test_dep_skips_addopts_check(self, tmp_path):
        """jest/rspec/etc. aren't Python pytest plugins -- the addopts smoke
        test only makes sense for test_dep == 'pytest'."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                mock.MagicMock(returncode=0, stdout="1.0.0", stderr=""),
            ]

            assert (
                _ensure_python_test_dependency(tmp_path, "/usr/bin/node", "jest")
                is True
            )
        assert mock_run.call_count == 1


# ---------------------------------------------------------------------------
# pfix installation source selection
# ---------------------------------------------------------------------------


class TestPfixInstallSource:
    def test_installs_pfix_from_pypi_by_default(self, tmp_path):
        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch(
                "goal.project_bootstrap._find_python_bin",
                return_value="/usr/bin/python3",
            ),
            mock.patch("goal.project_bootstrap._ensure_pfix_config", return_value=True),
            mock.patch("goal.project_bootstrap._ensure_pfix_env", return_value=True),
            mock.patch("goal.project_bootstrap._validate_pfix_env", return_value=True),
            mock.patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                mock.MagicMock(returncode=1, stdout="", stderr="ModuleNotFoundError"),
                mock.MagicMock(returncode=0, stdout="", stderr=""),
            ]

            assert _ensure_pfix_installed(tmp_path, yes=True) is True

        assert mock_run.call_args_list[1].args[0] == [
            "/usr/bin/python3",
            "-m",
            "pip",
            "install",
            "pfix>=0.1.60",
        ]

    def test_installs_pfix_from_local_path_when_configured(self, tmp_path):
        local_pfix = tmp_path / "local-pfix"
        local_pfix.mkdir()

        with (
            mock.patch.dict(
                os.environ, {"GOAL_PFIX_LOCAL_PATH": str(local_pfix)}, clear=False
            ),
            mock.patch(
                "goal.project_bootstrap._find_python_bin",
                return_value="/usr/bin/python3",
            ),
            mock.patch("goal.project_bootstrap._ensure_pfix_config", return_value=True),
            mock.patch("goal.project_bootstrap._ensure_pfix_env", return_value=True),
            mock.patch("goal.project_bootstrap._validate_pfix_env", return_value=True),
            mock.patch("subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                mock.MagicMock(returncode=1, stdout="", stderr="ModuleNotFoundError"),
                mock.MagicMock(returncode=0, stdout="", stderr=""),
            ]

            assert _ensure_pfix_installed(tmp_path, yes=True) is True

        assert mock_run.call_args_list[1].args[0] == [
            "/usr/bin/python3",
            "-m",
            "pip",
            "install",
            "-e",
            str(local_pfix.resolve()),
        ]


# ---------------------------------------------------------------------------
# costs / badge generation
# ---------------------------------------------------------------------------


class TestCostsBadgeGeneration:
    def test_costs_install_upgrades_stale_version(self, tmp_path):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            import_command = [
                "/usr/bin/python",
                "-c",
                "import costs; print(costs.__version__)",
            ]
            if command[:3] == import_command:
                return mock.MagicMock(returncode=0, stdout="0.1.51\n", stderr="")
            return mock.MagicMock(returncode=0, stdout="", stderr="")

        with mock.patch("goal.bootstrap.costs_badge.subprocess.run", side_effect=fake_run):
            assert _install_costs_package(tmp_path, "/usr/bin/python") is True

        assert calls == [
            ["/usr/bin/python", "-c", "import costs; print(costs.__version__)"],
            [
                "/usr/bin/python",
                "-m",
                "pip",
                "install",
                "-U",
                "costs>=0.1.53",
            ],
        ]

    def test_costs_install_falls_back_to_uv_when_pip_unavailable(self, tmp_path):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            import_command = [
                "/venv/bin/python",
                "-c",
                "import costs; print(costs.__version__)",
            ]
            if command[:3] == import_command:
                return mock.MagicMock(returncode=0, stdout="0.1.51\n", stderr="")
            if command[:4] == ["/venv/bin/python", "-m", "pip", "install"]:
                return mock.MagicMock(returncode=1, stdout="", stderr="No module named pip")
            return mock.MagicMock(returncode=0, stdout="", stderr="")

        with (
            mock.patch("goal.bootstrap.costs_badge.shutil.which", return_value="/usr/bin/uv"),
            mock.patch("goal.bootstrap.costs_badge.subprocess.run", side_effect=fake_run),
        ):
            assert _install_costs_package(tmp_path, "/venv/bin/python") is True

        assert calls[-1] == [
            "/usr/bin/uv",
            "pip",
            "install",
            "--python",
            "/venv/bin/python",
            "costs>=0.1.53",
        ]

    def test_uses_git_root_for_subproject_analysis(self, tmp_path):
        repo_root = tmp_path
        (repo_root / ".git").mkdir()
        (repo_root / "README.md").write_text("# Repo\n\n## AI Cost Tracking\n")
        (repo_root / "pyproject.toml").write_text(
            '[project]\nname = "goal"\nversion = "2.1.262"\n',
            encoding="utf-8",
        )

        subproject = repo_root / "my-api"
        subproject.mkdir()

        fake_costs = types.ModuleType("costs")
        fake_costs.__path__ = []
        fake_costs.calculate_human_time = lambda commits: 1.0
        calls = {}

        def fake_update_readme_badge(project_dir, results):
            calls["readme_update"] = project_dir
            calls["readme_results"] = results
            return True

        fake_costs.update_readme_badge = fake_update_readme_badge

        fake_git_parser = types.ModuleType("costs.git_parser")

        class FakeAuthor:
            name = "Tom"

        class FakeCommit:
            def __init__(self):
                from datetime import datetime, timezone

                self.hexsha = "abc123"
                self.committed_datetime = datetime(2026, 1, 1, tzinfo=timezone.utc)
                self.author = FakeAuthor()

        def fake_get_repo_stats(path):
            calls["repo_stats"] = path
            return {"repo_name": "goal"}

        def fake_parse_commits(path, max_count, ai_only, full_history):
            calls["parse_commits"] = (path, max_count, ai_only, full_history)
            return [(FakeCommit(), "AI: generated by llm")]

        def fake_get_commit_diff(path, sha):
            calls["commit_diff"] = (path, sha)
            return "diff --git a/file b/file"

        fake_git_parser.get_repo_stats = fake_get_repo_stats
        fake_git_parser.parse_commits = fake_parse_commits
        fake_git_parser.get_commit_diff = fake_get_commit_diff

        fake_calculator = types.ModuleType("costs.calculator")
        fake_calculator.ai_cost = lambda diff, model=None, api_key=None: {"cost": 0.25}

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "costs": fake_costs,
                    "costs.git_parser": fake_git_parser,
                    "costs.calculator": fake_calculator,
                },
                clear=False,
            ),
            mock.patch("subprocess.run") as mock_run,
            mock.patch(
                "goal.project_bootstrap._ensure_costs_config", return_value=True
            ),
            mock.patch(
                "goal.project_bootstrap._ensure_env_template", return_value=True
            ),
        ):
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="0.1.48", stderr=""
            )
            result = _ensure_costs_installed(subproject, "/usr/bin/python")

        assert result is True
        assert _find_git_root(subproject) == repo_root
        assert calls["repo_stats"] == str(repo_root)
        assert calls["parse_commits"][0] == str(repo_root)
        assert calls["commit_diff"][0] == str(repo_root)
        assert calls["readme_update"] == repo_root
        assert calls["readme_results"]["summary"]["version"] == "2.1.262"


# ---------------------------------------------------------------------------
# bootstrap_project
# ---------------------------------------------------------------------------


class TestBootstrapProject:
    def test_full_bootstrap_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testpkg"\nversion = "0.1.0"'
        )
        # Mock expensive operations
        with (
            mock.patch("subprocess.run") as mock_run,
            mock.patch("goal.project_bootstrap._ensure_costs_installed") as mock_costs,
            mock.patch("goal.project_bootstrap._ensure_pfix_installed") as mock_pfix,
        ):
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="3.9.0", stderr=""
            )
            mock_costs.return_value = True
            mock_pfix.return_value = True
            result = bootstrap_project(tmp_path, "python", yes=True)
            assert result["env_ok"] is True
            assert result["project_type"] == "python"
            # Should have created a scaffold test since none existed
            assert result["test_created"] is not None
            assert result["test_created"].exists()
            assert len(result["tests_found"]) >= 1

    def test_bootstrap_with_existing_tests(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testpkg"\nversion = "0.1.0"'
        )
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_existing.py").write_text("def test_x(): pass")
        # Mock expensive operations
        with (
            mock.patch("subprocess.run") as mock_run,
            mock.patch("goal.project_bootstrap._ensure_costs_installed") as mock_costs,
            mock.patch("goal.project_bootstrap._ensure_pfix_installed") as mock_pfix,
        ):
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="3.9.0", stderr=""
            )
            mock_costs.return_value = True
            mock_pfix.return_value = True
            result = bootstrap_project(tmp_path, "python", yes=True)
            assert result["test_created"] is None
            assert len(result["tests_found"]) == 1


# ---------------------------------------------------------------------------
# bootstrap_all_projects
# ---------------------------------------------------------------------------


class TestBootstrapAllProjects:
    def test_detects_and_bootstraps(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "root"\nversion = "0.1.0"'
        )
        sub = tmp_path / "frontend"
        sub.mkdir()
        (sub / "package.json").write_text('{"name": "frontend"}')

        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Mock expensive operations
            with (
                mock.patch("subprocess.run") as mock_run,
                mock.patch(
                    "goal.project_bootstrap._ensure_costs_installed"
                ) as mock_costs,
                mock.patch(
                    "goal.project_bootstrap._ensure_pfix_installed"
                ) as mock_pfix,
                mock.patch("shutil.which") as mock_which,
            ):
                mock_run.return_value = mock.MagicMock(returncode=0)
                mock_costs.return_value = True
                mock_pfix.return_value = True
                mock_which.return_value = "/usr/bin/npm"
                results = bootstrap_all_projects(tmp_path, yes=True)
        finally:
            os.chdir(old)

        types_found = {r["project_type"] for r in results}
        assert "python" in types_found
        # nodejs may or may not succeed (npm might not be installed) but should be detected
        assert any(r["project_type"] == "nodejs" for r in results)

    def test_empty_dir(self, tmp_path):
        old = os.getcwd()
        try:
            os.chdir(tmp_path)
            results = bootstrap_all_projects(tmp_path, yes=True)
        finally:
            os.chdir(old)
        assert results == []


# ---------------------------------------------------------------------------
# CLI: goal bootstrap
# ---------------------------------------------------------------------------


class TestBootstrapCommand:
    def test_bootstrap_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "--help"])
        assert result.exit_code == 0
        assert "Bootstrap project environments" in result.output

    def test_bootstrap_empty_dir(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "No project types detected" in result.output

    def test_bootstrap_python_project(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testpkg"\nversion = "0.1.0"'
        )
        runner = CliRunner()
        # Mock subprocess to avoid slow venv/pip operations
        with (
            mock.patch("subprocess.run") as mock_run,
            mock.patch("goal.project_bootstrap._ensure_costs_installed") as mock_costs,
            mock.patch("goal.project_bootstrap._ensure_pfix_installed") as mock_pfix,
        ):
            mock_run.return_value = mock.MagicMock(
                returncode=0, stdout="3.9.0", stderr=""
            )
            mock_costs.return_value = True
            mock_pfix.return_value = True
            result = runner.invoke(main, ["bootstrap", "-y", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Bootstrap complete" in result.output
        assert "python" in result.output


# ---------------------------------------------------------------------------
# All project types have required keys in PROJECT_BOOTSTRAP
# ---------------------------------------------------------------------------


class TestProjectBootstrapConfig:
    @pytest.mark.parametrize("ptype", list(PROJECT_BOOTSTRAP.keys()))
    def test_required_keys(self, ptype):
        cfg = PROJECT_BOOTSTRAP[ptype]
        assert "marker_files" in cfg
        assert "test_dirs" in cfg
        assert "test_patterns" in cfg
        assert "dep_install_commands" in cfg
        assert "scaffold_test" in cfg
        assert isinstance(cfg["marker_files"], list)
        assert isinstance(cfg["test_dirs"], list)
        assert isinstance(cfg["dep_install_commands"], list)


def _write_pyproject(tmp_path, body: str):
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    return tmp_path


def test_pfix_auto_apply_defaults_true(tmp_path):
    from goal.project_bootstrap import _pfix_auto_apply

    # no pyproject at all
    assert _pfix_auto_apply(tmp_path) is True
    # pyproject without [tool.pfix]
    _write_pyproject(tmp_path, "[project]\nname = 'x'\n")
    assert _pfix_auto_apply(tmp_path) is True
    # [tool.pfix] without auto_apply key
    _write_pyproject(tmp_path, "[tool.pfix]\nmodel = 'm'\n")
    assert _pfix_auto_apply(tmp_path) is True


def test_pfix_auto_apply_false_is_respected(tmp_path):
    from goal.project_bootstrap import _pfix_auto_apply

    _write_pyproject(tmp_path, "[tool.pfix]\nauto_apply = false\n")
    assert _pfix_auto_apply(tmp_path) is False
    _write_pyproject(tmp_path, "[tool.pfix]\nauto_apply = true\n")
    assert _pfix_auto_apply(tmp_path) is True


def test_run_bootstrap_diagnostics_gated_by_auto_apply(tmp_path, monkeypatch):
    import goal.project_bootstrap as pb

    captured = {}

    def fake_diag(project_dir, project_type, auto_fix):
        captured["auto_fix"] = auto_fix
        return {"ok": True}

    monkeypatch.setattr(pb, "diagnose_and_report", fake_diag)

    # auto_apply = false -> even with yes=True, auto_fix must be False
    _write_pyproject(tmp_path, "[tool.pfix]\nauto_apply = false\n")
    pb._run_bootstrap_diagnostics(tmp_path, "python", yes=True)
    assert captured["auto_fix"] is False

    # auto_apply = true -> yes=True propagates as auto_fix=True
    _write_pyproject(tmp_path, "[tool.pfix]\nauto_apply = true\n")
    pb._run_bootstrap_diagnostics(tmp_path, "python", yes=True)
    assert captured["auto_fix"] is True

    # yes=False is always False regardless of setting
    pb._run_bootstrap_diagnostics(tmp_path, "python", yes=False)
    assert captured["auto_fix"] is False


def test_auto_fix_enabled_reads_goal_yaml(tmp_path):
    from goal.project_bootstrap import _auto_fix_enabled

    (tmp_path / "goal.yaml").write_text("auto_apply: false\n", encoding="utf-8")
    assert _auto_fix_enabled(tmp_path) is False
    (tmp_path / "goal.yaml").write_text("advanced:\n  auto_apply: false\n", encoding="utf-8")
    assert _auto_fix_enabled(tmp_path) is False
    (tmp_path / "goal.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    assert _auto_fix_enabled(tmp_path) is True  # unset -> default True


def test_auto_fix_enabled_env_override(tmp_path, monkeypatch):
    from goal.project_bootstrap import _auto_fix_enabled

    (tmp_path / "goal.yaml").write_text("auto_apply: true\n", encoding="utf-8")
    monkeypatch.setenv("GOAL_AUTO_FIX", "false")
    assert _auto_fix_enabled(tmp_path) is False
    monkeypatch.setenv("GOAL_AUTO_FIX", "true")
    assert _auto_fix_enabled(tmp_path) is True
