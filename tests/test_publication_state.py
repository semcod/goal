"""A monitor must distinguish registry absence from uncertainty and integrity."""

from datetime import datetime, timezone
from email.message import Message
from http.client import IncompleteRead
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError, URLError

import pytest

from goal.publish import state
from goal.version_validation import exact_version_published


TARGET = state.ReleaseTarget("pypi", "Example_Pkg", "1.0rc1+local.2")
SHA = "a" * 64
NOW = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def document(**changes):
    return {
        "info": {"name": "example.pkg", "version": TARGET.version},
        "urls": [{"filename": "example_pkg-1.0rc1.whl", "digests": {"sha256": SHA}, "yanked": False}],
        **changes,
    }


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, url=TARGET.url):
        super().__init__(data if isinstance(data, bytes) else json.dumps(data).encode())
        self.url = url

    def geturl(self):
        return self.url


def observe(data=None, **kwargs):
    return state.observe_release(TARGET, opener=lambda url, timeout: Response(document() if data is None else data), now=NOW, **kwargs)


def fail(error):
    def opener(url, timeout):
        raise error
    return opener


@pytest.mark.parametrize("registry,base", [
    ("pypi", "https://pypi.org"),
    ("PyPI", "https://pypi.org"),
    ("https://pypi.org/simple/", "https://pypi.org"),
    ("testpypi", "https://test.pypi.org"),
    ("https://test.pypi.org/simple/", "https://test.pypi.org"),
])
def test_exact_target_preserves_registry_and_encodes_prerelease(registry, base):
    target = state.ReleaseTarget(registry, "Example_Pkg", TARGET.version)
    assert target.package == "example-pkg"
    assert target.url == f"{base}/pypi/example-pkg/1.0rc1%2Blocal.2/json"


@pytest.mark.parametrize("registry,name,version", [
    ("https://private.example/simple/", "x", "1"),
    ("https://pypi.org@evil.example", "x", "1"),
    ("http://pypi.org", "x", "1"),
    ("pypi", "../x", "1"),
    ("pypi", "-x", "1"),
    ("pypi", "x", "../1"),
    ("pypi", "x", ""),
])
def test_unsupported_or_unsafe_targets_never_make_requests(registry, name, version):
    with pytest.raises(ValueError):
        state.ReleaseTarget(registry, name, version)


@pytest.mark.parametrize("code,expected", [(404, "missing"), (401, "unknown"), (403, "unknown"), (429, "unknown"), (500, "unknown"), (503, "unknown")])
def test_http_statuses_do_not_turn_outages_into_absence(code, expected):
    result = state.observe_release(TARGET, opener=fail(HTTPError(TARGET.url, code, "error", {}, None)), now=NOW)
    assert result.state == expected
    assert result.http_status == code
    assert not result.verified


@pytest.mark.parametrize("header,deadline", [
    ("120", "2026-10-31T12:02:00+00:00"),
    ("Sat, 31 Oct 2026 12:03:00 GMT", "2026-10-31T12:03:00+00:00"),
    ("Sat, 31 Oct 2026 11:00:00 GMT", NOW.isoformat()),
    ("nonsense", None),
])
def test_throttling_preserves_retry_after_without_retrying(header, deadline):
    headers = Message()
    headers["Retry-After"] = header
    calls = []

    def opener(url, timeout):
        calls.append(url)
        raise HTTPError(url, 429, "throttled", headers, None)

    result = state.observe_release(TARGET, opener=opener, now=NOW)
    assert result.state == "unknown"
    assert result.retry_not_before == deadline
    assert calls == [TARGET.url]


@pytest.mark.parametrize("error", [TimeoutError(), URLError("offline"), ConnectionResetError(), IncompleteRead(b"{")])
def test_network_failure_is_unknown(error):
    assert state.observe_release(TARGET, opener=fail(error)).state == "unknown"


@pytest.mark.parametrize("data", [
    b"<html>error</html>", b"\xff", [], None,
    document(info={"name": "other", "version": TARGET.version}),
    document(info={"name": "example-pkg", "version": "2.0"}),
    document(urls=[]), document(urls={}),
    document(urls=[{"filename": "x"}]),
    document(urls=[{"filename": "../x", "digests": {"sha256": SHA}, "yanked": False}]),
    document(urls=[{"filename": "x", "digests": {"sha256": "bad"}, "yanked": False}]),
    document(urls=[{"filename": "x", "digests": {"sha256": SHA}, "yanked": "false"}]),
    document(urls=document()["urls"] * 2),
])
def test_malformed_empty_or_wrong_release_cannot_mean_missing_or_verified(data):
    result = state.observe_release(TARGET, opener=lambda url, timeout: Response(data))
    assert result.state == "unknown"
    assert not result.verified


