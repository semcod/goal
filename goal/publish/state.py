"""Read-only, exact-release observations shared by publishers and monitors.

``present`` means the registry serves a valid release document. Only
``verified`` additionally binds the caller's expected artifact names and hashes.
No result authorizes source edits, repair, upload or merge. Private registries
need their own explicit adapter; their URLs must never silently query PyPI.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
from http.client import HTTPException
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Callable, Literal, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
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
    url: str | None = None


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


def _registry_document(target, url, timeout, opener, instant):
    """One bounded transport for exact releases and package existence queries."""
    def error(state, reason, **kwargs):
        return None, PublicationObservation(target, state, reason, instant.isoformat(), **kwargs)

    try:
        with (opener or urlopen)(url, timeout=timeout) as response:
            status = response.status
            if urlsplit(response.geturl())[:2] != urlsplit(target.registry)[:2]:
                return error("unknown", "unexpected_redirect", http_status=status)
            if status != 200:
                return error("unknown", "unexpected_http_status", http_status=status)
            document = response.read(_MAX_DOCUMENT_BYTES + 1)
        if len(document) > _MAX_DOCUMENT_BYTES:
            return error("unknown", "response_too_large", http_status=status)
        return json.loads(document), None
    except HTTPError as failure:
        same_origin = urlsplit(failure.geturl())[:2] == urlsplit(target.registry)[:2]
        retry = _retry_deadline(failure.headers.get("Retry-After") if failure.headers else None, instant)
        state = "missing" if failure.code == 404 and same_origin else "unknown"
        failure.close()
        return error(state, "not_found" if state == "missing" else "http_error", http_status=failure.code, retry_not_before=retry)
    except (URLError, TimeoutError, OSError, HTTPException):
        return error("unknown", "network_error")
    except (ValueError, TypeError, AttributeError):
        return error("unknown", "invalid_release_document")


@dataclass(frozen=True)
class PackageObservation:
    registry: str
    package: str
    state: Literal["present", "missing", "unknown"]
    latest_version: str | None
    reason: str
    observed_at: str
    http_status: int | None = None
    retry_not_before: str | None = None


def observe_package(target: ReleaseTarget, *, timeout=10, opener=None, now=None) -> PackageObservation:
    """Distinguish a new distribution from unavailable latest-version metadata."""
    instant = now or datetime.now(timezone.utc)
    if not math.isfinite(timeout) or timeout <= 0 or instant.tzinfo is None:
        raise ValueError("query requires a positive finite timeout and aware time")
    url = f"{target.registry}/pypi/{quote(target.package, safe='')}/json"
    data, error = _registry_document(target, url, timeout, opener, instant)
    if error is not None:
        return PackageObservation(target.registry, target.package, error.state, None, error.reason,
                                  error.observed_at, error.http_status, error.retry_not_before)
    try:
        actual = ReleaseTarget(target.registry, data["info"]["name"], data["info"]["version"])
        if actual.package != target.package:
            raise ValueError("package identity mismatch")
        return PackageObservation(target.registry, target.package, "present", actual.version,
                                  "package_document", instant.isoformat(), 200)
    except (ValueError, TypeError, KeyError, AttributeError):
        return PackageObservation(target.registry, target.package, "unknown", None,
                                  "invalid_package_document", instant.isoformat(), 200)


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

    data, error = _registry_document(target, target.url, timeout, opener, instant)
    if error is not None:
        return replace(error, verification=verification)
    status = 200
    try:
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
            url = item.get("url")
            try:
                parsed = urlsplit(url) if isinstance(url, str) else None
                host = "files.pythonhosted.org" if target.registry == "https://pypi.org" else "test-files.pythonhosted.org"
                if (parsed is None or parsed.scheme != "https" or parsed.hostname != host or parsed.port is not None
                        or parsed.username or parsed.password or parsed.query or parsed.fragment
                        or unquote(parsed.path.rsplit("/", 1)[-1]) != name):
                    url = None
            except ValueError:
                url = None
            artifacts.append(Artifact(name, digest, yanked, url))
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
    except (ValueError, TypeError, KeyError, AttributeError):
        return result("unknown", "invalid_release_document")


@dataclass(frozen=True)
class ProjectReleasePlan:
    project_root: str
    package: str | None = None
    version: str | None = None
    source_head: str | None = None
    source_branch: str | None = None
    source_clean: bool = False
    tracking_head: str | None = None
    repository: str | None = None
    observation: PublicationObservation | None = None
    package_observation: PackageObservation | None = None
    pending: bool = False
    initial_release: bool = False
    ready_for_goal: bool = False
    reconciliation_required: bool = False
    source_comparison: dict | None = None
    reason: str = "not_configured"

    def to_dict(self):
        return {"schema": "goal.release-plan/v1", **asdict(self),
                "authorization_granted": False, "source_publication_verified": False}


def _config_value(config, key, default=None):
    if isinstance(config, Mapping):
        value = config
        for part in key.split("."):
            if not isinstance(value, Mapping) or part not in value:
                return default
            value = value[part]
        return value
    return config.get(key, default) if config is not None else default


def _git_observation(*arguments):
    try:
        result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                                 *arguments], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def plan_current_project(config=None, *, timeout=10, require_config=False, verify_source=False) -> ProjectReleasePlan:
    """Read-only release intent. Eligibility never substitutes for Goal admission.

    Tracking refs are observations, not an authoritative remote or review proof.
    Goal -a must revalidate the remote base, source ownership and protected gates.
    Existing-version presence also says nothing about a newer source/artifact.
    """
    root = Path.cwd().resolve()
    base = _config_value(config, "governance.delivery.base_branch", "main")
    remote = _config_value(config, "governance.delivery.remote", "origin")
    valid_refs = (isinstance(base, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", base)
                  and isinstance(remote, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", remote))
    head = _git_observation("rev-parse", "HEAD")
    branch = _git_observation("branch", "--show-current")
    top = _git_observation("rev-parse", "--show-toplevel")
    clean = _git_observation("status", "--porcelain=v1", "--untracked-files=all") == ""
    tracking = _git_observation("rev-parse", f"refs/remotes/{remote}/{base}") if valid_refs else None
    identity = None
    if valid_refs:
        origin = _git_observation("remote", "get-url", remote) or ""
        # Never emit userinfo, query tokens or arbitrary remote-helper strings.
        match = re.fullmatch(r"git@github\.com:([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?", origin)
        if match:
            identity = "github.com/" + match.group(1).lower()
        else:
            try:
                parsed = urlsplit(origin)
                if ((parsed.scheme == "https" and parsed.hostname == "github.com")
                        or (parsed.scheme == "ssh" and parsed.hostname in {"github.com", "ssh.github.com"})):
                    path = parsed.path.strip("/").removesuffix(".git")
                    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path):
                        identity = "github.com/" + path.lower()
            except ValueError:
                pass
    values = dict(project_root=str(root), source_head=head, source_branch=branch,
                  source_clean=clean, tracking_head=tracking, repository=identity)

    def plan(reason, **changes):
        return ProjectReleasePlan(**values, reason=reason, **changes)

    if require_config and _config_value(config, "publishing.enabled") is None:
        return plan("publishing_not_configured")
    if _config_value(config, "publishing.enabled", True) is not True:
        return plan("publishing_disabled")
    if _config_value(config, "strategies.python.publish_enabled", True) is not True:
        return plan("python_publishing_disabled")
    registries = _config_value(config, "publishing.registries", ["pypi"])
    if registries != ["pypi"]:
        return plan("unsupported_project_registry")
    if any((root / name).is_file() for name in ("package.json", "Cargo.toml")):
        return plan("mixed_registry_project_requires_explicit_adapter")
    try:
        metadata = tomllib.loads((root / "pyproject.toml").read_text())["project"]
        target = ReleaseTarget(_config_value(config, "registries.pypi.url", "pypi"), metadata["name"], metadata["version"])
        if target.registry != "https://pypi.org":
            return plan("unsupported_workflow_registry")
        from goal.cli.version_state import collect_version_sources, normalize_version, version_key
        versions = {source.value for source in collect_version_sources(config) if source.value is not None}
        if versions != {normalize_version(target.version)}:
            return plan("version_sources_disagree")
        version_key(target.version)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return plan("unsupported_or_missing_package_metadata")
    values.update(package=target.package, version=target.version)
    package = observe_package(target, timeout=timeout)
    if package.state == "unknown":
        return plan("registry_unknown", package_observation=package)
    if package.state == "missing":
        exact = PublicationObservation(target, "missing", "package_not_found", package.observed_at, 404)
        pending, initial = True, True
    else:
        exact = observe_release(target, timeout=timeout)
        if exact.state == "unknown":
            return plan("registry_unknown", observation=exact, package_observation=package)
        try:
            pending = exact.state == "missing" and version_key(target.version) > version_key(package.latest_version)
        except (ValueError, TypeError):
            return plan("unsupported_registry_version", observation=exact, package_observation=package)
        initial = False
    delivery = _config_value(config, "governance.delivery", {})
    allowed = delivery.get("allowed_modes", ["pull-request"]) if isinstance(delivery, Mapping) else []
    governed = (isinstance(delivery, Mapping) and delivery.get("default_mode", "pull-request") == "pull-request"
                and delivery.get("require_goal_a") is True and delivery.get("require_clean_governance") is True
                and isinstance(allowed, list) and "pull-request" in allowed)
    synchronized = (governed and clean and head is not None and head == tracking
                    and branch == base and top is not None and Path(top).resolve() == root and identity is not None)
    comparison = None
    if verify_source and exact.state == "present":
        try:
            if version_key(target.version) < version_key(package.latest_version):
                return plan("source_version_behind_registry", observation=exact, package_observation=package)
        except (ValueError, TypeError):
            return plan("unsupported_registry_version", observation=exact, package_observation=package)
        from goal.publish.source import compare_published_python
        comparison = (compare_published_python(root, head, exact.artifacts, timeout=timeout)
                      if synchronized else {"state": "unknown", "reason": "source_not_synchronized", "source_head": head})
        reason = {"diverged": "published_python_content_differs", "matched": "published_python_content_matches"}.get(
            comparison["state"], "published_python_content_unknown")
        return plan(reason, observation=exact, package_observation=package, source_comparison=comparison,
                    reconciliation_required=comparison["state"] == "diverged", pending=False, ready_for_goal=False)
    return plan("pending_release" if pending else "version_present_or_not_newer", observation=exact,
                package_observation=package, pending=pending, initial_release=initial, ready_for_goal=bool(pending and synchronized))


def main(argv: list[str] | None = None) -> int:
    """JSON observation entrypoint; does not bootstrap the project or invoke Goal."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry")
    parser.add_argument("--package")
    parser.add_argument("--version")
    parser.add_argument("--project", type=Path, help="Read-only plan for one configured project")
    parser.add_argument("--project-config", type=Path, help="Explicit configuration for --project")
    parser.add_argument("--verify-source", action="store_true", help="Compare public wheel Python content with supported clean Git source")
    parser.add_argument("--artifact", action="append", type=Path, default=[])
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args(argv)
    if args.project is not None:
        if any((args.registry, args.package, args.version, args.artifact)):
            parser.error("--project cannot be combined with explicit registry/package/version/artifacts")
        previous = Path.cwd()
        configuration = args.project_config.resolve() if args.project_config is not None else None
        try:
            os.chdir(args.project)
            config = None
            configuration = configuration or Path("goal.yaml")
            if configuration.is_file():
                import yaml
                try:
                    config = yaml.safe_load(configuration.read_text())
                except yaml.YAMLError:
                    raise ValueError("invalid project configuration") from None
                if not isinstance(config, dict):
                    raise ValueError("project configuration must be a mapping")
            planned = plan_current_project(config, timeout=args.timeout, require_config=True, verify_source=args.verify_source)
            print(json.dumps(planned.to_dict(), sort_keys=True))
            return 2 if planned.reason in {"registry_unknown", "published_python_content_unknown"} else 0
        except (ValueError, OSError):
            print(json.dumps({"schema": "goal.release-plan/v1", "reason": "project_plan_unavailable",
                              "ready_for_goal": False, "authorization_granted": False}))
            return 2
        finally:
            os.chdir(previous)
    if args.project_config is not None:
        parser.error("--project-config requires --project")
    if args.verify_source:
        parser.error("--verify-source requires --project")
    if not all((args.registry, args.package, args.version)):
        parser.error("--registry, --package and --version are required without --project")
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
