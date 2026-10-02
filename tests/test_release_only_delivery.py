"""Release-only policy applies independently of package metadata discovery."""
import json
from types import SimpleNamespace
from unittest.mock import patch

import click
import pytest

from goal.config import GoalConfig
from goal.cli.version_state import VersionDecision
from goal.push.core import _mirror_github_release, _recover_existing_generic_release_decision


def configuration(tmp_path, loaded):
    config = {"project": {"name": "standard"}, "publishing": {"enabled": False,
        "fallback": {"github_release": {"enabled": True, "owner": "example",
            "repo": "standard", "create_on_tag": True}}}}
    if loaded:
        path = tmp_path / "goal.yaml"
        path.write_text(json.dumps(config))
        return GoalConfig(str(path))
    return config


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize("success", [False, True])
def test_disabled_registry_mirrors_without_assets_and_retains_terminal_failure(tmp_path, loaded, success):
    config = configuration(tmp_path, loaded)
    with patch("goal.publish.github_fallback.try_github_release_on_tag", return_value=success) as mirror:
        def run():
            _mirror_github_release(tag_name="v1.0.0", effective_no_tag=False,
                delivery=SimpleNamespace(mode="direct-main"), project_types=["python"],
                new_version="1.0.0", publish_config=config)
        if success:
            run()
        else:
            with pytest.raises(click.ClickException, match="GitHub Release creation failed"):
                run()
    assert mirror.call_args.kwargs["artifacts"] == []
    assert mirror.call_args.kwargs["allow_empty_assets"] is True
    assert mirror.call_args.kwargs["package_name"] == "standard"


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize("valid_tag", [False, True])
def test_release_only_repair_still_requires_exact_annotated_tag(tmp_path, loaded, valid_tag):
    config = configuration(tmp_path, loaded)
    decision = VersionDecision(current_version="1.0.0", target_version="1.0.1",
        reason="normal-bump", sources=(), baseline_version="1.0.0",
        baseline_evidence=("git-tag:v1.0.0",), registry_versions=(),
        unavailable_registries=(), derived_paths=())
    with patch("goal.push.core.reuse_exact_annotated_tag", return_value="v1.0.0",
            side_effect=None if valid_tag else click.ClickException("tag is not at exact HEAD")) as reuse:
        def run():
            return _recover_existing_generic_release_decision("1.0.0", decision,
                clean_force_publish=True, delivery=SimpleNamespace(mode="direct-main"),
                project_types=["python"], publish_config=config)
        if valid_tag:
            resolved, repaired = run()
            assert repaired and resolved.target_version == "1.0.0"
            assert resolved.reason == "existing-tag-release-repair"
        else:
            with pytest.raises(click.ClickException, match="exact HEAD"):
                run()
    reuse.assert_called_once_with("1.0.0")
