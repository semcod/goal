"""Tests for project doctor — auto-diagnosis and auto-fix of project config issues."""

import json
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from goal.project_doctor import (
    Issue,
    DoctorReport,
    diagnose_project,
    diagnose_and_report,
    _diagnose_python,
    _diagnose_nodejs,
    _diagnose_rust,
    _diagnose_go,
    _diagnose_ruby,
    _diagnose_php,
    _diagnose_dotnet,
    _diagnose_java,
)
from goal.cli import main


# ---------------------------------------------------------------------------
# DoctorReport model
# ---------------------------------------------------------------------------

class TestDoctorReport:
    def test_properties(self):
        report = DoctorReport(project_dir=Path('.'), project_type='python', issues=[
            Issue(severity='error', code='E1', title='err', detail=''),
            Issue(severity='warning', code='W1', title='warn', detail=''),
            Issue(severity='info', code='I1', title='info', detail=''),
            Issue(severity='error', code='E2', title='fixed err', detail='', fixed=True),
        ])
        assert len(report.errors) == 2
        assert len(report.warnings) == 1
        assert len(report.fixed) == 1
        assert report.has_problems is True

    def test_no_problems(self):
        report = DoctorReport(project_dir=Path('.'), project_type='python', issues=[
            Issue(severity='info', code='I1', title='info', detail=''),
        ])
        assert report.has_problems is False


# ---------------------------------------------------------------------------
# Python diagnostics
# ---------------------------------------------------------------------------

