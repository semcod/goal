"""Bounded Python-content comparison; never reproducibility or upload authority."""
from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
from http.client import HTTPException
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tomllib
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
import zipfile

MAX_ARCHIVE = 20 * 1024 * 1024
MAX_CONTENT = 64 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024
MAX_FILES = 2000
SCOPE = "tracked-python-package-content"


class Unknown(ValueError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, target):
        return None


def _git(root, *args, input=None, limit=MAX_FILE):
    try:
        result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                capture_output=True, timeout=5, input=input)
    except (OSError, subprocess.TimeoutExpired):
        raise Unknown("source_unavailable") from None
    if result.returncode or len(result.stdout) > limit:
        raise Unknown("source_unavailable")
    return result.stdout


def _safe_path(name):
    return (isinstance(name, str) and name and not name.startswith("/") and "\\" not in name
            and not any(ord(c) < 32 or ord(c) == 127 for c in name)
            and not any(part in {".", "..", ""} for part in name.rstrip("/").split("/")))


def _source_files(root, head):
    metadata = tomllib.loads(_git(root, "show", head + ":pyproject.toml").decode())
    build = metadata.get("build-system", {})
    tool = metadata.get("tool", {}).get("setuptools", {})
    find = tool.get("packages", {}).get("find", {}) if isinstance(tool.get("packages", {}), dict) else {}
    where, include, exclude = find.get("where", ["."]), find.get("include"), find.get("exclude", [])
    if (build.get("build-backend") != "setuptools.build_meta" or build.get("backend-path")
            or where not in (["."], ["src"]) or not isinstance(include, list) or not include
            or not isinstance(exclude, list) or any(not isinstance(p, str) or not p for p in include + exclude)
            or tool.get("package-dir", {}) not in ({}, {"": "src"} if where == ["src"] else {})
            or tool.get("py-modules")):
        raise Unknown("unsupported_source_layout")
    prefix = "src/" if where == ["src"] else ""
    tracked = _git(root, "ls-tree", "-rlz", head).split(b"\0")
    selected, total = [], 0
    for entry in filter(None, tracked):
        header, name = entry.split(b"\t", 1)
        mode, kind, blob, size = header.split()
        name = name.decode()
        if not name.startswith(prefix) or not name.endswith(".py"):
            continue
        relative = name.removeprefix(prefix)
        package = ".".join(PurePosixPath(relative).parts[:-1])
        if not package or not any(fnmatchcase(package, p) for p in include) or any(fnmatchcase(package, p) for p in exclude):
            continue
        if not _safe_path(relative) or len(selected) >= MAX_FILES:
            raise Unknown("source_manifest_limit")
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise Unknown("source_entry_not_regular")
        length = int(size)
        total += length
        if length > MAX_FILE or total > MAX_CONTENT:
            raise Unknown("source_content_limit")
        selected.append((relative, blob, length))
    if not selected:
        raise Unknown("empty_source_manifest")
    payload = b"".join(blob + b"\n" for _, blob, _ in selected)
    stream = io.BytesIO(_git(root, "cat-file", "--batch", input=payload, limit=MAX_CONTENT + MAX_FILES * 128))
    result = {}
    for relative, blob, length in selected:
        if stream.readline(128).split() != [blob, b"blob", str(length).encode()]:
            raise Unknown("source_blob_mismatch")
        content = stream.read(length)
        if len(content) != length or stream.read(1) != b"\n":
            raise Unknown("source_blob_mismatch")
        result[relative] = hashlib.sha256(content).hexdigest()
    if stream.read(1):
        raise Unknown("source_blob_mismatch")
    return result


def _wheel_files(raw):
    result, total = {}, 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        names = [p.filename for p in members]
        if len(names) > 5000 or len(names) != len(set(names)) or not all(_safe_path(n) for n in names):
            raise Unknown("unsafe_archive_manifest")
        for member in members:
            if not member.filename.endswith(".py"):
                continue
            mode = member.external_attr >> 16
            if (mode & 0o170000) not in (0, 0o100000) or member.file_size > MAX_FILE:
                raise Unknown("unsafe_archive_entry")
            total += member.file_size
            if total > MAX_CONTENT or len(result) >= MAX_FILES:
                raise Unknown("archive_content_limit")
            with archive.open(member) as stream:
                content = stream.read(MAX_FILE + 1)
            if len(content) != member.file_size or len(content) > MAX_FILE:
                raise Unknown("archive_content_limit")
            result[member.filename] = hashlib.sha256(content).hexdigest()
    if not result:
        raise Unknown("empty_archive_manifest")
    return result


def _manifest_digest(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compare_published_python(root: Path, head: str, artifacts, *, timeout=10, opener=None):
    """Compare scoped package bytes only. Unknown results must never open tickets."""
    result = {"state": "unknown", "reason": "source_comparison_unavailable", "scope": SCOPE, "source_head": head}
    try:
        if not isinstance(head, str) or not re.fullmatch(r"[0-9a-f]{40}", head):
            raise Unknown("invalid_source_head")
        if not 0 < float(timeout) <= 120:
            raise Unknown("invalid_timeout")
        if _git(root, "rev-parse", "HEAD").decode().strip() != head or _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
            raise Unknown("source_not_clean")
        wheels = [a for a in artifacts if not a.yanked and a.filename.endswith("-none-any.whl")]
        if len(wheels) != 1:
            raise Unknown("unsupported_or_ambiguous_wheel")
        artifact = wheels[0]
        parsed = urlsplit(artifact.url or "")
        if (parsed.scheme != "https" or parsed.hostname != "files.pythonhosted.org" or parsed.port is not None
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or unquote(parsed.path.rsplit("/", 1)[-1]) != artifact.filename):
            raise Unknown("unsupported_artifact_url")
        if not re.fullmatch(r"[0-9a-f]{64}", artifact.sha256):
            raise Unknown("invalid_artifact_digest")
        source = _source_files(root, head)
        with (opener or build_opener(_NoRedirect()).open)(artifact.url, timeout=timeout) as response:
            if response.geturl() != artifact.url:
                raise Unknown("unexpected_artifact_redirect")
            raw = response.read(MAX_ARCHIVE + 1)
        if len(raw) > MAX_ARCHIVE:
            raise Unknown("archive_size_limit")
        if hashlib.sha256(raw).hexdigest() != artifact.sha256:
            raise Unknown("artifact_digest_mismatch")
        published = _wheel_files(raw)
        if _git(root, "rev-parse", "HEAD").decode().strip() != head or _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
            raise Unknown("source_changed_during_observation")
        matched = source == published
        result.update(state="matched" if matched else "diverged", reason="python_content_matches" if matched else "python_content_differs",
                      artifact=artifact.filename, artifact_sha256=artifact.sha256, source_manifest_sha256=_manifest_digest(source),
                      published_manifest_sha256=_manifest_digest(published), python_files_compared=len(source))
    except HTTPError as error:
        from goal.publish.state import _retry_deadline
        result.update(reason="unexpected_artifact_redirect" if 300 <= error.code < 400 else "artifact_http_unknown", retry_not_before=_retry_deadline(
            error.headers.get("Retry-After") if error.headers else None, datetime.now(timezone.utc)))
        error.close()
    except Unknown as error:
        result["reason"] = str(error)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, HTTPException, zipfile.BadZipFile, RuntimeError, UnicodeError):
        result["reason"] = "source_comparison_unavailable"
    return result
