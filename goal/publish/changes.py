"""Detect whether staged changes warrant a registry publish."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Iterable

# Basenames that are release metadata, not package source.
METADATA_BASENAMES = frozenset(
    {
        "VERSION",
        "CHANGELOG.md",
        "README.md",
        "goal.yaml",
        "uv.lock",
        "poetry.lock",
        "Pipfile.lock",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
        "Cargo.lock",
        "go.sum",
        "Gemfile.lock",
        "composer.lock",
        "Package.resolved",
        "pubspec.lock",
        "mix.lock",
        "gradle.lockfile",
        "packages.lock.json",
    }
)

# Manifest / version files — not published artifacts on their own.
MANIFEST_BASENAMES = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "environment.yml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "composer.json",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "mix.exs",
        "pubspec.yaml",
        "Package.swift",
        "Makefile",
    }
)

NON_PUBLISHABLE_PREFIXES = (
    "docs/",
    ".github/",
    ".gitlab/",
    ".planfile/",
    "dist/",
    "build/",
    ".venv/",
    "node_modules/",
    "tests/",
    "test/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "examples/",
    "project/",
)

SOURCE_PREFIXES = (
    "src/",
    "lib/",
    "goal/",
    "pkg/",
    "internal/",
    "cmd/",
    "app/",
    "crates/",
)

PUBLISHABLE_SUFFIXES: dict[str, frozenset[str]] = {
    "python": frozenset({".py"}),
    "nodejs": frozenset({".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}),
    "rust": frozenset({".rs"}),
    "go": frozenset({".go"}),
    "ruby": frozenset({".rb"}),
    "php": frozenset({".php"}),
    "dotnet": frozenset({".cs", ".fs", ".vb"}),
    "java": frozenset({".java", ".kt", ".kts"}),
    "elixir": frozenset({".ex", ".exs"}),
    "haskell": frozenset({".hs", ".lhs"}),
    "swift": frozenset({".swift"}),
    "dart": frozenset({".dart"}),
    "kotlin": frozenset({".kt", ".kts"}),
}

# Project types that goal can publish to a registry.
REGISTRY_PROJECT_TYPES = frozenset(PUBLISHABLE_SUFFIXES.keys())


@dataclass
class PublishChangeReport:
    """Result of analyzing staged files for publish-worthy changes."""

    has_changes: bool
    project_types: list[str] = field(default_factory=list)
    publishable_files: list[str] = field(default_factory=list)
    non_publishable_files: list[str] = field(default_factory=list)
    reason: str = ""

    @property
    def skip_reason(self) -> str:
        if self.has_changes:
            return ""
        return self.reason or "no_package_changes"


def _normalize_path(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix()


def _basename(path: str) -> str:
    return PurePosixPath(path).name


def _suffix(path: str) -> str:
    return PurePosixPath(path).suffix.lower()


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    normalized = _normalize_path(path)
    for pattern in patterns:
        if normalized == pattern or normalized.startswith(pattern):
            return True
        if fnmatch(_basename(normalized), pattern):
            return True
    return False


def _is_test_path(path: str) -> bool:
    normalized = _normalize_path(path)
    name = _basename(normalized)
    if _matches_any(normalized, ("tests/", "test/")):
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    if name.endswith((".test.js", ".test.ts", ".test.tsx", ".spec.js", ".spec.ts")):
        return True
    return name in {"conftest.py", "pytest.ini", "tox.ini"}


def _is_metadata_file(path: str) -> bool:
    normalized = _normalize_path(path)
    name = _basename(normalized)
    if name in METADATA_BASENAMES or name in MANIFEST_BASENAMES:
        return True
    if normalized.endswith((".md", ".rst", ".yaml", ".yml")):
        return True
    if _matches_any(normalized, NON_PUBLISHABLE_PREFIXES):
        return True
    if name.endswith(".gemspec") or name.endswith((".csproj", ".fsproj", ".cabal")):
        return True
    return False


def _is_publishable_for_type(path: str, project_type: str) -> bool:
    normalized = _normalize_path(path)
    if _is_metadata_file(path) or _is_test_path(path):
        return False

    suffixes = PUBLISHABLE_SUFFIXES.get(project_type)
    if not suffixes:
        return False

    if _suffix(normalized) in suffixes:
        if _matches_any(normalized, SOURCE_PREFIXES):
            return True
        # Top-level package modules (e.g. goal/*.py) or nested docker subprojects.
        parts = normalized.split("/")
        if len(parts) >= 2 and _suffix(normalized) in suffixes:
            return True
        if len(parts) == 1 and _suffix(normalized) in suffixes:
            return True

    if project_type == "rust" and _matches_any(normalized, ("src/", "benches/")):
        return True

    return False


def analyze_publishable_changes(
    files: list[str],
    project_types: list[str],
) -> PublishChangeReport:
    """Return whether any staged file changes package source for registry types."""
    registry_types = [t for t in project_types if t in REGISTRY_PROJECT_TYPES]
    if not registry_types:
        return PublishChangeReport(
            has_changes=False,
            project_types=registry_types,
            non_publishable_files=list(files),
            reason="no_registry_project_types",
        )

    publishable: list[str] = []
    non_publishable: list[str] = []

    for path in files:
        matched = any(_is_publishable_for_type(path, ptype) for ptype in registry_types)
        if matched:
            publishable.append(path)
        else:
            non_publishable.append(path)

    if publishable:
        return PublishChangeReport(
            has_changes=True,
            project_types=registry_types,
            publishable_files=publishable,
            non_publishable_files=non_publishable,
        )

    return PublishChangeReport(
        has_changes=False,
        project_types=registry_types,
        non_publishable_files=non_publishable,
        reason="no_package_source_changes",
    )
