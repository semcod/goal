"""Read-only Cargo manifest and test discovery for bootstrap."""

import re
import tomllib
from pathlib import Path


def cargo_manifest(root: Path) -> dict:
    return tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))


def is_virtual_workspace(manifest: dict) -> bool:
    return isinstance(manifest.get("workspace"), dict) and "package" not in manifest


def rust_test_files(root: Path) -> list[Path]:
    """Find integration and inline unit tests in declared workspace members."""
    roots = {root}
    try:
        manifest = cargo_manifest(root)
        workspace = manifest.get("workspace", {})
        if isinstance(workspace, dict):
            excluded = {
                path.resolve()
                for pattern in workspace.get("exclude", [])
                for path in root.glob(pattern)
            }
            for pattern in workspace.get("members", []):
                roots.update(path for path in root.glob(pattern)
                             if path.resolve() not in excluded
                             and (path / "Cargo.toml").is_file())
    except (OSError, ValueError, TypeError):
        # Diagnostics owns malformed manifests; discovery never repairs them.
        pass
    found = set()
    for package in roots:
        found.update((package / "tests").rglob("*.rs"))
        for source in (package / "src").rglob("*.rs"):
            try:
                content = source.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if re.search(r"#\s*\[\s*(?:\w+::)*test\s*(?:\([^\]]*\))?\s*\]", content):
                found.add(source)
    return sorted(found)