@pytest.mark.parametrize("url", ["https://mirror.example/x", "http://pypi.org/pypi/x/json"])
def test_unexpected_redirect_is_unknown_including_redirected_404(url):
    assert state.observe_release(TARGET, opener=lambda *a, **k: Response(document(), url)).state == "unknown"
    assert state.observe_release(TARGET, opener=fail(HTTPError(url, 404, "not found", {}, None))).state == "unknown"


def test_response_size_is_bounded():
    result = observe(b" " * (state._MAX_DOCUMENT_BYTES + 1))
    assert result.state == "unknown"
    assert result.reason == "response_too_large"


def test_presence_is_distinct_from_verified_local_artifacts():
    assert observe().state == "present"
    assert not observe().verified
    expected = {"example_pkg-1.0rc1.whl": SHA}
    assert observe(expected_artifacts=expected).verified
    mismatch = observe(expected_artifacts={"example_pkg-1.0rc1.whl": "b" * 64})
    assert mismatch.state == "present" and mismatch.verification == "mismatch"
    assert not mismatch.verified
    incomplete = observe(expected_artifacts={"other.whl": SHA})
    assert incomplete.state == "present" and incomplete.verification == "incomplete"


def test_yanked_artifact_cannot_verify_even_when_hash_matches():
    data = document()
    data["urls"][0]["yanked"] = True
    result = observe(data, expected_artifacts={"example_pkg-1.0rc1.whl": SHA})
    assert result.state == "present" and not result.verified


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_timeout_fails_before_network(timeout):
    with pytest.raises(ValueError):
        observe(timeout=timeout)


def test_empty_expected_set_cannot_vacuously_verify():
    with pytest.raises(ValueError):
        observe(expected_artifacts={})


def test_compatibility_adapter_uses_same_typed_observation(monkeypatch):
    monkeypatch.setattr(state, "urlopen", lambda url, timeout: Response(document()))
    assert exact_version_published("pypi", "example-pkg", TARGET.version)
    monkeypatch.setattr(state, "urlopen", fail(TimeoutError()))
    assert not exact_version_published("pypi", "example-pkg", TARGET.version)
    assert not exact_version_published("private", "example-pkg", TARGET.version)


