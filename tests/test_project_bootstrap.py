"""Tests for project environment bootstrapping and test scaffolding."""

import json
import os
import subprocess
from pathlib import Path
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
)
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
        result = ensure_project_environment(tmp_path, "python", yes=True)
        assert result is True
        assert (tmp_path / ".venv").exists()
        assert (tmp_path / ".venv" / "bin" / "python").exists()

    def test_skips_if_venv_exists(self, tmp_path):
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        (tmp_path / ".venv" / "bin" / "python").write_text("#!/bin/sh")
        (tmp_path / ".venv" / "bin" / "python").chmod(0o755)
        result = ensure_project_environment(tmp_path, "python", yes=True)
        assert result is True

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
# bootstrap_project
# ---------------------------------------------------------------------------

class TestBootstrapProject:
    def test_full_bootstrap_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testpkg"\nversion = "0.1.0"'
        )
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
        result = runner.invoke(main, ["bootstrap", "-p", str(tmp_path)])
        assert result.exit_code == 0
        assert "No known project types detected" in result.output

    def test_bootstrap_python_project(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testpkg"\nversion = "0.1.0"'
        )
        runner = CliRunner()
        result = runner.invoke(main, ["bootstrap", "-y", "-p", str(tmp_path)])
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
