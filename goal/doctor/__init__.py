"""Doctor package - Project diagnostics and auto-fix.

This package provides automated diagnostics for various project types
and can auto-fix common configuration issues.
"""

# Models
from .models import Issue, DoctorReport

# Core diagnostic functions
from .core import (
    diagnose_project,
    diagnose_and_report,
    _DIAGNOSTICS,
)

# Language-specific diagnostics
from .python import diagnose_python
from .nodejs import diagnose_nodejs
from .rust import diagnose_rust
from .go import diagnose_go
from .ruby import diagnose_ruby
from .php import diagnose_php
from .dotnet import diagnose_dotnet
from .java import diagnose_java

# TODO management
from .todo import (
    add_issues_to_todo,
    diagnose_and_report_with_todo,
    _generate_ticket_id,
    _read_existing_tickets,
    _format_todo_entry,
)

# Logging helpers
from .logging import _log_issue, _log_fix, _SEVERITY_STYLE

__all__ = [
    'Issue',
    'DoctorReport',
    'diagnose_project',
    'diagnose_and_report',
    'diagnose_and_report_with_todo',
    'add_issues_to_todo',
    # Language-specific diagnostics
    'diagnose_python',
    'diagnose_nodejs',
    'diagnose_rust',
    'diagnose_go',
    'diagnose_ruby',
    'diagnose_php',
    'diagnose_dotnet',
    'diagnose_java',
]
