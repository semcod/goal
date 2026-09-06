from pathlib import Path
from unittest.mock import patch

import click
import pytest

import goal.cli as cli


def configure():
    ctx = click.Context(click.Command("goal"))
    cli._configure_main_context(
        ctx, bump="patch", target_version=None, yes=False, all_flags=True,
        upgrade_deps=False, recursive=False, interactive=False, no_publish=False,
        force_publish=False, todo=False, markdown=False, dry_run=False,
        config_path=None, abstraction=False, delivery_mode=None,
    )
    return ctx


@pytest.mark.parametrize("existing", [False, True])
def test_governed_all_flags_preserves_configuration(tmp_path, monkeypatch, existing):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".governance").mkdir()
    (tmp_path / ".governance/manifest.json").write_text("{}")
    config = tmp_path / "goal.yaml"
    original = "project:\n  name: retained\n"
    if existing:
        config.write_text(original)
    with patch.object(cli, "ensure_config", side_effect=AssertionError("premature write")):
        with patch.object(cli, "get_user_config", return_value=None):
            configure()
    assert config.exists() is existing
    if existing:
        assert config.read_text() == original


def test_ungoverned_all_flags_keeps_bootstrap(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch.object(cli, "ensure_config", return_value=object()) as bootstrap:
        with patch.object(cli, "get_user_config", return_value=None):
            configure()
    bootstrap.assert_called_once_with()
    assert not Path(".governance").exists()