class TestDiagnosePython:
    def test_no_pyproject(self, tmp_path):
        issues = _diagnose_python(tmp_path)
        assert issues == []

    def test_only_requirements_txt(self, tmp_path):
        (tmp_path / 'requirements.txt').write_text('click\n')
        issues = _diagnose_python(tmp_path)
        assert any(i.code == 'PY001' for i in issues)

    def test_missing_build_system(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        issues = _diagnose_python(tmp_path, auto_fix=True)
        py002 = [i for i in issues if i.code == 'PY002']
        assert len(py002) == 1
        assert py002[0].fixed is True
        content = (tmp_path / 'pyproject.toml').read_text()
        assert '[build-system]' in content
        assert 'setuptools' in content

    def test_missing_build_system_no_fix(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        issues = _diagnose_python(tmp_path, auto_fix=False)
        py002 = [i for i in issues if i.code == 'PY002']
        assert len(py002) == 1
        assert py002[0].fixed is False
        content = (tmp_path / 'pyproject.toml').read_text()
        assert '[build-system]' not in content

    def test_deprecated_license_classifier(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = "x"\nversion = "0.1.0"\n'
            'classifiers = [\n'
            '    "Development Status :: 3 - Alpha",\n'
            '    "License :: OSI Approved :: MIT License",\n'
            ']\n'
        )
        issues = _diagnose_python(tmp_path, auto_fix=True)
        py003 = [i for i in issues if i.code == 'PY003']
        assert len(py003) == 1
        assert py003[0].fixed is True
        content = (tmp_path / 'pyproject.toml').read_text()
        assert 'License :: OSI Approved' not in content
        assert 'Development Status' in content

    def test_broken_backend(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\n'
            'build-backend = "setuptools.backends._legacy"\n\n'
            '[project]\nname = "x"\n'
        )
        issues = _diagnose_python(tmp_path, auto_fix=True)
        py004 = [i for i in issues if i.code == 'PY004']
        assert len(py004) == 1
        assert py004[0].fixed is True
        content = (tmp_path / 'pyproject.toml').read_text()
        assert 'setuptools.build_meta' in content
        assert 'setuptools.backends._legacy' not in content

    def test_license_table_format(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = "x"\n'
            'license = {text = "MIT"}\n'
        )
        issues = _diagnose_python(tmp_path, auto_fix=True)
        py005 = [i for i in issues if i.code == 'PY005']
        assert len(py005) == 1
        assert py005[0].fixed is True
        content = (tmp_path / 'pyproject.toml').read_text()
        assert 'license = "MIT"' in content

    def test_duplicate_authors(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = "x"\n'
            'authors = [\n'
            '    {name = "Alice", email = "a@b.com"},\n'
            '    {name = "Alice", email = "a@b.com"},\n'
            ']\n'
        )
        issues = _diagnose_python(tmp_path, auto_fix=True)
        py006 = [i for i in issues if i.code == 'PY006']
        assert len(py006) == 1
        assert py006[0].fixed is True
        content = (tmp_path / 'pyproject.toml').read_text()
        assert content.count('{name = "Alice"') == 1

    def test_missing_requires_python(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = "x"\nversion = "0.1.0"\n'
        )
        issues = _diagnose_python(tmp_path, auto_fix=True)
        py007 = [i for i in issues if i.code == 'PY007']
        assert len(py007) == 1
        assert py007[0].fixed is True
        content = (tmp_path / 'pyproject.toml').read_text()
        assert 'requires-python' in content

    def test_healthy_project(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = "x"\nversion = "0.1.0"\n'
            'requires-python = ">=3.8"\n'
            'license = "MIT"\n'
            'authors = [\n    {name = "Alice", email = "a@b.com"},\n]\n'
            'classifiers = [\n    "Development Status :: 3 - Alpha",\n]\n'
        )
        issues = _diagnose_python(tmp_path)
        assert all(i.severity != 'error' for i in issues)


# ---------------------------------------------------------------------------
# Node.js diagnostics
# ---------------------------------------------------------------------------

class TestDiagnoseNodejs:
    def test_no_package_json(self, tmp_path):
        assert _diagnose_nodejs(tmp_path) == []

    def test_invalid_json(self, tmp_path):
        (tmp_path / 'package.json').write_text('{invalid')
        issues = _diagnose_nodejs(tmp_path)
        assert any(i.code == 'JS001' for i in issues)

    def test_missing_version(self, tmp_path):
        (tmp_path / 'package.json').write_text('{"name": "x"}')
        issues = _diagnose_nodejs(tmp_path, auto_fix=True)
        js003 = [i for i in issues if i.code == 'JS003']
        assert len(js003) == 1
        assert js003[0].fixed is True
        data = json.loads((tmp_path / 'package.json').read_text())
        assert data['version'] == '0.1.0'

    def test_missing_test_script(self, tmp_path):
        (tmp_path / 'package.json').write_text('{"name": "x", "version": "1.0.0"}')
        issues = _diagnose_nodejs(tmp_path)
        assert any(i.code == 'JS004' for i in issues)

    def test_no_test_specified(self, tmp_path):
        (tmp_path / 'package.json').write_text(
            '{"name": "x", "version": "1.0.0", "scripts": {"test": "echo \\"Error: no test specified\\" && exit 1"}}'
        )
        issues = _diagnose_nodejs(tmp_path)
        assert any(i.code == 'JS004' for i in issues)

    def test_healthy_nodejs(self, tmp_path):
        (tmp_path / 'package.json').write_text(
            '{"name": "x", "version": "1.0.0", "main": "index.js", "scripts": {"test": "jest"}}'
        )
        issues = _diagnose_nodejs(tmp_path)
        assert not any(i.severity == 'error' for i in issues)


# ---------------------------------------------------------------------------
# Rust diagnostics
# ---------------------------------------------------------------------------

class TestDiagnoseRust:
    def test_no_cargo(self, tmp_path):
        assert _diagnose_rust(tmp_path) == []

    def test_missing_package(self, tmp_path):
        (tmp_path / 'Cargo.toml').write_text('[dependencies]\n')
        issues = _diagnose_rust(tmp_path)
        assert any(i.code == 'RS001' for i in issues)

    def test_missing_edition(self, tmp_path):
        (tmp_path / 'Cargo.toml').write_text('[package]\nname = "x"\nversion = "0.1.0"\n')
        issues = _diagnose_rust(tmp_path)
        assert any(i.code == 'RS002' for i in issues)


# ---------------------------------------------------------------------------
# Go diagnostics
# ---------------------------------------------------------------------------

class TestDiagnoseGo:
    def test_no_gomod(self, tmp_path):
        assert _diagnose_go(tmp_path) == []

    def test_invalid_gomod(self, tmp_path):
        (tmp_path / 'go.mod').write_text('invalid content')
        issues = _diagnose_go(tmp_path)
        assert any(i.code == 'GO001' for i in issues)

    def test_missing_gosum(self, tmp_path):
        (tmp_path / 'go.mod').write_text('module example.com/x\n\nrequire github.com/pkg v1.0.0\n')
        issues = _diagnose_go(tmp_path)
        assert any(i.code == 'GO002' for i in issues)


# ---------------------------------------------------------------------------
# Ruby diagnostics
# ---------------------------------------------------------------------------

class TestDiagnoseRuby:
    def test_no_gemfile(self, tmp_path):
        assert _diagnose_ruby(tmp_path) == []

    def test_missing_lock(self, tmp_path):
        (tmp_path / 'Gemfile').write_text("source 'https://rubygems.org'\n")
        issues = _diagnose_ruby(tmp_path)
        assert any(i.code == 'RB001' for i in issues)


# ---------------------------------------------------------------------------
# PHP diagnostics
# ---------------------------------------------------------------------------

class TestDiagnosePhp:
    def test_no_composer(self, tmp_path):
        assert _diagnose_php(tmp_path) == []

    def test_invalid_json(self, tmp_path):
        (tmp_path / 'composer.json').write_text('{bad')
        issues = _diagnose_php(tmp_path)
        assert any(i.code == 'PHP001' for i in issues)

    def test_missing_autoload(self, tmp_path):
        (tmp_path / 'composer.json').write_text('{"name": "vendor/x"}')
        issues = _diagnose_php(tmp_path)
        assert any(i.code == 'PHP002' for i in issues)


# ---------------------------------------------------------------------------
# .NET diagnostics
# ---------------------------------------------------------------------------

class TestDiagnoseDotnet:
    def test_no_csproj(self, tmp_path):
        assert _diagnose_dotnet(tmp_path) == []

    def test_missing_target_framework(self, tmp_path):
        (tmp_path / 'App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"></Project>')
        issues = _diagnose_dotnet(tmp_path)
        assert any(i.code == 'NET001' for i in issues)


# ---------------------------------------------------------------------------
# Java diagnostics
# ---------------------------------------------------------------------------

class TestDiagnoseJava:
    def test_no_build_file(self, tmp_path):
        issues = _diagnose_java(tmp_path)
        assert all(i.severity == 'info' for i in issues)

    def test_missing_model_version(self, tmp_path):
        (tmp_path / 'pom.xml').write_text('<project></project>')
        issues = _diagnose_java(tmp_path)
        assert any(i.code == 'JV001' for i in issues)


# ---------------------------------------------------------------------------
# diagnose_project (dispatcher)
# ---------------------------------------------------------------------------

class TestDiagnoseProject:
    def test_unknown_type(self, tmp_path):
        report = diagnose_project(tmp_path, 'unknown_lang')
        assert report.issues == []

    def test_python_dispatch(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        report = diagnose_project(tmp_path, 'python', auto_fix=False)
        assert any(i.code == 'PY002' for i in report.issues)


# ---------------------------------------------------------------------------
# diagnose_and_report (with output)
# ---------------------------------------------------------------------------

class TestDiagnoseAndReport:
    def test_prints_report(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        report = diagnose_and_report(tmp_path, 'python', auto_fix=False)
        assert report.has_problems

    def test_healthy_project(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = "x"\nversion = "0.1.0"\nrequires-python = ">=3.8"\n'
            'license = "MIT"\nauthors = [{name = "A", email = "a@b.com"}]\n'
            'classifiers = ["Development Status :: 3 - Alpha"]\n'
        )
        report = diagnose_and_report(tmp_path, 'python')
        assert not report.has_problems


# ---------------------------------------------------------------------------
# CLI: goal doctor
# ---------------------------------------------------------------------------

class TestDoctorCommand:
    def test_doctor_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ['doctor', '--help'])
        assert result.exit_code == 0
        assert 'Diagnose and auto-fix' in result.output

    def test_doctor_empty_dir(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ['doctor', '-p', str(tmp_path)])
        assert result.exit_code == 0
        assert 'No known project types' in result.output

    def test_doctor_finds_python_issues(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text(
            '[project]\nname = "x"\n'
            'classifiers = [\n    "License :: OSI Approved :: MIT License",\n]\n'
        )
        runner = CliRunner()
        result = runner.invoke(main, ['doctor', '-p', str(tmp_path)])
        assert result.exit_code == 0
        assert 'PY002' in result.output or 'PY003' in result.output

    def test_doctor_no_fix(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        runner = CliRunner()
        result = runner.invoke(main, ['doctor', '--no-fix', '-p', str(tmp_path)])
        assert result.exit_code == 0
        content = (tmp_path / 'pyproject.toml').read_text()
        assert '[build-system]' not in content  # should NOT have been fixed

    def test_doctor_with_fix(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[project]\nname = "x"\n')
        runner = CliRunner()
        result = runner.invoke(main, ['doctor', '--fix', '-p', str(tmp_path)])
        assert result.exit_code == 0
        content = (tmp_path / 'pyproject.toml').read_text()
        assert '[build-system]' in content  # should have been fixed
        assert 'FIXED' in result.output or 'auto-fixed' in result.output
