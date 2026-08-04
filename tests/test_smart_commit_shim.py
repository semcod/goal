"""Tests for goal/smart_commit.py shim."""


def test_shim_imports():
    """Test that smart_commit shim properly exports classes."""
    from goal import smart_commit

    assert hasattr(smart_commit, "CodeAbstraction")
    assert hasattr(smart_commit, "SmartCommitGenerator")
    assert hasattr(smart_commit, "create_smart_generator")


def test_all_exports():
    """Test __all__ exports are importable."""
    from goal.smart_commit import (
        CodeAbstraction,
        SmartCommitGenerator,
        create_smart_generator,
    )

    assert CodeAbstraction is not None
    assert SmartCommitGenerator is not None
    assert create_smart_generator is not None
