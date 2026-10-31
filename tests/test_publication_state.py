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
