"""Publication failures must be visible to scheduler and shell callers."""
import importlib
from unittest.mock import Mock

import click
import pytest

publish_cmd = importlib.import_module("goal.cli.publish_cmd")


@pytest.mark.parametrize("make_failure", [False, True])
def test_failed_upload_raises_nonzero_error(monkeypatch, make_failure):
    monkeypatch.setattr(publish_cmd, "detect_project_types", lambda: ["python"])
    monkeypatch.setattr(publish_cmd.shutil, "which", lambda name: "/usr/bin/make")
    monkeypatch.setattr(publish_cmd, "makefile_has_target", lambda name: make_failure)
    monkeypatch.setattr(publish_cmd, "run_command_tee", Mock(return_value=Mock(returncode=1)))
    upload = Mock(return_value=False)
    monkeypatch.setattr(publish_cmd, "publish_project", upload)
    with pytest.raises(click.ClickException, match="Publish failed"):
        publish_cmd._publish_impl({}, make_failure, "publish", "1.2.3")
    upload.assert_called_once()


def test_successful_upload_returns_normally(monkeypatch):
    monkeypatch.setattr(publish_cmd, "detect_project_types", lambda: ["python"])
    monkeypatch.setattr(publish_cmd, "publish_project", Mock(return_value=True))
    publish_cmd._publish_impl({}, False, "publish", "1.2.3")


def test_publish_dry_run_does_not_upload(monkeypatch):
    upload = Mock()
    monkeypatch.setattr(publish_cmd, "detect_project_types", lambda: ["python"])
    monkeypatch.setattr(publish_cmd, "publish_project", upload)
    publish_cmd._publish_impl({"dry_run": True}, False, "publish", "1.2.3")
    upload.assert_not_called()
