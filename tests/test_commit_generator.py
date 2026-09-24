"""Tests for CommitMessageGenerator, ChangeAnalyzer, and ContentAnalyzer."""

from goal.generator.analyzer import ChangeAnalyzer, ContentAnalyzer
from goal.generator.generator import CommitMessageGenerator


def test_detect_scope_src_package():
    analyzer = ChangeAnalyzer()
    files = ["src/clonerd/core.py", "src/clonerd/cli.py", "tests/test_core.py"]
    scope = analyzer.detect_scope(files)
    assert scope == "clonerd"


def test_detect_scope_goal_package():
    analyzer = ChangeAnalyzer()
    files = ["goal/cli/push_cmd.py", "goal/generator/analyzer.py"]
    scope = analyzer.detect_scope(files)
    assert scope == "goal"


def test_detect_scope_non_goal_with_goal_yaml():
    analyzer = ChangeAnalyzer()
    # A third-party project having goal.yaml at root should detect its main package
    files = ["goal.yaml", "src/mytool/main.py", "README.md"]
    scope = analyzer.detect_scope(files)
    assert scope == "mytool"


def test_content_analyzer_does_not_falsely_trigger_on_common_markdown_words():
    analyzer = ContentAnalyzer()
    files = ["README.md", "pyproject.toml", "src/clonerd/core.py"]
    diff = """
+## Overview
+This is a python markdown formatted readme.
+We provide commit message helpers.
"""
    summary = analyzer.short_action_summary(files, diff)
    assert summary != "add markdown output and commit messages"


def test_commit_message_generator_omits_heuristic_notes_by_default():
    generator = CommitMessageGenerator()
    notes = generator._build_implementation_notes()
    assert notes == []

    debug_generator = CommitMessageGenerator(config={"debug_heuristics": True})
    debug_notes = debug_generator._build_implementation_notes()
    assert len(debug_notes) > 0
