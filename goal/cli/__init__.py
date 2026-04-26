"""Goal CLI package - Split from monolithic cli.py for better maintainability."""

import os
import re
import subprocess
import sys
from importlib import import_module
from typing import List, Dict, Any

import click
import goal

from goal import __version__

try:
    import nfo
    _HAS_NFO = True
except ImportError:
    _HAS_NFO = False

from goal.git_ops import run_git, read_ticket, read_tickert, apply_ticket_prefix
from goal.config import GoalConfig, ensure_config, init_config, load_config
from goal.user_config import get_user_config, initialize_user_config, show_user_config
from goal.cli_helpers import split_paths_by_type, stage_paths, confirm, strip_ansi


DOCS_URL = "https://github.com/wronai/goal#readme"


def _setup_nfo_logging(nfo_format: str = "markdown", nfo_sink: str = ""):
    """Configure nfo logging for the goal CLI session."""
    if not _HAS_NFO:
        return
    sinks = [f"terminal:{nfo_format}"]
    if nfo_sink:
        sinks.append(nfo_sink)
    nfo.configure(
        name="goal",
        level=os.environ.get("NFO_LEVEL", "INFO"),
        sinks=sinks,
        propagate_stdlib=False,
        force=True,
    )


def _nfo_log_call(**kwargs):
    """Conditional @nfo.log_call — no-op decorator when nfo is not installed."""
    if _HAS_NFO:
        return nfo.log_call(**kwargs)
    def _passthrough(fn):
        return fn
    return _passthrough


_COMMAND_MODULES_LOADED = False


def load_command_modules() -> None:
    """Import Click command modules so they register against `main`."""
    global _COMMAND_MODULES_LOADED

    if _COMMAND_MODULES_LOADED:
        return

    for module_name in (
        '.push_cmd',
        '.publish_cmd',
        '.utils_cmd',
        '.doctor_cmd',
        '.config_cmd',
        '.commit_cmd',
        '.recover_cmd',
        '.wizard_cmd',
        '.license_cmd',
        '.authors_cmd',
        '.hooks_cmd',
        '.postcommit_cmd',
        '.validation_cmd',
    ):
        import_module(module_name, __name__)

    _COMMAND_MODULES_LOADED = True


def _auto_update_goal(current_version: str, latest_version: str) -> bool:
    """Attempt to auto-update goal to the latest version.
    
    Returns True if update was successful, False otherwise.
    """
    click.echo(click.style(f"\n🔄 Auto-updating goal from v{current_version} to v{latest_version}...", fg='cyan'))
    
    try:
        # Use the same Python interpreter to run pip install
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-U', 'goal'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            click.echo(click.style(f"✅ Successfully updated to v{latest_version}", fg='green', bold=True))
            return True
        else:
            click.echo(click.style(f"❌ Update failed: {result.stderr}", fg='red'))
            return False
    except Exception as e:
        click.echo(click.style(f"❌ Update failed: {e}", fg='red'))
        return False


def _show_goal_version_banner() -> None:
    from goal import __version__
    from goal.version_validation import get_pypi_version

    latest = get_pypi_version("goal")
    if latest and latest != __version__:
        click.echo(click.style(f"Goal v{__version__} (latest: v{latest})", fg='yellow', bold=True))
        # Auto-update disabled temporarily due to bugs
        click.echo(click.style("  (Auto-update disabled - run: pip install -U goal)", fg='cyan'))
    else:
        click.echo(click.style(f"Goal v{__version__} ✓", fg='cyan', bold=True))


def _configure_main_context(ctx, bump, target_version, yes, all_flags, no_publish, todo, markdown, dry_run, config_path, abstraction) -> None:
    ctx.ensure_object(dict)
    ctx.obj['bump'] = bump
    ctx.obj['version'] = target_version
    ctx.obj['yes'] = yes or all_flags
    ctx.obj['no_publish'] = no_publish
    ctx.obj['todo'] = todo
    ctx.obj['markdown'] = markdown
    ctx.obj['dry_run'] = dry_run
    ctx.obj['abstraction'] = abstraction
    ctx.obj['config'] = load_config(config_path) if config_path else ensure_config()
    ctx.obj['user_config'] = get_user_config()


class GoalGroup(click.Group):
    """Custom Click Group that shows docs URL for unknown commands (like Poetry),
    and defaults to 'push' command when -a/--all is passed without a subcommand."""
    
    def get_command(self, ctx, cmd_name) -> Any:
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv
        # Unknown command - show helpful message with docs URL
        click.echo(click.style(f"The requested command {cmd_name} does not exist.\n", fg='red', bold=True))
        
        # Special hint for push command (indicates old version)
        if cmd_name == 'push':
            click.echo(click.style("💡 This command was added in recent versions. Update goal:\n", fg='cyan'))
            click.echo(click.style("   pip install -U goal\n", fg='yellow'))
        
        click.echo(click.style(f"Documentation: {DOCS_URL}", fg='cyan'))
        click.echo()
        click.echo(click.style("Available commands:", fg='cyan', bold=True))
        self.list_commands(ctx)
        ctx.exit(2)
    
    def parse_args(self, ctx, args) -> Any:
        # Check if -a or --all is in args without any command
        has_all_flag = '-a' in args or '--all' in args
        has_subcommand = any(
            not a.startswith('-') and a not in ('--help', '-h')
            for a in args
        )
        
        if has_all_flag and not has_subcommand:
            # Default to push command
            args = args + ['push']
        
        return super().parse_args(ctx, args)


@click.group(cls=GoalGroup)
@click.option('--bump', default='patch', help='Version bump type (major, minor, patch)')
@click.option('--target-version', default=None, help='Explicit version to use')
@click.version_option(version=__version__, prog_name="goal")
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all prompts')
@click.option('--all', '-a', 'all_flags', is_flag=True, help='Run full workflow (tests, push, publish)')
@click.option('--no-publish', is_flag=True, help='Skip publishing to registry')
@click.option('--todo', '-t', is_flag=True, help='Create TODO.md file with detected issues')
@click.option('--markdown/--ascii', default=False, help='Output format')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--config', 'config_path', default=None, help='Path to goal.yaml config file')
@click.option('--abstraction', default=None, help='Abstraction level for commit messages')
@click.option('--nfo-format', default='markdown', help='nfo log format')
@click.option('--nfo-sink', default='', help='Additional nfo sink')
@click.pass_context
def main(ctx, bump, target_version, yes, all_flags, no_publish, todo, markdown, dry_run, config_path, abstraction, nfo_format, nfo_sink) -> None:
    """Goal - Automated git push with smart commit messages."""
    # Skip version banner for help requests to avoid blocking help output
    # Check both sys.argv and Click's resilient_parsing (used for --help)
    is_help_request = '--help' in sys.argv or '-h' in sys.argv or ctx.resilient_parsing
    if not is_help_request:
        _show_goal_version_banner()
    _setup_nfo_logging(nfo_format, nfo_sink)

    _configure_main_context(ctx, bump, target_version, yes, all_flags, no_publish, todo,
                            markdown, dry_run, config_path, abstraction)


# Import commands to register them
load_command_modules()

# Import version functions for external access
from .version import sync_all_versions

__all__ = [
    'main',
    'GoalGroup',
    'load_command_modules',
    '_setup_nfo_logging',
    '_nfo_log_call',
    'strip_ansi',
    'read_ticket',
    'read_tickert',
    'apply_ticket_prefix',
    'split_paths_by_type',
    'stage_paths',
    'confirm',
    'sync_all_versions',
    'DOCS_URL',
]
