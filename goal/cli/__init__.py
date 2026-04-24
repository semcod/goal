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


ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
_COMMAND_MODULES_LOADED = False


def strip_ansi(text: str) -> str:
    try:
        return ANSI_ESCAPE_RE.sub('', text)
    except Exception:
        return text


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


def split_paths_by_type(paths: List[str]) -> Dict[str, List[str]]:
    """Split file paths into groups (code/docs/ci/examples/other)."""
    groups: Dict[str, List[str]] = {'code': [], 'docs': [], 'ci': [], 'examples': [], 'other': []}
    for p in paths:
        pl = p.lower()
        if pl.startswith('examples/'):
            groups['examples'].append(p)
        elif pl.startswith('docs/') or pl.endswith(('.md', '.rst')) or os.path.basename(pl) in ('readme.md',):
            groups['docs'].append(p)
        elif pl.startswith('.github/') or pl.startswith('.gitlab/') or pl.endswith(('.yml', '.yaml')):
            groups['ci'].append(p)
        elif pl.startswith('src/') or pl.startswith('lib/') or pl.endswith('.py'):
            groups['code'].append(p)
        else:
            groups['other'].append(p)

    return {k: v for k, v in groups.items() if v}


def stage_paths(paths: List[str]) -> None:
    if not paths:
        return
    # stage in chunks to avoid arg length issues
    chunk: List[str] = []
    for p in paths:
        chunk.append(p)
        if len(chunk) >= 100:
            run_git('add', '--', *chunk)
            chunk = []
    if chunk:
        run_git('add', '--', *chunk)


def confirm(prompt: str, default: bool = True) -> bool:
    """Ask for user confirmation with Y/n prompt (Enter defaults to Yes)."""
    if default:
        suffix = " [Y/n] "
    else:
        suffix = " [y/N] "
    
    while True:
        response = input(f"{click.style(prompt, fg='cyan')}{suffix}").strip().lower()
        
        if not response:
            return default
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            click.echo(click.style("Please respond with 'y' or 'n'", fg='red'))


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
        
        # Check if auto-update is enabled (via environment variable or config)
        auto_update = os.environ.get('GOAL_AUTO_UPDATE', '').lower() in ('1', 'true', 'yes')
        
        # Also check config if env var is not set
        if not auto_update:
            try:
                from goal.config import ensure_config
                config = ensure_config()
                auto_update = config.get('advanced.auto_update_config', False)
            except Exception:
                pass
        
        if auto_update:
            if confirm("Auto-update to latest version?", default=True):
                success = _auto_update_goal(__version__, latest)
                if success:
                    # Restart goal with the new version
                    click.echo(click.style("\n🔄 Restarting goal with new version...", fg='cyan'))
                    os.execv(sys.executable, [sys.executable] + sys.argv)
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
