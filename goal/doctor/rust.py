"""Rust project diagnostics."""

import re
from pathlib import Path
from typing import List

try:
    from ..doctor.models import Issue
except ImportError:
    from goal.doctor.models import Issue


def diagnose_rust(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Rust-specific diagnostics."""
    issues: List[Issue] = []
    cargo = project_dir / 'Cargo.toml'
    if not cargo.exists():
        return issues

    content = cargo.read_text(errors='ignore')

    if not re.search(r'^\[package\]', content, re.MULTILINE):
        issues.append(Issue(
            severity='error', code='RS001',
            title='Missing [package] section in Cargo.toml',
            detail='Cargo.toml needs a [package] section with name and version.',
            file='Cargo.toml',
        ))

    if 'edition' not in content:
        issues.append(Issue(
            severity='warning', code='RS002',
            title='No edition specified in Cargo.toml',
            detail='Consider adding edition = "2021" to [package] for modern Rust features.',
            file='Cargo.toml',
        ))

    return issues
