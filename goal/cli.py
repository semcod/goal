#!/usr/bin/env python3
"""Goal CLI - Automated git push with smart commit messages and version management.

NOTE: This file now serves as a backward-compatibility shim.
The actual implementation has been split into the goal.cli package.
"""

# Re-export everything from the new cli package for backward compatibility
try:
    from .cli import (
        main, GoalGroup, _setup_nfo_logging, _nfo_log_call,
        strip_ansi, read_ticket, read_tickert, apply_ticket_prefix,
        split_paths_by_type, stage_paths, confirm,
        DOCS_URL,
    )
    from .cli.version import (
        PROJECT_TYPES, detect_project_types, find_version_files,
        get_version_from_file, get_current_version, bump_version,
        update_version_in_file, update_json_version, update_project_metadata,
        update_readme_metadata, sync_all_versions,
    )
    from .cli.publish import makefile_has_target, publish_project
    from .cli.tests import run_tests
    from .cli.push_cmd import push
    from .cli.publish_cmd import publish
    from .cli.utils_cmd import status, init, info, version, package_managers, check_versions, clone, bootstrap
    from .cli.doctor_cmd import doctor
    from .cli.config_cmd import config, config_show, config_validate, config_update, config_set, config_get, setup
    from .cli.commit_cmd import commit, fix_summary, validate
except ImportError as _exc:
    import sys as _sys
    print(f"Warning: goal.cli shim failed to import: {_exc}", file=_sys.stderr)
    pass


# If no imports from the new package worked, define minimal compatibility
if 'main' not in globals():
    import click
    from pathlib import Path
    
    @click.group()
    def main():
        """Goal CLI - Please ensure goal.cli package is properly installed."""
        click.echo("Error: Could not load goal.cli package. Please check installation.")
        raise click.Abort()


# Maintain backward compatibility for direct function access
__all__ = [
    'main', 'push', 'publish', 'status', 'init', 'info', 'version',
    'package_managers', 'doctor', 'config', 'commit', 'validate',
    'fix_summary', 'clone', 'bootstrap', 'check_versions', 'setup',
    'GoalGroup', '_setup_nfo_logging', '_nfo_log_call',
    'strip_ansi', 'read_tickert', 'apply_ticket_prefix',
    'split_paths_by_type', 'stage_paths', 'confirm',
    'detect_project_types', 'get_current_version', 'bump_version',
    'sync_all_versions', 'publish_project', 'run_tests',
    'makefile_has_target', 'DOCS_URL',
]


if __name__ == '__main__':
    main()
