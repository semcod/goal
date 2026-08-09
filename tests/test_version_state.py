import json
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from goal.cli.version_state import (
    VersionStateError,
    collect_version_sources,
    resolve_version_decision,
    validate_version_sources,
)


def _git(tmp_path: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)


def _init_release(tmp_path: Path, version: str, *, tag: bool = True) -> dict:
    (tmp_path / "VERSION").write_text(f"{version}\n")
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "fixture"\nversion = "{version}"\n'
    )
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.name", "Goal Test")
    _git(tmp_path, "config", "user.email", "goal-test@example.invalid")
    _git(tmp_path, "add", "VERSION", "pyproject.toml")
    _git(tmp_path, "commit", "-m", "initial release")
    if tag:
        _git(tmp_path, "tag", f"v{version}")
    return {
        "versioning": {
            "files": ["VERSION", "pyproject.toml:version"],
        }
    }


def test_normal_bump_uses_released_baseline(tmp_path, monkeypatch):
    config = _init_release(tmp_path, "1.2.3")
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(config=config, registry_versions={})

    assert decision.current_version == "1.2.3"
    assert decision.target_version == "1.2.4"
    assert decision.reason == "normal-bump"


def test_complete_local_prebump_is_not_bumped_twice(tmp_path, monkeypatch):
    config = _init_release(tmp_path, "1.2.3")
    (tmp_path / "VERSION").write_text("1.2.4\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.4"\n'
    )
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(config=config, registry_versions={})

    assert decision.current_version == "1.2.3"
    assert decision.target_version == "1.2.4"
    assert decision.reason == "already-bumped"
    assert decision.stale_sources == ()


def test_partial_local_prebump_repairs_forward(tmp_path, monkeypatch):
    config = _init_release(tmp_path, "1.2.3")
    (tmp_path / "VERSION").write_text("1.2.4\n")
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(config=config, registry_versions={})

    assert decision.target_version == "1.2.4"
    assert decision.reason == "partial-bump"
    assert [source.spec for source in decision.stale_sources] == [
        "pyproject.toml:version"
    ]


def test_conflicting_forward_candidates_are_rejected(tmp_path, monkeypatch):
    config = _init_release(tmp_path, "1.2.3")
    (tmp_path / "VERSION").write_text("1.2.4\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.5"\n'
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(VersionStateError, match="Multiple forward"):
        resolve_version_decision(config=config, registry_versions={})


def test_registry_ahead_of_local_state_is_rejected(tmp_path, monkeypatch):
    config = _init_release(tmp_path, "1.2.3", tag=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(VersionStateError, match="regresses behind"):
        resolve_version_decision(
            config=config,
            registry_versions={"pypi:fixture": "1.2.4"},
        )


def test_released_partial_state_is_repaired_without_another_release(
    tmp_path, monkeypatch
):
    config = _init_release(tmp_path, "1.2.4")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.3"\n'
    )
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(
        config=config,
        registry_versions={"pypi:fixture": "1.2.4"},
        release_required=False,
    )

    assert decision.current_version == "1.2.4"
    assert decision.target_version == "1.2.4"
    assert decision.reason == "released-partial-repair"
    assert [source.spec for source in decision.stale_sources] == [
        "pyproject.toml:version"
    ]


def test_released_partial_state_advances_when_package_changes_need_release(
    tmp_path, monkeypatch
):
    config = _init_release(tmp_path, "1.2.4")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.3"\n'
    )
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(
        config=config,
        registry_versions={"pypi:fixture": "1.2.4"},
        release_required=True,
    )

    assert decision.current_version == "1.2.4"
    assert decision.target_version == "1.2.5"
    assert decision.reason == "normal-bump-with-repair"


def test_explicit_target_repairs_stale_sources_without_extra_bump(
    tmp_path, monkeypatch
):
    config = _init_release(tmp_path, "1.2.3")
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(
        config=config,
        target_version="1.3.0",
        bump="patch",
        registry_versions={},
    )

    assert decision.target_version == "1.3.0"
    assert decision.reason == "explicit-target"
    assert {source.spec for source in decision.stale_sources} == {
        "VERSION",
        "pyproject.toml:version",
    }


def test_multiline_version_contract_is_reported_but_not_managed(
    tmp_path, monkeypatch
):
    (tmp_path / "VERSION").write_text(
        "FORMAT=example.integrity/v1\nARTIFACT=fixture\n"
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "fixture", "version": "2.0.0"}) + "\n"
    )
    monkeypatch.chdir(tmp_path)
    config = {
        "versioning": {"files": ["VERSION", "package.json:version"]}
    }

    decision = resolve_version_decision(config=config, registry_versions={})

    contract = next(source for source in decision.sources if source.spec == "VERSION")
    assert contract.contract is True
    assert "VERSION" not in decision.managed_specs
    assert decision.current_version == "2.0.0"


