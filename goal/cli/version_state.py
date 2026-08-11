"""Collect, explain and validate the version state of a project."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

from .version_utils import bump_version, is_plain_version


_VERSION_RE = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?P<suffix>.*)$"
)
_SELECTORS = {"version", "__version__"}
_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    ".venv_test",
    "venv",
    "env",
    ".env",
    "site-packages",
    "node_modules",
    "build",
    "dist",
    "target",
    "vendor",
    "third_party",
    "__pycache__",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".eggs",
    "examples",
    "example",
    "samples",
    "sample",
    "templates",
    "fixtures",
    "testdata",
    "__fixtures__",
}
_VERSION_FILENAMES = {
    "VERSION",
    "pyproject.toml",
    "package.json",
    "composer.json",
    "Cargo.toml",
    "setup.py",
    "pom.xml",
}
_PYTHON_VERSION_FILENAMES = {
    "__init__.py",
    "version.py",
    "_version.py",
    "__about__.py",
}
_DERIVED_LOCKS = {
    "pyproject.toml": ("uv.lock", "poetry.lock", "pdm.lock"),
    "package.json": ("package-lock.json", "pnpm-lock.yaml"),
    "Cargo.toml": ("Cargo.lock",),
}


class VersionStateError(ValueError):
    """The observed version state cannot be resolved safely."""

    def __init__(self, message: str, issues: Sequence[str] = ()) -> None:
        self.issues = tuple(issues)
        detail = "\n".join(f"- {issue}" for issue in self.issues)
        super().__init__(f"{message}\n{detail}" if detail else message)


@dataclass(frozen=True)
class VersionSource:
    """One configured or safely detected version declaration."""

    spec: str
    path: str
    selector: str
    value: Optional[str]
    origin: str
    error: Optional[str] = None
    contract: bool = False
    creatable: bool = False

    @property
    def managed(self) -> bool:
        return not self.contract and self.error is None


@dataclass(frozen=True)
class VersionDecision:
    """An explainable release-version decision."""

    current_version: str
    target_version: str
    reason: str
    sources: tuple[VersionSource, ...]
    baseline_version: Optional[str]
    baseline_evidence: tuple[str, ...]
    registry_versions: tuple[tuple[str, str], ...]
    unavailable_registries: tuple[str, ...]
    derived_paths: tuple[str, ...]

    @property
    def managed_specs(self) -> tuple[str, ...]:
        return tuple(source.spec for source in self.sources if source.managed)

    @property
    def stale_sources(self) -> tuple[VersionSource, ...]:
        return tuple(
            source
            for source in self.sources
            if source.managed and source.value != self.target_version
        )

    @property
    def local_drift(self) -> bool:
        values = {source.value for source in self.sources if source.value is not None}
        return len(values) > 1 or any(source.error for source in self.sources)


def normalize_version(value: str) -> str:
    value = value.strip()
    return value[1:] if value.startswith("v") else value


def version_key(value: str) -> tuple[int, int, int, int, str]:
    """Return a sortable key where a stable release follows its prereleases."""
    match = _VERSION_RE.fullmatch(value.strip())
    if not match:
        raise VersionStateError(f"Unsupported version value: {value!r}")
    suffix = match.group("suffix")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        1 if not suffix else 0,
        suffix,
    )


def _split_spec(spec: str) -> tuple[str, str]:
    path, separator, selector = spec.rpartition(":")
    if separator and selector in _SELECTORS:
        return path, selector
    return spec, ""


def _normalized_spec(spec: str) -> str:
    path, selector = _split_spec(spec)
    normalized = Path(path).as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return f"{normalized}:{selector}" if selector else normalized


def _extract_version(path: Path, selector: str, content: str) -> tuple[Optional[str], bool]:
    if path.name == "VERSION" and not selector:
        value = content.strip()
        if value and is_plain_version(value):
            return normalize_version(value), False
        return None, bool(value)

    if selector == "__version__" or path.name == "__init__.py":
        match = re.search(
            r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE
        )
        return (normalize_version(match.group(1)), False) if match else (None, False)

    if path.name in {"package.json", "composer.json"}:
        value = json.loads(content).get("version")
        return (normalize_version(str(value)), False) if value else (None, False)

    if path.name in {"pyproject.toml", "Cargo.toml"}:
        try:
            import tomllib

            document = tomllib.loads(content)
            if path.name == "Cargo.toml":
                value = (document.get("package") or {}).get("version")
            else:
                value = (document.get("project") or {}).get("version")
                if value is None:
                    value = ((document.get("tool") or {}).get("poetry") or {}).get(
                        "version"
                    )
            if value is not None:
                return normalize_version(str(value)), False
        except (TypeError, ValueError):
            pass

    patterns = (
        r'(?m)^version\s*=\s*["\']([^"\']+)["\']',
        r"<Version>([^<]+)</Version>",
        r"<version>([^<]+)</version>",
    )
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return normalize_version(match.group(1)), False
    return None, False


def read_version_source(spec: str, origin: str = "configured") -> VersionSource:
    normalized_spec = _normalized_spec(spec)
    path_text, selector = _split_spec(normalized_spec)
    path = Path(path_text)
    if not path.exists():
        if path.name == "VERSION" and not selector:
            return VersionSource(
                normalized_spec,
                path_text,
                selector,
                None,
                origin,
                creatable=True,
            )
        return VersionSource(
            normalized_spec,
            path_text,
            selector,
            None,
            origin,
            error="file does not exist",
        )
    try:
        value, contract = _extract_version(
            path, selector, path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return VersionSource(
            normalized_spec,
            path_text,
            selector,
            None,
            origin,
            error=str(exc),
        )
    if contract:
        return VersionSource(
            normalized_spec,
            path_text,
            selector,
            None,
            origin,
            contract=True,
        )
    if value is None:
        return VersionSource(
            normalized_spec,
            path_text,
            selector,
            None,
            origin,
            error=f"selector {selector or 'plain-version'} was not found",
        )
    if not is_plain_version(value):
        return VersionSource(
            normalized_spec,
            path_text,
            selector,
            value,
            origin,
            error=f"unsupported version value {value!r}",
        )
    return VersionSource(
        normalized_spec,
        path_text,
        selector,
        normalize_version(value),
        origin,
    )


def _configured_specs(config) -> tuple[str, ...]:
    if config is None:
        return ()
    if isinstance(config, Mapping):
        files = (config.get("versioning") or {}).get("files", [])
    else:
        try:
            files = config.get("versioning.files", [])
        except (AttributeError, TypeError):
            files = []
    return tuple(_normalized_spec(str(spec)) for spec in files or [])


def _candidate_spec(path: Path, content: Optional[str] = None) -> Optional[str]:
    if path.name in _PYTHON_VERSION_FILENAMES:
        try:
            text = content if content is not None else path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        declares_version = re.search(
            r'^__version__\s*=\s*["\'][^"\']+["\']', text, re.MULTILINE
        )
        return f"{path.as_posix()}:__version__" if declares_version else None
    if path.suffix in {".csproj", ".fsproj"}:
        return f"{path.as_posix()}:version"
    if path.name not in _VERSION_FILENAMES:
        return None
    selector = "" if path.name == "VERSION" else "version"
    return f"{path.as_posix()}:{selector}" if selector else path.as_posix()


def discover_version_specs() -> tuple[str, ...]:
    """Find version declarations while pruning dependencies and fixtures."""
    specs: list[str] = []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in _SKIP_DIRS and not name.endswith(".egg-info")
        ]
        for filename in filenames:
            path = Path(dirpath) / filename
            spec = _candidate_spec(path)
            if spec:
                specs.append(_normalized_spec(spec))
    return tuple(dict.fromkeys(specs))


def _is_primary_source(source: VersionSource) -> bool:
    parts = Path(source.path).parts
    if len(parts) == 1:
        return True
    if Path(source.path).name == "__init__.py":
        return len(parts) <= 2 or parts[0] in {"src", "lib", "app", "goal"}
    return False


def collect_version_sources(
    config=None, baseline_version: Optional[str] = None
) -> tuple[VersionSource, ...]:
    """Collect the configured release set plus inferred lockstep declarations."""
    configured = _configured_specs(config)
    candidates = discover_version_specs()
    ordered_specs = tuple(dict.fromkeys((*configured, *candidates)))
    if not ordered_specs:
        ordered_specs = ("VERSION",)

    configured_set = set(configured)
    observed: list[VersionSource] = []
    for spec in ordered_specs:
        initial_origin = "configured" if spec in configured_set else "detected"
        source = read_version_source(spec, initial_origin)
        if initial_origin == "detected" and _is_primary_source(source):
            source = VersionSource(**{**source.__dict__, "origin": "primary"})
        observed.append(source)

    authoritative_values = {
        source.value
        for source in observed
        if source.origin in {"configured", "primary"} and source.value is not None
    }
    if baseline_version:
        authoritative_values.add(normalize_version(baseline_version))

    selected: list[VersionSource] = []
    for source in observed:
        if source.origin in {"configured", "primary"}:
            selected.append(source)
            continue
        if source.value is not None and source.value in authoritative_values:
            selected.append(
                VersionSource(**{**source.__dict__, "origin": "inferred-lockstep"})
            )
    return tuple(selected)


def _normalized_package_identity(kind: str, name: str) -> tuple[str, str]:
    normalized = name.strip().casefold()
    if kind == "python":
        normalized = re.sub(r"[-_.]+", "-", normalized)
    return kind, normalized


def _manifest_package_identity(
    path: str, content: str
) -> Optional[tuple[str, str]]:
    try:
        if path == "pyproject.toml":
            document = tomllib.loads(content)
            project = document.get("project") or {}
            poetry = (document.get("tool") or {}).get("poetry") or {}
            name = project.get("name") or poetry.get("name")
            return (
                _normalized_package_identity("python", name)
                if isinstance(name, str) and name.strip()
                else None
            )
        if path == "package.json":
            name = json.loads(content).get("name")
            return (
                _normalized_package_identity("node", name)
                if isinstance(name, str) and name.strip()
                else None
            )
        if path == "Cargo.toml":
            name = (tomllib.loads(content).get("package") or {}).get("name")
            return (
                _normalized_package_identity("rust", name)
                if isinstance(name, str) and name.strip()
                else None
            )
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, TypeError, ValueError):
        return None
    return None


def _current_package_identity(
    project_types: Sequence[str],
) -> Optional[tuple[str, str, str]]:
    manifests = {
        "python": "pyproject.toml",
        "node": "package.json",
        "nodejs": "package.json",
        "rust": "Cargo.toml",
    }
    ordered_paths = [
        manifests[kind] for kind in project_types if kind in manifests
    ]
    ordered_paths.extend(["pyproject.toml", "package.json", "Cargo.toml"])
    for path in dict.fromkeys(ordered_paths):
        try:
            content = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        identity = _manifest_package_identity(path, content)
        if identity is not None:
            return path, *identity
    return None


def _tag_matches_package_identity(
    tag: str, current: tuple[str, str, str]
) -> bool:
    path, current_kind, current_name = current
    try:
        result = subprocess.run(
            ["git", "show", f"{tag}:{path}"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    if result.returncode != 0:
        return False
    identity = _manifest_package_identity(path, result.stdout)
    return identity == (current_kind, current_name)


def detect_git_tag_version(
    project_types: Sequence[str] = (),
) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "tag", "--merged", "HEAD", "--list"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    current_identity = _current_package_identity(project_types)
    versions = []
    for tag in result.stdout.splitlines():
        value = normalize_version(tag)
        if is_plain_version(value) and (
            current_identity is None
            or _tag_matches_package_identity(tag, current_identity)
        ):
            versions.append(value)
    return max(versions, key=version_key) if versions else None


def _version_at_ref(source: VersionSource, ref: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{source.path}"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    try:
        value, contract = _extract_version(
            Path(source.path), source.selector, result.stdout
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None if contract or value is None else normalize_version(value)


def detect_version_transition_boundary(
    sources: Iterable[VersionSource], base_ref: str
) -> Optional[str]:
    """Find the first commit where all managed carriers reached HEAD's version.

    A publish-only delivery can leave the latest release tag behind the version
    already present in the registry.  The synchronized version transition then
    provides a safe lower bound for committed-source analysis.  Ambiguous or
    incomplete history deliberately returns ``None`` so callers can fall back
    to the release tag.
    """
    managed = tuple(
        source for source in sources if source.managed and source.value is not None
    )
    current_values = {source.value for source in managed}
    if len(current_values) != 1:
        return None
    current = next(iter(current_values))

    if all(_version_at_ref(source, base_ref) == current for source in managed):
        return None

    paths = tuple(dict.fromkeys(source.path for source in managed))
    try:
        result = subprocess.run(
            [
                "git",
                "rev-list",
                "--reverse",
                "--topo-order",
                f"{base_ref}..HEAD",
                "--",
                *paths,
            ],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None

    for commit in result.stdout.splitlines():
        if commit and all(
            _version_at_ref(source, commit) == current for source in managed
        ):
            return commit
    return None


def detect_git_history_baseline(sources: Iterable[VersionSource]) -> Optional[str]:
    """Find a lower HEAD/HEAD^ value that proves a local bump already happened."""
    local_values = [source.value for source in sources if source.value is not None]
    if not local_values:
        return None
    highest_local = max(local_values, key=version_key)
    historic: list[str] = []
    for source in sources:
        if not source.managed:
            continue
        for ref in ("HEAD", "HEAD^"):
            value = _version_at_ref(source, ref)
            if value and version_key(value) < version_key(highest_local):
                historic.append(value)
    return max(historic, key=version_key) if historic else None


def _registry_evidence(
    project_types: Sequence[str], current_version: str
) -> tuple[dict[str, str], tuple[str, ...]]:
    if not project_types:
        return {}, ()
    from goal.version_validation import validate_project_versions

    try:
        results = validate_project_versions(list(project_types), current_version)
    except Exception:
        # Registry access is release safety evidence, not an online requirement
        # for inspecting and repairing local version state.
        return {}, tuple(str(project_type) for project_type in project_types)
    versions: dict[str, str] = {}
    unavailable: list[str] = []
    for project_type, result in results.items():
        value = result.get("registry_version")
        registry = result.get("registry") or project_type
        package = result.get("package_name") or "unknown-package"
        label = f"{registry}:{package}"
        if value and is_plain_version(str(value)):
            versions[label] = normalize_version(str(value))
        elif result.get("package_name"):
            unavailable.append(label)
    return versions, tuple(unavailable)


def _derived_paths(sources: Sequence[VersionSource]) -> tuple[str, ...]:
    derived: list[str] = []
    for source in sources:
        name = Path(source.path).name
        for lock_name in _DERIVED_LOCKS.get(name, ()):
            candidate = Path(source.path).parent / lock_name
            if candidate.exists():
                derived.append(candidate.as_posix())
    if Path("README.md").exists():
        try:
            readme = Path("README.md").read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            readme = ""
        if "img.shields.io/badge/version-" in readme or "img.shields.io/badge/v-" in readme:
            derived.append("README.md")
    return tuple(dict.fromkeys(derived))


def _highest_version(values: Iterable[str]) -> Optional[str]:
    values = tuple(values)
    return max(values, key=version_key) if values else None


def resolve_version_decision(
    *,
    bump: str = "patch",
    target_version: Optional[str] = None,
    config=None,
    project_types: Sequence[str] = (),
    registry_versions: Optional[Mapping[str, str]] = None,
    release_required: bool = True,
    allow_registry_ahead_repair: bool = False,
) -> VersionDecision:
    """Resolve the release target without mutating the project."""
    tag_version = detect_git_tag_version(project_types)
    initial_sources = collect_version_sources(config, tag_version)
    initial_values = [
        source.value for source in initial_sources if source.value is not None
    ]
    registry_unavailable: tuple[str, ...] = ()
    if registry_versions is None:
        registry_map, registry_unavailable = _registry_evidence(
            project_types,
            _highest_version(initial_values) or tag_version or "0.0.0",
        )
    else:
        registry_map = {
            str(name): normalize_version(str(value))
            for name, value in registry_versions.items()
            if value and is_plain_version(str(value))
        }

    baseline_candidates: list[tuple[str, str]] = []
    if tag_version:
        baseline_candidates.append((f"git-tag:v{tag_version}", tag_version))
    baseline_candidates.extend(
        (f"registry:{name}", value) for name, value in registry_map.items()
    )
    baseline = _highest_version(value for _, value in baseline_candidates)
    sources = collect_version_sources(config, baseline)
    if baseline is None:
        baseline = detect_git_history_baseline(sources)
        if baseline:
            baseline_candidates.append(("git-history", baseline))
            sources = collect_version_sources(config, baseline)

    issues = [
        f"{source.spec}: {source.error}"
        for source in sources
        if source.error is not None
    ]
    if issues:
        raise VersionStateError("Version sources are unreadable or unsupported", issues)

    local_versions = {
        source.value for source in sources if source.value is not None and source.managed
    }
    for value in local_versions:
        version_key(value)

    if target_version is not None:
        target = normalize_version(target_version)
        if not is_plain_version(target):
            raise VersionStateError(f"Invalid --target-version value: {target_version!r}")
        target_key = version_key(target)
        unsafe = [
            f"{source.spec} declares {source.value}, which is newer than target {target}"
            for source in sources
            if source.value is not None and version_key(source.value) > target_key
        ]
        if baseline and target_key < version_key(baseline):
            unsafe.append(
                f"target {target} is older than released baseline {baseline}"
            )
        if unsafe:
            raise VersionStateError("Explicit target would regress version state", unsafe)
        current = baseline or _highest_version(local_versions) or "0.0.0"
        reason = "explicit-target"
    elif baseline:
        baseline_key = version_key(baseline)
        regressions = sorted(
            (value for value in local_versions if version_key(value) < baseline_key),
            key=version_key,
        )
        forward = sorted(
            (value for value in local_versions if version_key(value) > baseline_key),
            key=version_key,
        )
        if regressions:
            registry_is_baseline = any(
                label.startswith("registry:") and value == baseline
                for label, value in baseline_candidates
            )
            uniform_local_version = (
                next(iter(local_versions)) if len(local_versions) == 1 else None
            )
            # ``goal -a`` may recover from an interrupted/accidental adjacent
            # publication, but must not turn a stale or internally inconsistent
            # checkout into a new release automatically.
            repair_registry_ahead = bool(
                allow_registry_ahead_repair
                and registry_is_baseline
                and not forward
                and uniform_local_version is not None
                and bump_version(uniform_local_version, "patch") == baseline
            )
            if forward or (
                baseline not in local_versions and not repair_registry_ahead
            ):
                raise VersionStateError(
                    "Local version state regresses behind released evidence",
                    [
                        f"local {value} < released baseline {baseline}"
                        for value in regressions
                    ],
                )
            current = baseline
            if release_required:
                target = bump_version(baseline, bump)
                reason = (
                    "auto-bump-from-registry"
                    if repair_registry_ahead
                    else "normal-bump-with-repair"
                )
            else:
                target = baseline
                reason = (
                    "auto-sync-to-registry"
                    if repair_registry_ahead
                    else "released-partial-repair"
                )
            forward = []
        if len(forward) > 1:
            raise VersionStateError(
                "Multiple forward version candidates are ambiguous",
                [f"candidate {value}" for value in forward],
            )
        if not regressions:
            current = baseline
            if forward:
                target = forward[0]
                reason = (
                    "partial-bump"
                    if baseline in local_versions
                    else "already-bumped"
                )
            elif release_required:
                target = bump_version(baseline, bump)
                reason = "normal-bump"
            else:
                target = baseline
                reason = "no-release"
    else:
        if len(local_versions) > 1:
            raise VersionStateError(
                "Version sources disagree and no release baseline can resolve them",
                [f"observed {value}" for value in sorted(local_versions, key=version_key)],
            )
        current = next(iter(local_versions), "0.0.0")
        target = bump_version(current, bump)
        reason = "normal-bump"

    selected_evidence = tuple(
        label for label, value in baseline_candidates if value == baseline
    )
    return VersionDecision(
        current_version=current,
        target_version=target,
        reason=reason,
        sources=sources,
        baseline_version=baseline,
        baseline_evidence=selected_evidence,
        registry_versions=tuple(sorted(registry_map.items())),
        unavailable_registries=registry_unavailable,
        derived_paths=_derived_paths(sources),
    )


def write_version_source(spec: str, target_version: str) -> bool:
    """Write one declared source and fail instead of silently skipping it."""
    target = normalize_version(target_version)
    normalized_spec = _normalized_spec(spec)
    path_text, selector = _split_spec(normalized_spec)
    path = Path(path_text)
    source = read_version_source(normalized_spec, "synchronization")
    if source.contract:
        raise VersionStateError(
            "Refusing to overwrite a VERSION data contract", [normalized_spec]
        )
    if source.error:
        raise VersionStateError(
            "Cannot synchronize configured version source",
            [f"{normalized_spec}: {source.error}"],
        )
    if source.value == target:
        return False
    if source.creatable:
        path.write_text(f"{target}\n", encoding="utf-8")
        return True

    content = path.read_text(encoding="utf-8")
    new_content = content
    if path.name == "VERSION" and not selector:
        new_content = f"{target}\n"
    elif selector == "__version__" or path.name == "__init__.py":
        new_content, count = re.subn(
            r'^(__version__\s*=\s*["\'])[^"\']+(["\'])',
            rf"\g<1>{target}\g<2>",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if count != 1:
            raise VersionStateError(
                "Cannot synchronize configured version source",
                [f"{normalized_spec}: selector was not writable"],
            )
    elif path.name in {"package.json", "composer.json"}:
        document = json.loads(content)
        if "version" not in document:
            raise VersionStateError(
                "Cannot synchronize configured version source",
                [f"{normalized_spec}: version key is missing"],
            )
        document["version"] = target
        new_content = json.dumps(document, indent=2) + "\n"
    elif path.name in {"pyproject.toml", "Cargo.toml"}:
        try:
            import tomlkit

            document = tomlkit.parse(content)
            table_name = "package" if path.name == "Cargo.toml" else "project"
            if table_name in document and "version" in document[table_name]:
                document[table_name]["version"] = target
            elif (
                path.name == "pyproject.toml"
                and "tool" in document
                and "poetry" in document["tool"]
                and "version" in document["tool"]["poetry"]
            ):
                document["tool"]["poetry"]["version"] = target
            else:
                raise KeyError("version key is missing")
            new_content = tomlkit.dumps(document)
        except (KeyError, TypeError, ValueError) as exc:
            raise VersionStateError(
                "Cannot synchronize configured version source",
                [f"{normalized_spec}: {exc}"],
            ) from exc
    else:
        substitutions = (
            (r'(?m)^(version\s*=\s*["\'])[^"\']+(["\'])', rf"\g<1>{target}\g<2>"),
            (r"(<Version>)[^<]+(</Version>)", rf"\g<1>{target}\g<2>"),
            (r"(<version>)[^<]+(</version>)", rf"\g<1>{target}\g<2>"),
        )
        for pattern, replacement in substitutions:
            new_content, count = re.subn(pattern, replacement, content, count=1)
            if count:
                break
        else:
            raise VersionStateError(
                "Cannot synchronize configured version source",
                [f"{normalized_spec}: no supported writable selector"],
            )

    if new_content == content:
        raise VersionStateError(
            "Version source did not change to the selected target",
            [normalized_spec],
        )
    path.write_text(new_content, encoding="utf-8")
    return True


def validate_version_sources(specs: Iterable[str], target_version: str) -> None:
    """Read managed declarations back and require the exact selected target."""
    target = normalize_version(target_version)
    issues: list[str] = []
    for spec in dict.fromkeys(_normalized_spec(spec) for spec in specs):
        source = read_version_source(spec, "validation")
        if source.contract:
            issues.append(f"{source.spec}: configured VERSION is a data contract")
        elif source.error:
            issues.append(f"{source.spec}: {source.error}")
        elif source.value != target:
            issues.append(f"{source.spec}: expected {target}, found {source.value}")
    if issues:
        raise VersionStateError("Version synchronization validation failed", issues)


def format_version_decision(decision: VersionDecision) -> list[str]:
    """Render concise, file-level evidence for CLI output."""
    baseline = decision.baseline_version or "none"
    evidence = ", ".join(decision.baseline_evidence) or "local-only"
    lines = [
        f"Version baseline: {baseline} ({evidence})",
        f"Version decision: {decision.reason} -> {decision.target_version}",
    ]
    for source in decision.sources:
        if source.contract:
            state = "data-contract (ignored)"
        elif source.error:
            state = f"ERROR: {source.error}"
        elif source.value is None:
            state = "missing (will create)"
        elif source.value == decision.target_version:
            state = f"{source.value} (target)"
        else:
            state = f"{source.value} -> {decision.target_version}"
        lines.append(f"  {source.spec} [{source.origin}]: {state}")
    if decision.derived_paths:
        lines.append("Derived updates: " + ", ".join(decision.derived_paths))
    if decision.unavailable_registries:
        lines.append(
            "Registry evidence unavailable: "
            + ", ".join(decision.unavailable_registries)
        )
    return lines
