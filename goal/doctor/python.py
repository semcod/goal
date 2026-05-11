"""Python project diagnostics — public API."""

from pathlib import Path
from typing import List

from goal.doctor.models import Issue
from goal.doctor.python_diag_extended import PythonDiagnostics



def diagnose_python(project_dir: Path, auto_fix: bool = True) -> List[Issue]:
    """Run all Python-specific diagnostics."""
    pyproject = project_dir / 'pyproject.toml'
    setup_py = project_dir / 'setup.py'
    setup_cfg = project_dir / 'setup.cfg'
    requirements = project_dir / 'requirements.txt'
    
    # PY001: Quick return if no config files
    if not pyproject.exists() and not setup_py.exists() and not setup_cfg.exists():
        issues: List[Issue] = []
        if requirements.exists():
            issues.append(Issue(
                severity='warning', code='PY001',
                title='No pyproject.toml / setup.py / setup.cfg found',
                detail='Only requirements.txt exists. Consider adding pyproject.toml for proper packaging.',
            ))
        return issues
    
    if not pyproject.exists():
        return []
    
    # Initialize diagnostics
    content = pyproject.read_text(errors='ignore')
    diag = PythonDiagnostics(project_dir, content, auto_fix)
    
    # Run all checks via registry
    diag.run_all_checks()
    
    # Write fixes
    diag.write_fixes(pyproject)
    
    return diag.issues