def test_inferred_lockstep_package_is_managed_but_independent_package_is_not(
    tmp_path, monkeypatch
):
    config = _init_release(tmp_path, "1.2.3")
    lockstep = tmp_path / "packages" / "lockstep"
    independent = tmp_path / "packages" / "independent"
    lockstep.mkdir(parents=True)
    independent.mkdir(parents=True)
    (lockstep / "pyproject.toml").write_text(
        '[project]\nname = "lockstep"\nversion = "1.2.3"\n'
    )
    (independent / "pyproject.toml").write_text(
        '[project]\nname = "independent"\nversion = "9.0.0"\n'
    )
    monkeypatch.chdir(tmp_path)

    sources = collect_version_sources(config, "1.2.3")
    specs = {source.spec for source in sources}

    assert "packages/lockstep/pyproject.toml:version" in specs
    assert "packages/independent/pyproject.toml:version" not in specs


def test_git_history_detects_uncommitted_prebump_without_release_tag(
    tmp_path, monkeypatch
):
    config = _init_release(tmp_path, "1.2.3", tag=False)
    (tmp_path / "VERSION").write_text("1.2.4\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.4"\n'
    )
    monkeypatch.chdir(tmp_path)

    decision = resolve_version_decision(config=config, registry_versions={})

    assert decision.baseline_version == "1.2.3"
    assert decision.reason == "already-bumped"
    assert decision.target_version == "1.2.4"


def test_strict_validation_lists_every_stale_source(tmp_path, monkeypatch):
    (tmp_path / "VERSION").write_text("1.0.0\n")
    (tmp_path / "package.json").write_text(
        '{"name": "fixture", "version": "1.0.1"}\n'
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(VersionStateError) as error:
        validate_version_sources(
            ["VERSION", "package.json:version"], "1.0.2"
        )

    message = str(error.value)
    assert "VERSION: expected 1.0.2, found 1.0.0" in message
    assert "package.json:version: expected 1.0.2, found 1.0.1" in message


def test_imported_version_name_is_not_detected_as_a_declaration(
    tmp_path, monkeypatch
):
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text(
        "from package.metadata import __version__\n"
    )
    (tmp_path / "VERSION").write_text("1.0.0\n")
    monkeypatch.chdir(tmp_path)

    sources = collect_version_sources({"versioning": {"files": ["VERSION"]}})

    assert {source.spec for source in sources} == {"VERSION"}


def test_registry_failure_does_not_disable_local_git_decision(
    tmp_path, monkeypatch
):
    config = _init_release(tmp_path, "1.2.3")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "goal.version_validation.validate_project_versions",
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("offline")),
    )

    decision = resolve_version_decision(config=config, project_types=["python"])

    assert decision.target_version == "1.2.4"
    assert decision.reason == "normal-bump"
    assert decision.unavailable_registries == ("python",)


def _registry_result(version: str) -> dict:
    return {
        "python": {
            "registry": "pypi",
            "package_name": "fixture",
            "registry_version": version,
            "local_version": version,
            "is_latest": True,
            "error": None,
        }
    }


def test_check_versions_explains_complete_prebump(
    tmp_path, monkeypatch
):
    from goal.cli import utils_cmd

    config = _init_release(tmp_path, "1.2.3")
    (tmp_path / "VERSION").write_text("1.2.4\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "1.2.4"\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        utils_cmd, "validate_project_versions", lambda *args: _registry_result("1.2.3")
    )

    result = CliRunner().invoke(
        utils_cmd.check_versions,
        [],
        obj={"config": config, "bump": "patch", "version": None},
    )

    assert result.exit_code == 0, result.output
    assert "Version decision: already-bumped -> 1.2.4" in result.output


def test_check_versions_fails_and_explains_partial_prebump(
    tmp_path, monkeypatch
):
    from goal.cli import utils_cmd

    config = _init_release(tmp_path, "1.2.3")
    (tmp_path / "VERSION").write_text("1.2.4\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        utils_cmd, "validate_project_versions", lambda *args: _registry_result("1.2.3")
    )

    result = CliRunner().invoke(
        utils_cmd.check_versions,
        [],
        obj={"config": config, "bump": "patch", "version": None},
    )

    assert result.exit_code == 1
    assert "Version decision: partial-bump -> 1.2.4" in result.output
    assert "pyproject.toml:version" in result.output
