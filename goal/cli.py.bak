def _format_import_warning_message(exc: BaseException) -> str:
    return f'Warning: goal.cli shim failed to import: {exc}'


def _print_import_warning(exc: BaseException, stderr: Any) -> None:
    message = _format_import_warning_message(exc)
    print(message, file=stderr)
