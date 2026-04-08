def _print_import_warning(exc: BaseException, stderr: Any) -> None:
    print(f'Warning: goal.cli shim failed to import: {exc}', file=stderr)
