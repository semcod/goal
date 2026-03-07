"""Project doctor — auto-diagnose and auto-fix common project configuration issues.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.doctor package.
"""

# Re-export everything from the new doctor package for backward compatibility
try:
    from .doctor import (
        Issue, DoctorReport,
        diagnose_project, diagnose_and_report,
        add_issues_to_todo, diagnose_and_report_with_todo,
        # Private functions for test compatibility
        diagnose_python as _diagnose_python,
        diagnose_nodejs as _diagnose_nodejs,
        diagnose_rust as _diagnose_rust,
        diagnose_go as _diagnose_go,
        diagnose_ruby as _diagnose_ruby,
        diagnose_php as _diagnose_php,
        diagnose_dotnet as _diagnose_dotnet,
        diagnose_java as _diagnose_java,
    )
except ImportError:
    # Fallback if relative imports fail
    from goal.doctor import (
        Issue, DoctorReport,
        diagnose_project, diagnose_and_report,
        add_issues_to_todo, diagnose_and_report_with_todo,
        # Private functions for test compatibility
        diagnose_python as _diagnose_python,
        diagnose_nodejs as _diagnose_nodejs,
        diagnose_rust as _diagnose_rust,
        diagnose_go as _diagnose_go,
        diagnose_ruby as _diagnose_ruby,
        diagnose_php as _diagnose_php,
        diagnose_dotnet as _diagnose_dotnet,
        diagnose_java as _diagnose_java,
    )


# Maintain backward compatibility for direct function access
__all__ = [
    'Issue', 'DoctorReport',
    'diagnose_project', 'diagnose_and_report',
    'add_issues_to_todo', 'diagnose_and_report_with_todo',
    '_diagnose_python', '_diagnose_nodejs', '_diagnose_rust',
    '_diagnose_go', '_diagnose_ruby', '_diagnose_php',
    '_diagnose_dotnet', '_diagnose_java',
]
