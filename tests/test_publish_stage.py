"""Registry configuration applies before package effects in managed releases."""

import json

import pytest

from goal.config import GoalConfig
from goal.publish.github_fallback import get_github_release_config
from goal.push.stages import publish as stage


@pytest.mark.parametrize("force_publish", [False, True])
@pytest.mark.parametrize("loaded_config", [False, True])
def test_disabled_registry_has_no_package_effects(
    monkeypatch, tmp_path, force_publish, loaded_config
):
    config = {
        "publishing": {
            "enabled": False,
            "registries": [],
            "fallback": {
                "github_release": {
                    "enabled": True,
                    "owner": "example",
                    "repo": "standard",
                    "create_on_tag": True,
                }
            },
        }
    }
    if loaded_config:
        path = tmp_path / "goal.yaml"
        path.write_text(json.dumps(config))
        config = GoalConfig(str(path))

    def forbidden(*args, **kwargs):
        pytest.fail("Disabled registry must not analyze, build or publish packages")

    monkeypatch.setattr(stage, "analyze_publishable_changes", forbidden)
    monkeypatch.setattr(stage, "publish_project", forbidden)
    assert stage.handle_publish(
        ["python"], "0.20.55", True, config=config,
        staged_files=[], force_publish=force_publish,
    ) == (True, None)
    github = get_github_release_config(config)
    assert github.enabled and github.create_on_tag
    assert (github.owner, github.repo) == ("example", "standard")


@pytest.mark.parametrize("config", [None, {}, {"publishing": {"enabled": True}}])
def test_enabled_or_default_registry_still_publishes(monkeypatch, config):
    calls = []
    monkeypatch.setattr(
        stage, "publish_project",
        lambda *args, **kwargs: calls.append((args, kwargs)) or True,
    )
    assert stage.handle_publish(
        ["python"], "1.0.0", True, config=config, force_publish=True,
    ) == (True, None)
    assert calls == [((["python"], "1.0.0", True), {"config": config})]


def test_no_publish_flag_retains_precedence(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("--no-publish must not invoke registry effects")

    monkeypatch.setattr(stage, "publish_project", forbidden)
    assert stage.handle_publish(
        ["python"], "1.0.0", True, no_publish=True,
        config={"publishing": {"enabled": False}}, force_publish=True,
    ) == (False, None)
