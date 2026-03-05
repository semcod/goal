"""Config commands - extracted from cli.py."""

import click

try:
    from ..config import GoalConfig, load_config, ensure_config
    from ..user_config import get_user_config, show_user_config, initialize_user_config
    from . import main
except ImportError:
    from goal.config import GoalConfig, load_config, ensure_config
    from goal.user_config import get_user_config, show_user_config, initialize_user_config
    from goal.cli import main


@main.group()
def config():
    """Manage goal configuration."""
    pass


@config.command(name='show')
@click.argument('key', required=False)
@click.pass_context
def config_show(ctx, key):
    """Show configuration value(s)."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = ensure_config()
    
    if key:
        value = cfg.get(key)
        click.echo(f"{key}: {value}")
    else:
        click.echo(click.style("=== Goal Configuration ===", fg='cyan', bold=True))
        for k, v in cfg.to_dict().items():
            click.echo(f"  {k}: {v}")


@config.command(name='validate')
@click.pass_context
def config_validate(ctx):
    """Validate goal.yaml configuration."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = ensure_config()
    
    errors = cfg.validate()
    if errors:
        click.echo(click.style("Configuration errors:", fg='red', bold=True))
        for error in errors:
            click.echo(f"  ✗ {error}")
    else:
        click.echo(click.style("✓ Configuration is valid", fg='green'))


@config.command(name='update')
@click.pass_context
def config_update(ctx):
    """Update configuration with latest defaults."""
    cfg = ensure_config(auto_update=True)
    click.echo(click.style("✓ Configuration updated", fg='green'))


@config.command(name='set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = ensure_config()
    
    cfg.set(key, value)
    click.echo(click.style(f"✓ Set {key} = {value}", fg='green'))


@config.command(name='get')
@click.argument('key')
@click.pass_context
def config_get(ctx, key):
    """Get a configuration value."""
    cfg = ctx.obj.get('config')
    if not cfg:
        cfg = ensure_config()
    
    value = cfg.get(key)
    click.echo(f"{key}: {value}")


@main.command()
@click.option('--reset', is_flag=True, help='Reset to defaults')
@click.option('--show', 'show_config', is_flag=True, help='Show current config')
def setup(reset, show_config):
    """Setup goal configuration interactively."""
    if reset:
        initialize_user_config(force=True)
        click.echo(click.style("✓ Configuration reset", fg='green'))
    elif show_config:
        show_user_config()
    else:
        # Interactive setup
        initialize_user_config()
        click.echo(click.style("✓ Setup complete", fg='green'))


__all__ = [
    'config',
    'config_show',
    'config_validate',
    'config_update',
    'config_set',
    'config_get',
    'setup',
]
