"""Rust project diagnostics."""

import tomllib
from pathlib import Path

from goal.doctor.models import Issue
from goal.rust_project import cargo_manifest, is_virtual_workspace


def diagnose_rust(project_dir: Path, auto_fix: bool = True) -> list[Issue]:
    """Run all Rust-specific diagnostics."""
    issues: list[Issue] = []
    cargo = project_dir / "Cargo.toml"
    if not cargo.exists():
        return issues

    try:
        manifest = cargo_manifest(project_dir)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return [Issue(severity="error", code="RS003", title="Invalid Cargo.toml",
                      detail=str(error), file="Cargo.toml")]

    if is_virtual_workspace(manifest):
        return issues  # A virtual root has no package or package edition.

    package = manifest.get("package")
    if not isinstance(package, dict):
        issues.append(
            Issue(
                severity="error",
                code="RS001",
                title="Missing [package] section in Cargo.toml",
                detail="Cargo.toml needs a [package] section with name and version.",
                file="Cargo.toml",
            )
        )

    if isinstance(package, dict) and "edition" not in package:
        issues.append(
            Issue(
                severity="warning",
                code="RS002",
                title="No edition specified in Cargo.toml",
                detail='Consider adding edition = "2021" to [package] for modern Rust features.',
                file="Cargo.toml",
            )
        )

    return issues
