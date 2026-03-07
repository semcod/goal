"""Goal CLI package - Split from monolithic cli.py for better maintainability."""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict

import click

try:
    import nfo
    from nfo.terminal import TerminalSink
    _HAS_NFO = True
except ImportError:
    _HAS_NFO = False

# Try both relative and absolute imports for flexibility
try:
    from ..git_ops import run_git
    from ..config import GoalConfig, ensure_config, init_config, load_config
    from ..user_config import get_user_config, initialize_user_config, show_user_config
except ImportError:
    from goal.git_ops import run_git
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


def strip_ansi(text: str) -> str:
    try:
        return ANSI_ESCAPE_RE.sub('', text)
    except Exception:
        return text


def read_ticket(path: Path = Path('TICKET')) -> Dict[str, str]:
    """Read TICKET configuration file (key=value)."""
    cfg: Dict[str, str] = {'prefix': '', 'format': '[{ticket}] {title}'}
    if not path.exists():
        return cfg
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            cfg[k.strip()] = v.strip()
    except Exception:
        return cfg
    return cfg


# Backward-compatible alias for the old typo name
read_tickert = read_ticket


def apply_ticket_prefix(title: str, ticket: Optional[str]) -> str:
    """Apply ticket prefix (from CLI or TICKET file) to commit title."""
    cfg = read_ticket()
    ticket_value = (ticket or cfg.get('prefix') or '').strip()
    if not ticket_value:
        return title
    fmt = cfg.get('format') or '[{ticket}] {title}'
    try:
        return fmt.format(ticket=ticket_value, title=title)
    except Exception:
        return f"[{ticket_value}] {title}"


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


def stage_paths(paths: List[str]):
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
        response = input(click.style(prompt, fg='cyan') + suffix).strip().lower()
        
        if not response:
            return default
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            click.echo(click.style("Please respond with 'y' or 'n'", fg='red'))


class GoalGroup(click.Group):
    """Custom Click Group that shows docs URL for unknown commands (like Poetry),
    and defaults to 'push' command when -a/--all is passed without a subcommand."""
    
    def get_command(self, ctx, cmd_name):
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
    
    def parse_args(self, ctx, args):
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
@click.option('--version', default=None, help='Explicit version to use')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all prompts')
@click.option('--all', '-a', 'all_flags', is_flag=True, help='Run full workflow (tests, push, publish)')
@click.option('--todo', '-t', is_flag=True, help='Create TODO.md file with detected issues')
@click.option('--markdown/--ascii', default=False, help='Output format')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--config', 'config_path', default=None, help='Path to goal.yaml config file')
@click.option('--abstraction', default=None, help='Abstraction level for commit messages')
@click.option('--nfo-format', default='markdown', help='nfo log format')
@click.option('--nfo-sink', default='', help='Additional nfo sink')
@click.pass_context
def main(ctx, bump, version, yes, all_flags, todo, markdown, dry_run, config_path, abstraction, nfo_format, nfo_sink):
    """Goal - Automated git push with smart commit messages."""
    _setup_nfo_logging(nfo_format, nfo_sink)
    
    ctx.ensure_object(dict)
    ctx.obj['bump'] = bump
    ctx.obj['version'] = version
    ctx.obj['yes'] = yes or all_flags
    ctx.obj['todo'] = todo
    ctx.obj['markdown'] = markdown
    ctx.obj['dry_run'] = dry_run
    ctx.obj['abstraction'] = abstraction
    
    # Load configuration
    config = load_config(config_path) if config_path else ensure_config()
    ctx.obj['config'] = config
    
    # Load user config
    user_config = get_user_config()
    ctx.obj['user_config'] = user_config


# Import commands to register them
from . import push_cmd
from . import publish_cmd
from . import utils_cmd
from . import doctor_cmd
from . import config_cmd
from . import commit_cmd

# Import version functions for external access
from .version import sync_all_versions

__all__ = [
    'main',
    'GoalGroup',
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
