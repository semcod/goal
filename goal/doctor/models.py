"""Diagnostic models - Issue and DoctorReport dataclasses."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Issue:
    """A single diagnosed issue."""
    severity: str          # 'error', 'warning', 'info'
    code: str              # e.g. 'PY001'
    title: str             # short one-liner
    detail: str            # longer explanation for the user
    file: Optional[str] = None
    fixed: bool = False
    fix_description: str = ""


@dataclass
class DoctorReport:
    """Aggregated report from a doctor run."""
    project_dir: Path
    project_type: str
    issues: List[Issue] = field(default_factory=list)

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def fixed(self) -> List[Issue]:
        return [i for i in self.issues if i.fixed]

    @property
    def has_problems(self) -> bool:
        return any(i.severity in ('error', 'warning') for i in self.issues)
