"""Compatibility shim for ``goal.cli`` — emits import warnings when the
package layout differs from the expected entry points.
"""
from typing import Any


def _format_import_warning_message(exc: BaseException) -> str:
    """Return a single-line warning describing a failed ``goal.cli`` import."""
    return f'Warning: goal.cli shim failed to import: {exc}'


def _print_import_warning(exc: BaseException, stderr: Any) -> None:
    """Write the formatted import warning for ``exc`` to ``stderr``."""
    message = _format_import_warning_message(exc)
    print(message, file=stderr)