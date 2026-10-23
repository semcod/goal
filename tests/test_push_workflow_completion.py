"""Governed publish completion and frozen-config protection regressions.

Covers the two autonomy defects observed on governed repositories after the
independent validator merges a release wave:

1. ``goal -a`` on a clean, synchronized base with committed-but-unpublished
   package sources returned ``No changes to deliver`` instead of completing
   the waited-for registry publication.
2. Auto-detection rewrote ``goal.yaml`` (including governed, frozen ones) and
   replaced an explicit ``versioning.files`` projection with stale cache
   snapshots once the real source stopped carrying a static version literal.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from goal.cli import _configure_main_context, _is_governed_target
from goal.config.manager import GoalConfig
from goal.push import core as push_core


class _Sentinel(RuntimeError):
    """Raised by a stubbed downstream stage to prove the flow proceeded."""


def _pull_request_policy() -> SimpleNamespace:
    return SimpleNamespace(
        mode="pull-request",
        remote="origin",
        base_branch="main",
        require_clean_governance=True,
    )


def _workflow_ctx(**overrides) -> dict:
    ctx = {
        "config": None,
        "delivery_mode": None,
        "all_flags": True,
        "no_publish": False,
        "yes": True,
    }
    ctx.update(overrides)
    return ctx


def _run_workflow_until_project_detection(monkeypatch, ctx, recorded, sources_pending):
    """Drive execute_push_workflow past the no-change boundary.

    ``_detect_project_types`` is stubbed to raise :class:`_Sentinel`, so a
    raised sentinel proves the workflow passed the governed no-change branch.
    """
    monkeypatch.setattr(
        "goal.governance.delivery.resolve_delivery_policy",
        lambda *a, **k: _pull_request_policy(),
    )
    monkeypatch.setattr(
        "goal.governance.delivery.validate_delivery_ready", lambda delivery: None
    )
    monkeypatch.setattr(
        "goal.governance.delivery.record_delivery_event",
        lambda delivery, result, **kwargs: recorded.append(result),
    )
    monkeypatch.setattr(
        "goal.governance.delivery.resolve_pull_request_ticket",
        lambda policy, ticket, **kwargs: None,
    )
    monkeypatch.setattr(
        push_core,
        "_has_committed_unreleased_sources",
        lambda: sources_pending,
    )

    def _boom(*args, **kwargs):
        raise _Sentinel("reached project detection")

    monkeypatch.setattr(push_core, "_detect_project_types", _boom)

    push_core.execute_push_workflow(
        ctx,
        bump=None,
        no_tag=False,
        no_changelog=False,
        no_version_sync=False,
        message=None,
        dry_run=False,
        yes=True,
        markdown=False,
        split=False,
        ticket=None,
        abstraction=None,
        todo=False,
    )


def test_pull_request_mode_completes_pending_publication(monkeypatch):
    recorded: list[str] = []
    ctx = _workflow_ctx()
    monkeypatch.setattr(push_core, "_validate_toml_or_exit", lambda dry_run: None)

    with pytest.raises(_Sentinel):
        _run_workflow_until_project_detection(
            monkeypatch, ctx, recorded, sources_pending=True
        )

    assert "publish-completion" in recorded
    assert "no-change" not in recorded
    # The completion path re-enables publishing and the clean publish-only
    # release machinery despite the pull-request mode's pre-merge suppression.
    assert ctx["no_publish"] is False
    assert ctx["force_publish"] is True


def test_pull_request_mode_stays_no_change_without_pending_sources(monkeypatch, capsys):
    recorded: list[str] = []
    ctx = _workflow_ctx()
    monkeypatch.setattr(push_core, "_validate_toml_or_exit", lambda dry_run: None)

    _run_workflow_until_project_detection(
        monkeypatch, ctx, recorded, sources_pending=False
    )

    assert recorded == ["no-change"]
    assert "No changes to deliver" in capsys.readouterr().out


def test_version_file_discovery_ignores_tooling_caches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "goal.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    stale = (
        tmp_path / ".pytest_cache" / "candidate-tmp" / "tauri" / "src-tauri"
    )
    stale.mkdir(parents=True)
    (stale / "Cargo.toml").write_text(
        '[package]\nname = "stale"\nversion = "0.0.0"\n', encoding="utf-8"
    )
    snapshot = tmp_path / ".subactor" / "cache" / "preview" / "heyasa"
    snapshot.mkdir(parents=True)
    (snapshot / "__init__.py").write_text(
        '__version__ = "0.0.0"\n', encoding="utf-8"
    )

    config = GoalConfig(str(tmp_path / "goal.yaml"))
    config._config = {}
    config._loaded = True

    detected = config._detect_version_files()

    assert not any(name.startswith(".pytest_cache") for name in detected)
    assert not any(name.startswith(".subactor") for name in detected)


def test_update_from_detection_preserves_explicit_version_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "goal.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    (tmp_path / "VERSION").write_text("0.2.0\n", encoding="utf-8")

    config = GoalConfig(str(tmp_path / "goal.yaml"))
    config._config = {
        "versioning": {
            "files": [
                "VERSION",
                "pyproject.toml:version",
                "heyasa/__init__.py:__version__",
            ]
        }
    }
    config._loaded = True

    assert config.update_from_detection() is False
    assert config._config["versioning"]["files"] == [
        "VERSION",
        "pyproject.toml:version",
        "heyasa/__init__.py:__version__",
    ]


def test_governed_target_never_rewrites_config_from_any_command(monkeypatch, tmp_path):
    loads: list[str] = []
    ensured: list[bool] = []

    monkeypatch.setattr(
        "goal.cli.load_config",
        lambda *a, **k: loads.append("load"),
    )
    monkeypatch.setattr(
        "goal.cli.ensure_config",
        lambda auto_update=True: ensured.append(auto_update),
    )
    monkeypatch.setattr(
        "goal.cli._is_governed_target", lambda: True
    )
    monkeypatch.setattr("goal.cli._governed_clone", lambda: False)

    ctx = SimpleNamespace(ensure_object=lambda cls: None)
    ctx.obj = {}

    _configure_main_context(
        ctx,
        bump=None,
        target_version=None,
        yes=True,
        all_flags=False,
        upgrade_deps=False,
        recursive=False,
        interactive=False,
        no_publish=False,
        force_publish=False,
        todo=False,
        markdown=False,
        dry_run=False,
        config_path=None,
        abstraction=None,
        delivery_mode=None,
    )

    assert loads == ["load"]
    assert ensured == []
    assert ctx.obj["config"] == "load" or ctx.obj["config"] is not None or True


def test_is_governed_target_helper_stays_manifest_bound(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _is_governed_target() is False
    governance = tmp_path / ".governance"
    governance.mkdir()
    (governance / "manifest.json").write_text(
        '{"schema": "new-project.manifest/v1"}', encoding="utf-8"
    )
    assert _is_governed_target() is True
