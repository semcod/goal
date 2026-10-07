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
            ctx = configure()
    assert config.exists() is existing
    if existing:
        assert config.read_text() == original
    assert ctx.obj["force_publish"] is True


def test_explicit_no_publish_remains_an_opt_out(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch.object(cli, "ensure_config", return_value=object()):
        with patch.object(cli, "get_user_config", return_value=None):
            ctx = click.Context(click.Command("goal"))
            cli._configure_main_context(
                ctx,
                bump="patch",
                target_version=None,
                yes=False,
                all_flags=True,
                upgrade_deps=False,
                recursive=False,
                interactive=False,
                no_publish=True,
                force_publish=False,
                todo=False,
                markdown=False,
                dry_run=False,
                config_path=None,
                abstraction=False,
                delivery_mode=None,
            )
    assert ctx.obj["force_publish"] is True
    assert ctx.obj["no_publish"] is True


def test_ungoverned_all_flags_keeps_bootstrap(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch.object(cli, "ensure_config", return_value=object()) as bootstrap:
        with patch.object(cli, "get_user_config", return_value=None):
            configure()
    bootstrap.assert_called_once_with()
    assert not Path(".governance").exists()


@pytest.mark.parametrize("mode", ["pull-request", "publish-only"])
@pytest.mark.parametrize("previous", [None, "retained"])
def test_governed_bootstrap_restores_markers_after_failure(monkeypatch, mode, previous):
    from goal.push import core
    for key in ["GOAL_SKIP_COSTS_BADGE", "GOAL_BOOTSTRAP_READ_ONLY"]:
        if previous is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, previous)

    def bootstrap(*args):
        import os
        assert os.environ["GOAL_BOOTSTRAP_READ_ONLY"] == "1"
        assert os.environ["GOAL_SKIP_COSTS_BADGE"] == "1"
        raise RuntimeError("installer failure")

    monkeypatch.setattr(core, "_bootstrap_projects", bootstrap)
    with pytest.raises(RuntimeError, match="installer failure"):
        core._bootstrap_projects_for_delivery(["python"], False, True, mode)
    import os
    for key in ["GOAL_SKIP_COSTS_BADGE", "GOAL_BOOTSTRAP_READ_ONLY"]:
        assert os.environ.get(key) == previous
