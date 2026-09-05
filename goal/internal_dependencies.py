"""Explicit-catalog PyPI/SemVer freshness and transactional uv lock updates.

Catalogs are operator-reviewed allowlists, not ownership inferred from names.
Updates resolve in a disposable directory and replace only a verified lockfile.
Tests, installation and publication remain the consuming repository's workflow.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
from urllib.request import urlopen

SCHEMA = "goal.internal-dependencies/v1"
INDEX = "https://pypi.org/simple"
MAX_BYTES = 8_000_000
MAX_PACKAGES = 100
_NAME = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?")
_VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def version_key(value: str) -> tuple[int, ...] | None:
    """The initial catalog contract deliberately supports stable SemVer only."""
    if isinstance(value, str) and _VERSION.fullmatch(value):
        return tuple(int(part) for part in value.split("."))
    return None


def read_bytes(path: Path) -> bytes:
    if path.is_symlink():
        raise ValueError(f"Symlink input is not supported: {path.name}")
    with path.open("rb") as stream:
        content = stream.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError(f"Input exceeds {MAX_BYTES} bytes: {path.name}")
    return content


def read_catalog(path: Path) -> dict[str, dict]:
    document = json.loads(read_bytes(path))
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise ValueError(f"Catalog must use {SCHEMA}")
    packages = document.get("packages")
    if not isinstance(packages, list) or not 1 <= len(packages) <= MAX_PACKAGES:
        raise ValueError(f"Catalog must contain 1..{MAX_PACKAGES} packages")
    result = {}
    for package in packages:
        if not isinstance(package, dict):
            raise ValueError("Each catalog package must be an object")
        name = package.get("name")
        repository = package.get("repository")
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError("Invalid package name")
        if not isinstance(repository, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
        ):
            raise ValueError(f"Missing canonical repository for {name}")
        if package.get("registry") != "pypi" or package.get("versioning") != "semver":
            raise ValueError(
                "This catalog version supports registry=pypi, versioning=semver"
            )
        name = normalize(name)
        if name in result:
            raise ValueError(f"Duplicate catalog package: {name}")
        result[name] = {**package, "name": name}
    return result


def fetch_metadata(name: str) -> dict:
    # The host is fixed: catalog content cannot redirect queries to a custom index.
    with urlopen(f"https://pypi.org/pypi/{name}/json", timeout=15) as response:
        if response.geturl() != f"https://pypi.org/pypi/{name}/json":
            raise ValueError("Unexpected registry redirect")
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("Registry response exceeds size limit")
    return json.loads(content)


def latest_release(document: dict) -> dict:
    releases = document.get("releases", {})
    if not isinstance(releases, dict):
        raise ValueError("Invalid registry release metadata")
    candidates = []
    for version, files in releases.items():
        key = version_key(version)
        if key is not None and isinstance(files, list):
            usable = [f for f in files if isinstance(f, dict) and not f.get("yanked")]
            if usable:
                candidates.append((key, version, usable))
    if not candidates:
        raise ValueError("No published non-yanked stable SemVer release")
    _, version, files = max(candidates, key=lambda item: item[0])
    return {
        "target": version,
        "requires_python": sorted({f.get("requires_python") or "" for f in files}),
    }


def audit(project: Path, catalog: dict, *, fetch=None) -> dict:
    project = project.resolve()
    manifest = read_bytes(project / "pyproject.toml")
    locked = read_bytes(project / "uv.lock")
    config = tomllib.loads(manifest.decode())
    lock = tomllib.loads(locked.decode())
    overrides = config.get("tool", {}).get("uv", {}).get("sources", {})
    overrides = {normalize(name) for name in overrides}
    packages = {}
    for package in lock.get("package", []):
        name = normalize(package["name"])
        if name in catalog:
            packages.setdefault(name, []).append(package)
    fetch = fetch or fetch_metadata

    def inspect(name):
        entries = packages[name]
        versions = sorted({p.get("version", "") for p in entries})
        result = {
            "name": name,
            "repository": catalog[name]["repository"],
            "locked": versions,
        }
        if name in overrides or any(
            p.get("source", {}).get("registry", "").rstrip("/") != INDEX
            for p in entries
        ):
            return {**result, "status": "alternate-source"}
        try:
            release = latest_release(fetch(name))
            keys = [version_key(v) for v in versions]
            target = version_key(release["target"])
            status = "current"
            if any(key is None for key in keys):
                status = "unsupported-version"
            elif any(key > target for key in keys):
                status = "ahead-of-registry"
            elif any(key < target for key in keys):
                status = "outdated"
            return {**result, **release, "status": status}
        except (OSError, ValueError, TypeError, AttributeError) as error:
            return {**result, "status": "registry-error", "error": str(error)[:500]}

    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(inspect, sorted(packages)))
    command = ["uv", "lock"]
    for entry in entries:
        if entry["status"] == "outdated":
            command += ["--upgrade-package", f"{entry['name']}=={entry['target']}"]
    return {
        "schema": "goal.internal-dependency-report/v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "versioning": "stable-semver",
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "lock_sha256": hashlib.sha256(locked).hexdigest(),
        "packages": entries,
        "update_command": command,
        "fresh": bool(entries) and all(e["status"] == "current" for e in entries),
        "application_tests_run": False,
    }


def _run(command: list[str], project: Path, timeout: int = 120):
    return subprocess.run(
        command, cwd=project, capture_output=True, text=True, timeout=timeout
    )


def update_lock(project: Path, report: dict) -> dict:
    """Resolve a static standalone project; install no environment or project code."""
    project = project.resolve()
    if report["project"] != str(project):
        raise ValueError("Report belongs to another project")
    if not report["packages"]:
        raise ValueError("No catalogued packages found in uv.lock")
    if any(e["status"] not in {"current", "outdated"} for e in report["packages"]):
        raise ValueError("Resolve source, version or registry blockers before updating")
    if report["fresh"]:
        return {**report, "updated": False}
    git_root = _run(["git", "rev-parse", "--show-toplevel"], project, 15)
    if git_root.returncode:
        raise ValueError("Update requires a Git checkout")
    if any(
        (parent / ".governance" / "manifest.json").exists()
        for parent in (project, Path(git_root.stdout.strip()))
    ):
        raise ValueError(
            "Governed updates require a dependency-manifest delivery ticket"
        )
    status = _run(["git", "status", "--porcelain"], project, 15)
    if status.returncode or status.stdout.strip():
        raise ValueError("Update requires a clean Git checkout")
    common = _run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], project, 15
    )
    if common.returncode:
        raise ValueError("Cannot resolve Git common directory")
    guard = Path(common.stdout.strip()) / "goal-internal-dependencies.lock"
    # Clone-wide coordination includes linked worktrees; never delete someone else's guard.
    fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        original = read_bytes(project / "uv.lock")
        manifest = read_bytes(project / "pyproject.toml")
        if (
            hashlib.sha256(original).hexdigest() != report["lock_sha256"]
            or hashlib.sha256(manifest).hexdigest() != report["manifest_sha256"]
        ):
            raise ValueError("Project changed after audit; repeat the audit")
        config = tomllib.loads(manifest.decode())
        additional = {
            name: read_bytes(project / name)
            for name in ("uv.toml", ".python-version")
            if (project / name).exists()
        }
        uv = config.get("tool", {}).get("uv", {})
        if (
            config.get("project", {}).get("dynamic")
            or uv.get("sources")
            or uv.get("workspace")
        ):
            raise ValueError(
                "Automatic update requires static metadata without workspace/source overrides"
            )
        lock = tomllib.loads(original.decode())
        for package in lock.get("package", []):
            source = package.get("source", {})
            if any(key in source for key in ("path", "directory")) or any(
                source.get(key, ".") != "." for key in ("editable", "virtual")
            ):
                raise ValueError(
                    "Local dependency graph requires its repository workflow"
                )
        with tempfile.TemporaryDirectory(prefix="goal-internal-") as directory:
            candidate = Path(directory)
            (candidate / "pyproject.toml").write_bytes(manifest)
            (candidate / "uv.lock").write_bytes(original)
            for name, data in additional.items():
                (candidate / name).write_bytes(data)
            result = _run(report["update_command"], candidate)
            if result.returncode:
                raise ValueError(
                    "Resolution failed: " + (result.stderr or result.stdout)[-4000:]
                )
            content = read_bytes(candidate / "uv.lock")
            resolved = tomllib.loads(content.decode())
            for entry in report["packages"]:
                records = [
                    p
                    for p in resolved.get("package", [])
                    if normalize(p["name"]) == entry["name"]
                ]
                if not records or any(
                    p.get("version") != entry["target"]
                    or p.get("source", {}).get("registry", "").rstrip("/") != INDEX
                    for p in records
                ):
                    raise ValueError(
                        f"Resolver did not reach the exact registry target for {entry['name']}"
                    )
            if (
                read_bytes(project / "uv.lock") != original
                or read_bytes(project / "pyproject.toml") != manifest
            ):
                raise ValueError(
                    "Project changed during resolution; candidate discarded"
                )
            current_additional = {
                name: read_bytes(project / name)
                for name in ("uv.toml", ".python-version")
                if (project / name).exists()
            }
            if current_additional != additional:
                raise ValueError("Resolver configuration changed; candidate discarded")
            with tempfile.NamedTemporaryFile(
                dir=project, prefix=".uv-lock-", delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            try:
                os.chmod(temporary, (project / "uv.lock").stat().st_mode & 0o777)
                os.replace(temporary, project / "uv.lock")
            finally:
                temporary.unlink(missing_ok=True)
        return {
            **report,
            "updated": True,
            "fresh": True,
            "previous_packages": report["packages"],
            "packages": [
                {**entry, "locked": [entry["target"]], "status": "current"}
                for entry in report["packages"]
            ],
            "lock_sha256": hashlib.sha256(content).hexdigest(),
        }
    finally:
        guard.unlink()
