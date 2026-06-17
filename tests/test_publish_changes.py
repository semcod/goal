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
