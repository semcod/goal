"""Tests for publish skip logic when no package source changed."""

from goal.publish.changes import analyze_publishable_changes


class TestAnalyzePublishableChanges:
    def test_detects_python_source_changes(self):
        report = analyze_publishable_changes(
            ["src/urisys/doctor.py", "CHANGELOG.md", "VERSION"],
            ["python"],
        )
        assert report.has_changes is True
        assert report.publishable_files == ["src/urisys/doctor.py"]

    def test_skips_metadata_only_python_changes(self):
        report = analyze_publishable_changes(
            ["CHANGELOG.md", "README.md", "VERSION", "pyproject.toml", "uv.lock"],
            ["python"],
        )
        assert report.has_changes is False
        assert report.skip_reason == "no_package_source_changes"

    def test_skips_docs_and_tests(self):
        report = analyze_publishable_changes(
            ["docs/README.md", "tests/test_doctor.py", "README.md"],
            ["python"],
        )
        assert report.has_changes is False

    def test_skips_governance_python_helpers(self):
        report = analyze_publishable_changes(
            [
                ".governance/check_required_checks.py",
                ".governance/decision_record.py",
                ".governance/governance_check.py",
            ],
            ["python"],
        )
        assert report.has_changes is False
        assert report.publishable_files == []
        assert report.skip_reason == "no_package_source_changes"

    def test_detects_node_source_changes(self):
        report = analyze_publishable_changes(
            ["src/index.ts", "package-lock.json"],
            ["nodejs"],
        )
        assert report.has_changes is True
        assert report.publishable_files == ["src/index.ts"]

    def test_no_registry_types(self):
        report = analyze_publishable_changes(["README.md"], ["generic"])
        assert report.has_changes is False
        assert report.skip_reason == "no_registry_project_types"

    def test_detects_nested_subproject_source(self):
        report = analyze_publishable_changes(
            ["urisys-node/src/urisysnode/cli.py", "README.md"],
            ["python"],
        )
        assert report.has_changes is True
        assert "urisys-node/src/urisysnode/cli.py" in report.publishable_files

    def test_lockfile_only_changes_are_not_publishable(self):
        report = analyze_publishable_changes(
            ["uv.lock", "pyproject.toml"],
            ["python"],
        )
        assert report.has_changes is False

    def test_empty_project_types_cannot_report_a_successful_publish(self, monkeypatch):
        import importlib

        publish_module = importlib.import_module("goal.cli.publish")

        monkeypatch.setattr(
            publish_module, "validate_project_toml_files", lambda: (True, [])
        )
        assert publish_module.publish_project([], "0.20.44", yes=True) is False

    def test_nested_python_package_is_detected_and_published_from_its_root(
        self, tmp_path, monkeypatch
    ):
        import importlib

        from goal.cli.publish import (
            _prefix_project_command,
            _resolve_python_publish_cmd,
        )
        from goal.cli.version_utils import detect_project_types

        package = tmp_path / "packages" / "wellman"
        dist = package / "dist"
        dist.mkdir(parents=True)
        (package / "pyproject.toml").write_text(
            '[project]\nname = "wellman"\nversion = "0.20.44"\n'
        )
        (dist / "wellman-0.20.44-py3-none-any.whl").write_text("wheel")
        monkeypatch.chdir(tmp_path)

        assert detect_project_types() == ["python"]
        command = _prefix_project_command(
            "twine upload dist/*", package.relative_to(tmp_path)
        )
        resolved = _resolve_python_publish_cmd(command, "0.20.44")

        assert command.startswith("cd packages/wellman &&")
        assert "dist/wellman-0.20.44-py3-none-any.whl" in resolved

        publish_module = importlib.import_module("goal.cli.publish")
        published_commands = []
        monkeypatch.setattr(
            publish_module, "validate_project_toml_files", lambda: (True, [])
        )
        monkeypatch.setattr(
            publish_module,
            "_prepare_python_publish",
            lambda strategy, version: ("/usr/bin/python", True),
        )
        monkeypatch.setattr(
            publish_module,
            "_run_publish_command",
            lambda ptype, publish_cmd, **kwargs: published_commands.append(publish_cmd)
            or True,
        )

        assert publish_module.publish_project(["python"], "0.20.44", yes=True)
        assert published_commands[0].startswith(
            "cd packages/wellman && /usr/bin/python -m build &&"
        )
        assert "/usr/bin/python -m twine upload" in published_commands[0]
