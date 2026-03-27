"""Tests for goal/formatter.py."""
import pytest
from goal.formatter import (
    MarkdownFormatter,
    format_status_output,
    format_push_result,
    _build_functional_overview,
    _determine_next_steps,
)


def test_markdown_formatter_basic():
    """Test basic MarkdownFormatter usage."""
    formatter = MarkdownFormatter()
    formatter.add_header("Test Header", 1)
    result = formatter.render()
    assert "# Test Header" in result
    assert "Generated at" in result


def test_markdown_formatter_with_metadata():
    """Test formatter with metadata."""
    formatter = MarkdownFormatter()
    formatter.add_metadata(version="1.0.0", project="test")
    formatter.add_header("Test", 1)
    result = formatter.render()
    assert "---" in result
    assert "version: 1.0.0" in result


def test_markdown_formatter_section():
    """Test adding section."""
    formatter = MarkdownFormatter()
    formatter.add_section("My Section", "Some content")
    result = formatter.render()
    assert "## My Section" in result
    assert "Some content" in result


def test_markdown_formatter_code_block():
    """Test section with code block."""
    formatter = MarkdownFormatter()
    formatter.add_section("Code", "print('hello')", code_block=True, language="python")
    result = formatter.render()
    assert "```python" in result
    assert "print('hello')" in result


def test_markdown_formatter_list():
    """Test adding list."""
    formatter = MarkdownFormatter()
    formatter.add_list("Items", ["item1", "item2", "item3"])
    result = formatter.render()
    assert "- item1" in result
    assert "- item2" in result
    assert "- item3" in result


def test_markdown_formatter_ordered_list():
    """Test ordered list."""
    formatter = MarkdownFormatter()
    formatter.add_list("Steps", ["step1", "step2"], ordered=True)
    result = formatter.render()
    assert "1. step1" in result
    assert "2. step2" in result


def test_markdown_formatter_command_output():
    """Test command output formatting."""
    formatter = MarkdownFormatter()
    formatter.add_command_output("git status", "nothing to commit", 0)
    result = formatter.render()
    assert "git status" in result
    assert "Success" in result


def test_markdown_formatter_command_failed():
    """Test failed command output."""
    formatter = MarkdownFormatter()
    formatter.add_command_output("pytest", "1 failed", 1)
    result = formatter.render()
    assert "Failed" in result


def test_markdown_formatter_summary():
    """Test summary section."""
    formatter = MarkdownFormatter()
    formatter.add_summary(
        actions_taken=["Staged files", "Committed"],
        next_steps=["Push to remote", "Create PR"]
    )
    result = formatter.render()
    assert "Actions Taken:" in result
    assert "Staged files" in result
    assert "Next Steps:" in result
    assert "Push to remote" in result


def test_build_functional_overview():
    """Test functional overview building."""
    title, content, entities = _build_functional_overview(
        features=["auth", "api"],
        summary="Added new features",
        entities=["User", "Auth"],
        files=["file1.py", "file2.py"],
        stats={"file1.py": (10, 5), "file2.py": (20, 0)},
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="feat: add features",
        project_types=["python"]
    )
    assert title == "Summary"
    assert "auth" in content or "api" in content
    assert "1.0.0" in content
    assert "1.1.0" in content


def test_build_functional_overview_single_feature():
    """Test with single feature."""
    title, content, entities = _build_functional_overview(
        features=["auth"],
        summary="",
        entities=[],
        files=["file.py"],
        stats={"file.py": (5, 0)},
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="feat: auth",
        project_types=["python"]
    )
    assert "auth support" in content


def test_build_functional_overview_no_features():
    """Test fallback when no features."""
    title, content, entities = _build_functional_overview(
        features=[],
        summary="",
        entities=[],
        files=["file.py"],
        stats={"file.py": (5, 0)},
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="chore: update",
        project_types=["python"]
    )
    assert title == "Overview"
    assert "Project Type:" in content


def test_determine_next_steps_success():
    """Test next steps for successful push."""
    steps = _determine_next_steps(None, 0, "1.1.0")
    assert any("Changes committed successfully" in s for s in steps)
    assert any("Version updated" in s for s in steps)


def test_determine_next_steps_test_failure():
    """Test next steps when tests fail."""
    steps = _determine_next_steps(None, 1, "1.1.0")
    assert any("Fix failing tests" in s for s in steps)
    assert any("pytest" in s or "Run tests manually" in s for s in steps)


def test_determine_next_steps_error():
    """Test next steps when there's an error."""
    steps = _determine_next_steps("Some error", 0, "1.1.0")
    assert any("Review the error" in s or "Check git status" in s for s in steps)


def test_format_status_output():
    """Test status output formatting."""
    result = format_status_output(
        version="1.0.0",
        branch="main",
        staged_files=["file1.py", "file2.py"],
        unstaged_files=["file3.py"]
    )
    assert "Goal Status" in result
    assert "1.0.0" in result
    assert "main" in result
    assert "file1.py" in result
    assert "file3.py" in result


def test_format_status_output_many_unstaged():
    """Test with many unstaged files."""
    files = [f"file{i}.py" for i in range(25)]
    result = format_status_output(
        version="1.0.0",
        branch="main",
        staged_files=[],
        unstaged_files=files
    )
    assert "and 5 more files" in result


def test_format_push_result():
    """Test push result formatting."""
    result = format_push_result(
        project_types=["python"],
        files=["main.py"],
        stats={"main.py": (10, 5)},
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="feat: update",
        actions=["Staged", "Committed"]
    )
    assert "Goal Push Result" in result
    assert "1.0.0" in result
    assert "1.1.0" in result
    assert "feat: update" in result


def test_format_push_result_with_error():
    """Test push result with error."""
    result = format_push_result(
        project_types=["python"],
        files=["main.py"],
        stats={"main.py": (10, 5)},
        current_version="1.0.0",
        new_version="1.1.0",
        commit_msg="feat: update",
        error="Something went wrong"
    )
    assert "Error" in result
    assert "Something went wrong" in result
