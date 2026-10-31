"""A present version must not conceal changed package content or grant upload."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import subprocess
import threading
from urllib.error import HTTPError, URLError
import zipfile

import pytest

from goal.publish import source
from goal.publish.state import Artifact

NAME = "example-1.0.0-py3-none-any.whl"
URL = "https://files.pythonhosted.org/packages/fixture/" + NAME
FILES = {"example/__init__.py": b"VALUE = 1\n"}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def commit(root):
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture(params=[".", "src"])
def project(tmp_path, request):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    where = request.param
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nbuild-backend="setuptools.build_meta"\n'
        '[project]\nname="example"\nversion="1.0.0"\n'
        f'[tool.setuptools.packages.find]\nwhere=["{where}"]\ninclude=["example*"]\n')
    for name, raw in FILES.items():
        path = tmp_path / where / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return tmp_path, where, commit(tmp_path)


def wheel(files=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in (FILES if files is None else files).items():
            entry = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            archive.writestr(entry, value, compress_type=zipfile.ZIP_DEFLATED)
    return stream.getvalue()


def test_wheel_fixture_is_stable_across_clock_changes(monkeypatch):
    from types import SimpleNamespace
    def clock(year):
        return SimpleNamespace(time=lambda: 0, localtime=lambda *_: (year, 1, 1, 0, 0, 0, 0, 1, 0))
    monkeypatch.setattr(zipfile, "time", clock(2020))
    first = wheel()
    monkeypatch.setattr(zipfile, "time", clock(2021))
    assert wheel() == first


class Response(io.BytesIO):
    def __init__(self, raw, url=URL):
        super().__init__(raw)
        self.url = url
    def geturl(self):
        return self.url


def compare(project, *, files=None, artifacts=None, opener=None):
    root, _, head = project
    raw = wheel(files)
    artifacts = artifacts if artifacts is not None else [Artifact(NAME, hashlib.sha256(raw).hexdigest(), False, URL)]
    return source.compare_published_python(root, head, artifacts, timeout=5,
        opener=opener or (lambda url, timeout: Response(raw)))


def test_matching_static_python_content_is_scoped_and_read_only(project):
    root, _, head = project
    before = git(root, "status", "--porcelain")
    result = compare(project)
    assert result["state"] == "matched" and result["scope"] == "tracked-python-package-content"
    assert result["source_head"] == head and result["python_files_compared"] == 1
    assert result["source_manifest_sha256"] == result["published_manifest_sha256"]
    assert "verified" not in result and "authorization_granted" not in result
    assert git(root, "status", "--porcelain") == before == ""


@pytest.mark.parametrize("change", ["modified", "added", "deleted"])
def test_same_version_module_changes_are_detected(project, change):
    root, where, _ = project
    published = dict(FILES, **{"example/old.py": b"old\n"}) if change == "deleted" else FILES
    if change == "modified":
        (root / where / "example/__init__.py").write_text("VALUE = 2\n")
    elif change == "added":
        (root / where / "example/new.py").write_text("NEW = 1\n")
    else:
        (root / where / "example/current.py").write_text("CURRENT = 1\n")
    head = commit(root)
    result = compare((root, where, head), files=published)
    assert result["state"] == "diverged" and result["source_head"] == head
    assert result["source_manifest_sha256"] != result["published_manifest_sha256"]
    assert 'version="1.0.0"' in (root / "pyproject.toml").read_text()


def test_test_and_document_commits_do_not_imply_package_divergence(project):
    root, where, _ = project
    (root / "README.md").write_text("documentation\n")
    (root / "test_fixture.py").write_text("assert True\n")
    assert compare((root, where, commit(root)))["state"] == "matched"


@pytest.mark.parametrize("change", ["dirty", "new_commit"])
def test_download_race_cannot_bind_another_source(project, change):
    root, where, _ = project
    def opener(url, timeout):
        (root / where / "example/__init__.py").write_text("VALUE = 2\n")
        if change == "new_commit":
            commit(root)
        return Response(wheel())
    result = compare(project, opener=opener)
    assert result["state"] == "unknown" and result["reason"] == "source_changed_during_observation"


def test_dirty_source_is_not_downloaded(project):
    root, where, _ = project
    (root / where / "example/__init__.py").write_text("VALUE = 2\n")
    result = compare(project, opener=lambda *a, **k: pytest.fail("must not download"))
    assert result["reason"] == "source_not_clean"


@pytest.mark.parametrize("url", [None, "http://files.pythonhosted.org/" + NAME,
    "https://secret@files.pythonhosted.org/" + NAME, "https://evil.example/" + NAME,
    URL + "?download=1", URL + "#fragment", URL.replace(NAME, "other.whl"),
    "https://files.pythonhosted.org:443/" + NAME])
def test_untrusted_artifact_targets_are_unknown_without_network(project, url):
    artifact = Artifact(NAME, hashlib.sha256(wheel()).hexdigest(), False, url)
    result = compare(project, artifacts=[artifact], opener=lambda *a, **k: pytest.fail("must not download"))
    assert result["state"] == "unknown" and result["reason"] == "unsupported_artifact_url"
    assert "secret" not in json.dumps(result)


@pytest.mark.parametrize("kind", ["missing", "yanked", "binary", "ambiguous"])
def test_nonuniversal_or_ambiguous_wheel_selection_defers(project, kind):
    item = Artifact(NAME, hashlib.sha256(wheel()).hexdigest(), kind == "yanked", URL)
    artifacts = [] if kind == "missing" else [item, item] if kind == "ambiguous" else [item]
    if kind == "binary":
        artifacts = [Artifact("example-1.0.0-cp313-linux_x86_64.whl", item.sha256, False, URL)]
    assert compare(project, artifacts=artifacts)["reason"] == "unsupported_or_ambiguous_wheel"


@pytest.mark.parametrize("kind", ["hash", "redirect", "network", "invalid_zip"])
def test_failed_download_integrity_never_means_source_divergence(project, kind):
    raw = b"not a zip" if kind == "invalid_zip" else wheel()
    artifact = Artifact(NAME, "0" * 64 if kind == "hash" else hashlib.sha256(raw).hexdigest(), False, URL)
    def opener(url, timeout):
        if kind == "network":
            raise URLError("credential fixture must not appear")
        return Response(raw, "https://evil.example/redirect" if kind == "redirect" else URL)
    result = compare(project, artifacts=[artifact], opener=opener)
    assert result["state"] == "unknown" and "fixture" not in result["reason"]


def test_artifact_retry_after_is_retained(project):
    def opener(url, timeout):
        raise HTTPError(url, 429, "throttled", {"Retry-After": "120"}, None)
    result = compare(project, opener=opener)
    assert result["state"] == "unknown" and result["reason"] == "artifact_http_unknown"
    assert result["retry_not_before"]


@pytest.mark.parametrize("damage", ["backend", "where", "include", "mapping"])
def test_unsupported_packaging_layout_is_not_guessed(project, damage):
    root, where, _ = project
    path = root / "pyproject.toml"
    text = path.read_text()
    if damage == "backend":
        text = text.replace("setuptools.build_meta", "hatchling.build")
    elif damage == "where":
        text = text.replace(f'where=["{where}"]', 'where=["lib"]')
    elif damage == "include":
        text = text.replace('include=["example*"]', 'include=[]')
    else:
        text += '\n[tool.setuptools.package-dir]\n""="unexpected"\n'
    path.write_text(text)
    result = compare((root, where, commit(root)), opener=lambda *a, **k: pytest.fail("must not download"))
    assert result["state"] == "unknown" and result["reason"] == "unsupported_source_layout"


def test_compressed_archive_read_is_bounded(project, monkeypatch):
    monkeypatch.setattr(source, "MAX_ARCHIVE", 4)
    assert compare(project)["reason"] == "archive_size_limit"


@pytest.mark.parametrize("path", ["../escape.py", "/absolute.py", "example\\escape.py", "example/./escape.py", "example/line\n.py"])
def test_archive_paths_are_never_extracted_or_treated_as_source(path):
    with pytest.raises(source.Unknown, match="unsafe_archive_manifest"):
        source._wheel_files(wheel({path: b"payload"}))


def test_archive_duplicates_and_symlinks_are_unknown():
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w") as archive:
        with pytest.warns(UserWarning):
            archive.writestr("example/a.py", "first")
            archive.writestr("example/a.py", "second")
    with pytest.raises(source.Unknown, match="unsafe_archive_manifest"):
        source._wheel_files(raw.getvalue())
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w") as archive:
        item = zipfile.ZipInfo("example/link.py")
        item.external_attr = 0o120777 << 16
        archive.writestr(item, "target")
    with pytest.raises(source.Unknown, match="unsafe_archive_entry"):
        source._wheel_files(raw.getvalue())


def test_archive_uncompressed_and_file_count_limits(monkeypatch):
    monkeypatch.setattr(source, "MAX_FILE", 4)
    with pytest.raises(source.Unknown, match="unsafe_archive_entry"):
        source._wheel_files(wheel({"example/a.py": b"a" * 5}))
    monkeypatch.setattr(source, "MAX_FILE", 1024)
    monkeypatch.setattr(source, "MAX_CONTENT", 4)
    with pytest.raises(source.Unknown, match="archive_content_limit"):
        source._wheel_files(wheel({"example/a.py": b"aa", "example/b.py": b"aaa"}))
    monkeypatch.setattr(source, "MAX_CONTENT", 100)
    monkeypatch.setattr(source, "MAX_FILES", 1)
    with pytest.raises(source.Unknown, match="archive_content_limit"):
        source._wheel_files(wheel({"example/a.py": b"a", "example/b.py": b"b"}))


def test_source_symlink_is_not_followed(project):
    root, where, _ = project
    # Git can represent a symbolic entry as a plain file on platforms where
    # creating OS symlinks requires privileges. Keep this regression universal.
    git(root, "config", "core.symlinks", "false")
    name = "example/link.py" if where == "." else "src/example/link.py"
    (root / name).write_bytes(b"__init__.py")
    blob = subprocess.check_output(["git", "-C", str(root), "hash-object", "-w", "--stdin"], input=b"__init__.py").decode().strip()
    git(root, "update-index", "--add", "--cacheinfo", "120000", blob, name)
    git(root, "commit", "-qm", "symbolic fixture")
    assert git(root, "status", "--porcelain") == ""
    result = compare((root, where, git(root, "rev-parse", "HEAD")))
    assert result["reason"] == "source_entry_not_regular"


def test_default_downloader_refuses_redirect_before_a_second_request(project, monkeypatch):
    requested = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requested.append(self.path)
            self.send_response(302)
            self.send_header("Location", "/must-not-read-private-target")
            self.end_headers()
        def log_message(self, *args):
            pass
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        local = f"http://127.0.0.1:{server.server_port}/first/{NAME}"
        artifact = Artifact(NAME, hashlib.sha256(wheel()).hexdigest(), False, local)
        # Bypass only the initial public-host guard to exercise real urllib
        # redirect handling against an isolated loopback fixture.
        original = source.urlsplit
        monkeypatch.setattr(source, "urlsplit", lambda url: original(URL) if url == local else original(url))
        result = source.compare_published_python(project[0], project[2], [artifact], timeout=5)
        assert result["state"] == "unknown" and result["reason"] == "unexpected_artifact_redirect"
        assert requested == ["/first/" + NAME]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
