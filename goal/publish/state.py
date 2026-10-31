"""Read-only, exact-release observations shared by publishers and monitors.

``present`` means the registry serves a valid release document. Only
``verified`` additionally binds the caller's expected artifact names and hashes.
No result authorizes source edits, repair, upload or merge. Private registries
need their own explicit adapter; their URLs must never silently query PyPI.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
from http.client import HTTPException
import json
import math
from pathlib import Path
import re
from typing import Callable, Literal, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import urlopen


_REGISTRIES = {
    "pypi": "https://pypi.org",
    "testpypi": "https://test.pypi.org",
}
_MAX_DOCUMENT_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class ReleaseTarget:
    registry: str
    package: str
    version: str

    def __post_init__(self) -> None:
        registry = self.registry.rstrip("/")
        if registry.endswith("/simple"):
            registry = registry[:-7]
        registry = _REGISTRIES.get(registry.lower(), registry)
        if registry not in _REGISTRIES.values():
            raise ValueError("unsupported registry; explicitly select PyPI or TestPyPI")
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", self.package):
            raise ValueError("invalid distribution name")
        # Preserve PEP 440 spelling, including prerelease/local versions. A
        # response with different spelling is unknown, never inferred missing.
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]{0,199}", self.version):
            raise ValueError("invalid release version")
        object.__setattr__(self, "registry", registry)
        object.__setattr__(self, "package", re.sub(r"[-_.]+", "-", self.package).lower())

    @property
    def url(self) -> str:
        return f"{self.registry}/pypi/{quote(self.package, safe='')}/{quote(self.version, safe='')}/json"


@dataclass(frozen=True)
class Artifact:
    filename: str
    sha256: str
    yanked: bool


@dataclass(frozen=True)
class PublicationObservation:
    target: ReleaseTarget
    state: Literal["present", "missing", "unknown"]
    reason: str
    observed_at: str
    http_status: int | None = None
    retry_not_before: str | None = None
    artifacts: tuple[Artifact, ...] = ()
    verification: Literal["not_requested", "unverified", "matched", "mismatch", "incomplete"] = "not_requested"

    @property
    def verified(self) -> bool:
        return self.state == "present" and self.verification == "matched"

    def to_dict(self) -> dict:
        return {"schema": "goal.publication-observation/v1", **asdict(self), "verified": self.verified}


def _retry_deadline(value: str | None, now: datetime) -> str | None:
    if not value:
        return None
    try:
        deadline = now + timedelta(seconds=int(value)) if value.isdigit() else parsedate_to_datetime(value)
        if deadline.tzinfo is None:
            return None
        return max(now, deadline.astimezone(timezone.utc)).isoformat()
    except (ValueError, TypeError, OverflowError, IndexError):
        return None


def observe_release(
    target: ReleaseTarget,
    *,
    expected_artifacts: Mapping[str, str] | None = None,
    timeout: float = 10,
    opener: Callable | None = None,
    now: datetime | None = None,
) -> PublicationObservation:
    """Perform one bounded GET; preserve uncertainty and throttling metadata.

    Expected artifacts must be an explicit, nonempty set from the admitted
    build, not a dist glob selected here. Registry extras are permitted, but
    every expected file must exist, match SHA-256 and remain available.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    if expected_artifacts is not None and (
        not expected_artifacts
        or any(not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in expected_artifacts.values())
    ):
        raise ValueError("expected artifacts need nonempty SHA-256 digests")
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("observation time must be timezone-aware")
    verification = "unverified" if expected_artifacts is not None else "not_requested"

    def result(state: str, reason: str, **kwargs) -> PublicationObservation:
        return PublicationObservation(target, state, reason, instant.isoformat(), verification=verification, **kwargs)

    try:
        with (opener or urlopen)(target.url, timeout=timeout) as response:
            status = response.status
            if urlsplit(response.geturl())[:2] != urlsplit(target.registry)[:2]:
                return result("unknown", "unexpected_redirect", http_status=status)
            if status != 200:
                return result("unknown", "unexpected_http_status", http_status=status)
            document = response.read(_MAX_DOCUMENT_BYTES + 1)
        if len(document) > _MAX_DOCUMENT_BYTES:
            return result("unknown", "response_too_large", http_status=status)
        data = json.loads(document)
        info, urls = data["info"], data["urls"]
        if re.sub(r"[-_.]+", "-", info["name"]).lower() != target.package or info["version"] != target.version:
            return result("unknown", "release_identity_mismatch", http_status=status)
        if not isinstance(urls, list) or not urls:
            return result("unknown", "no_release_artifacts", http_status=status)
        artifacts = []
        for item in urls:
            name, digest, yanked = item["filename"], item["digests"]["sha256"], item["yanked"]
            if (not isinstance(name, str) or not name or name in {".", ".."}
                    or "/" in name or "\\" in name
                    or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                    or type(yanked) is not bool):
                return result("unknown", "invalid_artifact_metadata", http_status=status)
            artifacts.append(Artifact(name, digest, yanked))
        available = {item.filename: item for item in artifacts}
        if len(available) != len(artifacts):
            return result("unknown", "duplicate_artifact_metadata", http_status=status)
        if expected_artifacts is not None:
            if any(name not in available for name in expected_artifacts):
                verification = "incomplete"
            elif any(available[name].sha256 != digest or available[name].yanked for name, digest in expected_artifacts.items()):
                verification = "mismatch"
            else:
                verification = "matched"
        return result("present", "release_document", http_status=status, artifacts=tuple(sorted(artifacts, key=lambda item: item.filename)))
    except HTTPError as error:
        same_origin = urlsplit(error.geturl())[:2] == urlsplit(target.registry)[:2]
        retry = _retry_deadline(error.headers.get("Retry-After") if error.headers else None, instant)
        state = "missing" if error.code == 404 and same_origin else "unknown"
        error.close()
        return result(state, "not_found" if state == "missing" else "http_error", http_status=error.code, retry_not_before=retry)
    except (URLError, TimeoutError, OSError, HTTPException):
        return result("unknown", "network_error")
    except (ValueError, TypeError, KeyError, AttributeError):
        return result("unknown", "invalid_release_document")


def main(argv: list[str] | None = None) -> int:
    """JSON observation entrypoint; does not bootstrap the project or invoke Goal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifact", action="append", type=Path, default=[])
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args(argv)
    try:
        expected = {}
        for path in args.artifact:
            with path.open("rb") as stream:
                expected[path.name] = hashlib.file_digest(stream, "sha256").hexdigest()
        if len(expected) != len(args.artifact):
            raise ValueError("duplicate expected artifact names")
        observed = observe_release(ReleaseTarget(args.registry, args.package, args.version), expected_artifacts=expected or None, timeout=args.timeout)
    except (ValueError, OSError) as error:
        print(json.dumps({"schema": "goal.publication-observation/v1", "state": "unknown", "reason": str(error), "verified": False}))
        return 2
    print(json.dumps(observed.to_dict(), sort_keys=True))
    if observed.state == "unknown":
        return 2
    return 1 if expected and not observed.verified else 0


if __name__ == "__main__":
    raise SystemExit(main())
