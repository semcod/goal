"""Tests for goal/config.py shim."""


def test_config_shim_exports():
    """Test that config shim properly exports functions."""
    from goal import config

    assert hasattr(config, "GoalConfig")
    assert hasattr(config, "init_config")
    assert hasattr(config, "load_config")
    assert hasattr(config, "ensure_config")
    assert hasattr(config, "DEFAULT_CONFIG")


def test_all_exports():
    """Test __all__ exports are importable."""
    from goal.config import (
        GoalConfig,
        init_config,
        load_config,
        ensure_config,
        DEFAULT_CONFIG,
    )

    assert GoalConfig is not None
    assert init_config is not None
    assert load_config is not None
    assert ensure_config is not None
    assert DEFAULT_CONFIG is not None
