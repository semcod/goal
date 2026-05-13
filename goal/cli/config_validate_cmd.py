"""Goal config validate command - validates goal.yaml configuration."""

import sys
from typing import Optional

import click

from goal.config import validate_config_file, validate_config_interactive


@click.command(name="validate")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to goal.yaml configuration file (default: auto-detect)",
)
@click.option("--strict", "-s", is_flag=True, help="Treat warnings as errors")
@click.option(
    "--fix", "-f", is_flag=True, help="Interactively fix configuration issues"
)
@click.pass_context
def validate_cmd(ctx, config: Optional[str], strict: bool, fix: bool) -> None:
    """Validate goal.yaml configuration file.

    Checks that the configuration file is valid, complete, and follows
    best practices. Reports errors and warnings with helpful suggestions.

    Examples:
        goal config validate              # Validate auto-detected config
        goal config validate --strict     # Treat warnings as errors
        goal config validate --fix        # Interactively fix issues
        goal config validate -c ./goal.yaml  # Validate specific file
    """
    click.echo(
        click.style("🔍 Validating Goal configuration...\n", fg="blue", bold=True)
    )

    if fix:
        success = validate_config_interactive(config)
    else:
        success = validate_config_file(config, strict=strict)

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