def test_cli_json_reports_failed_artifact_verification_nonzero(tmp_path, monkeypatch, capsys):
    artifact = tmp_path / "different.whl"
    artifact.write_bytes(b"build")
    monkeypatch.setattr(state, "urlopen", lambda url, timeout: Response(document()))
    assert state.main(["--registry", "pypi", "--package", TARGET.package, "--version", TARGET.version, "--artifact", str(artifact)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "present" and not result["verified"]
    assert result["verification"] == "incomplete"


def test_module_entrypoint_is_json_and_does_not_bootstrap_or_write(tmp_path):
    environment = {**os.environ, "PYTHONPATH": str(Path(state.__file__).resolve().parents[2])}
    result = subprocess.run([sys.executable, "-m", "goal.publish.state", "--registry", "private", "--package", "x", "--version", "1"], cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert result.returncode == 2, result.stderr
    assert json.loads(result.stdout)["state"] == "unknown"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("code,expected", [(404, "missing"), (403, "unknown"), (429, "unknown")])
def test_package_existence_preserves_authoritative_absence_and_throttling(code, expected):
    headers = Message()
    headers["Retry-After"] = "120"
    calls = []

    def opener(url, timeout):
        calls.append(url)
        raise HTTPError(url, code, "refused", headers, None)

    result = state.observe_package(TARGET, opener=opener, now=NOW)
    assert result.state == expected and result.latest_version is None
    assert result.retry_not_before == "2026-10-31T12:02:00+00:00"
    assert calls == ["https://pypi.org/pypi/example-pkg/json"]


def test_package_document_reports_its_latest_version_without_confusing_target():
    data = document(info={"name": "example_pkg", "version": "9.0.0"})
    observed = state.observe_package(TARGET, opener=lambda *a, **k: Response(data))
    assert observed.state == "present" and observed.latest_version == "9.0.0"


@pytest.fixture
def release_project(tmp_path, monkeypatch):
    import yaml

    config = {"publishing": {"enabled": True, "registries": ["pypi"]},
              "versioning": {"files": ["pyproject.toml:version"]},
              "governance": {"delivery": {"default_mode": "pull-request", "base_branch": "main",
                                         "remote": "origin", "require_goal_a": True,
                                         "require_clean_governance": True}}}
    (tmp_path / "pyproject.toml").write_text('[project]\nname="example-pkg"\nversion="4.3.2"\n')
    (tmp_path / "goal.yaml").write_text(yaml.safe_dump(config))
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()
    git("init", "-q", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-qm", "fixture")
    git("remote", "add", "origin", "https://fixture-secret@github.com/example/release.git?key=private")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(state, "observe_package", lambda target, **kwargs: state.PackageObservation(
        target.registry, target.package, "missing", None, "not_found", NOW.isoformat(), 404))
    return config, git


def test_project_plan_binds_source_and_initial_version_without_effects(release_project, tmp_path):
    config, git = release_project
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    planned = state.plan_current_project(config, require_config=True)
    assert planned.pending and planned.initial_release and planned.ready_for_goal
    assert planned.version == "4.3.2" and planned.source_head == git("rev-parse", "HEAD")
    assert planned.repository == "github.com/example/release"
    wire = planned.to_dict()
    assert wire["authorization_granted"] is False and wire["source_publication_verified"] is False
    assert "fixture-secret" not in json.dumps(wire) and "private" not in json.dumps(wire)
    assert {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("condition", ["dirty", "ticket_branch", "stale_tracking"])
def test_pending_plan_does_not_grant_execution_on_unready_sources(release_project, tmp_path, condition):
    config, git = release_project
    if condition == "dirty":
        (tmp_path / "changed.py").write_text("change\n")
    elif condition == "ticket_branch":
        git("checkout", "-qb", "ticket/001-fixture")
    else:
        (tmp_path / "README.md").write_text("new head\n")
        git("add", ".")
        git("commit", "-qm", "new head")
    plan = state.plan_current_project(config)
    assert plan.pending and not plan.ready_for_goal


def test_project_plan_never_runs_a_repository_fsmonitor(release_project, tmp_path):
    config, git = release_project
    marker = tmp_path / "ran-fsmonitor"
    hook = tmp_path / ".git/fsmonitor-fixture"
    hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
    hook.chmod(0o700)
    git("config", "core.fsmonitor", str(hook))
    assert state.plan_current_project(config).pending
    assert not marker.exists()


@pytest.mark.parametrize("mode", ["outage", "present", "missing"])
def test_project_registry_readiness_uses_exact_and_package_observations(release_project, monkeypatch, mode):
    config, _ = release_project
    monkeypatch.setattr(state, "observe_package", lambda target, **kwargs: state.PackageObservation(
        target.registry, target.package, "unknown" if mode == "outage" else "present",
        None if mode == "outage" else "4.3.1", "fixture", NOW.isoformat()))
    monkeypatch.setattr(state, "observe_release", lambda target, **kwargs: state.PublicationObservation(
        target, "present" if mode == "present" else "missing", "fixture", NOW.isoformat()))
    planned = state.plan_current_project(config)
    assert planned.pending is (mode == "missing")
    assert not planned.initial_release
    if mode == "outage":
        assert planned.reason == "registry_unknown"


@pytest.mark.parametrize("condition", ["disabled", "private", "mixed", "multiple_registries", "version_drift"])
def test_unconfigured_or_unsupported_project_is_not_queried(release_project, tmp_path, monkeypatch, condition):
    config, _ = release_project
    if condition == "disabled":
        config["publishing"]["enabled"] = False
    elif condition == "private":
        config["registries"] = {"pypi": {"url": "https://credential@private.example/simple/"}}
    elif condition == "mixed":
        (tmp_path / "Cargo.toml").write_text("[package]\n")
    elif condition == "multiple_registries":
        config["publishing"]["registries"] = ["pypi", "private"]
    else:
        (tmp_path / "VERSION").write_text("4.3.1\n")
        config["versioning"]["files"].append("VERSION")
    monkeypatch.setattr(state, "observe_package", lambda *a, **k: pytest.fail("must not query"))
    assert not state.plan_current_project(config).pending


def test_project_cli_is_read_only_without_configuration(tmp_path, capsys):
    previous = Path.cwd()
    assert state.main(["--project", str(tmp_path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema"] == "goal.release-plan/v1" and not data["ready_for_goal"]
    assert data["reason"] == "publishing_not_configured"
    assert list(tmp_path.iterdir()) == [] and Path.cwd() == previous


def test_malformed_project_yaml_does_not_expose_its_content(tmp_path, capsys):
    (tmp_path / "goal.yaml").write_text('secret: sensitive-fixture\npublishing: [invalid\n')
    assert state.main(["--project", str(tmp_path)]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["reason"] == "project_plan_unavailable"
    assert "sensitive-fixture" not in output.out and output.err == ""


@pytest.mark.parametrize("mode", ["diverged", "matched", "unknown"])
def test_opt_in_source_comparison_is_reconciliation_only(release_project, tmp_path, monkeypatch, capsys, mode):
    from goal.publish import source
    config, git = release_project
    head = git("rev-parse", "HEAD")
    monkeypatch.setattr(state, "observe_package", lambda target, **kwargs: state.PackageObservation(
        target.registry, target.package, "present", target.version, "fixture", NOW.isoformat()))
    monkeypatch.setattr(state, "observe_release", lambda target, **kwargs: state.PublicationObservation(
        target, "present", "fixture", NOW.isoformat()))
    calls = []
    def compare(root, source_head, artifacts, **kwargs):
        calls.append((root, source_head))
        return {"state": mode, "source_head": source_head, "scope": "tracked-python-package-content"}
    monkeypatch.setattr(source, "compare_published_python", compare)
    planned = state.plan_current_project(config, verify_source=True)
    assert planned.reconciliation_required is (mode == "diverged")
    assert not planned.pending and not planned.ready_for_goal
    assert not planned.to_dict()["source_publication_verified"]
    assert calls == [(tmp_path, head)]
    assert state.main(["--project", str(tmp_path), "--verify-source"]) == (2 if mode == "unknown" else 0)
    wire = json.loads(capsys.readouterr().out)
    assert wire["reconciliation_required"] is (mode == "diverged")
    assert wire["authorization_granted"] is False


@pytest.mark.parametrize("condition", ["dirty", "ticket_branch", "stale_tracking"])
def test_source_comparison_requires_synchronized_clean_base(release_project, tmp_path, monkeypatch, condition):
    from goal.publish import source
    config, git = release_project
    monkeypatch.setattr(state, "observe_package", lambda target, **kwargs: state.PackageObservation(
        target.registry, target.package, "present", target.version, "fixture", NOW.isoformat()))
    monkeypatch.setattr(state, "observe_release", lambda target, **kwargs: state.PublicationObservation(
        target, "present", "fixture", NOW.isoformat()))
    monkeypatch.setattr(source, "compare_published_python", lambda *a, **k: pytest.fail("must not compare"))
    if condition == "dirty":
        (tmp_path / "dirty.py").write_text("change\n")
    elif condition == "ticket_branch":
        git("checkout", "-qb", "ticket/001-fixture")
    else:
        (tmp_path / "README.md").write_text("changed\n")
        git("add", ".")
        git("commit", "-qm", "new head")
    planned = state.plan_current_project(config, verify_source=True)
    assert planned.source_comparison["state"] == "unknown"
    assert not planned.reconciliation_required and not planned.ready_for_goal


def test_opt_in_does_not_compare_a_missing_release(release_project, monkeypatch):
    from goal.publish import source
    config, _ = release_project
    monkeypatch.setattr(source, "compare_published_python", lambda *a, **k: pytest.fail("must not compare"))
    plan = state.plan_current_project(config, verify_source=True)
    assert plan.pending and plan.ready_for_goal and not plan.reconciliation_required


def test_source_flag_requires_project_context():
    with pytest.raises(SystemExit) as error:
        state.main(["--verify-source", "--registry", "pypi", "--package", "example", "--version", "1"])
    assert error.value.code == 2


@pytest.mark.parametrize("url", ["https://credential@files.pythonhosted.org/secret.whl", "https://evil.example/secret.whl"])
def test_release_metadata_does_not_emit_untrusted_artifact_urls(url):
    data = document()
    data["urls"][0]["url"] = url
    result = observe(data)
    assert result.state == "present" and result.artifacts[0].url is None
    assert "credential" not in json.dumps(result.to_dict()) and "evil.example" not in json.dumps(result.to_dict())
