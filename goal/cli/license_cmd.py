"""License commands for Goal."""

import click

from goal.cli import main
from goal.user_config import UserConfig
from goal.license import (
    LicenseManager,
    create_license_file,
    update_license_file,
    validate_spdx_id,
    get_license_info,
    check_compatibility,
)


@main.group()
def license() -> None:
    """Manage project licenses."""
    pass


@license.command(name="create")
@click.argument("license_id")
@click.option("--fullname", "-n", help="Copyright holder full name")
@click.option("--year", "-y", type=int, help="Copyright year")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing LICENSE file")
def license_create(license_id, fullname, year, force) -> None:
    """Create a LICENSE file with the specified license."""

    # Validate license ID
    is_valid, msg = validate_spdx_id(license_id)
    if not is_valid:
        # Check if it's a custom template
        manager = LicenseManager()
        if license_id not in manager.get_available_licenses():
            click.echo(click.style(f"✗ Invalid license ID: {msg}", fg="red"))
            return
        click.echo(click.style(f"⚠ Using custom template: {license_id}", fg="yellow"))

    # Get user info if not provided
    if not fullname:
        user_config = UserConfig()
        fullname = user_config.get("author_name")
        if not fullname:
            fullname = click.prompt(
                click.style("Copyright holder name", fg="cyan"), type=str
            )

    # Create license file
    if create_license_file(license_id, fullname, year, force):
        click.echo(click.style("✓ LICENSE file created successfully", fg="green"))
    else:
        click.echo(click.style("✗ Failed to create LICENSE file", fg="red"))


@license.command(name="update")
@click.option("--license", "-l", "license_id", help="New SPDX license ID")
@click.option("--fullname", "-n", help="New copyright holder full name")
@click.option("--year", "-y", type=int, help="New copyright year")
def license_update(license_id, fullname, year) -> None:
    """Update existing LICENSE file."""

    if not Path("LICENSE").exists():
        click.echo(
            click.style(
                "✗ No LICENSE file found. Use 'goal license create' first.", fg="red"
            )
        )
        return

    if update_license_file(license_id, fullname, year):
        click.echo(click.style("✓ LICENSE file updated successfully", fg="green"))
    else:
        click.echo(click.style("✗ Failed to update LICENSE file", fg="red"))


@license.command(name="validate")
def license_validate() -> None:
    """Validate the LICENSE file."""
    manager = LicenseManager()
    is_valid, issues = manager.validate_license_file()

    if is_valid:
        click.echo(click.style("✓ LICENSE file is valid", fg="green"))
    else:
        click.echo(click.style("✗ LICENSE file has issues:", fg="red", bold=True))
        for issue in issues:
            click.echo(f"  • {issue}")


@license.command(name="info")
@click.argument("license_id")
def license_info(license_id) -> None:
    """Show information about a license."""

    # Validate and get info
    is_valid, msg = validate_spdx_id(license_id)

    if not is_valid:
        click.echo(click.style(f"✗ {msg}", fg="red"))
        return

    info = get_license_info(license_id)
    if not info:
        click.echo(
            click.style(f"✗ No information available for {license_id}", fg="red")
        )
        return

    click.echo()
    click.echo(click.style(f"License: {info['name']}", fg="cyan", bold=True))
    click.echo(f"ID: {info['id']}")
    click.echo(f"Category: {info['category']}")

    if info["is_copyleft"]:
        click.echo(click.style("Type: Copyleft", fg="orange"))
    elif info["is_permissive"]:
        click.echo(click.style("Type: Permissive", fg="green"))

    if info["is_deprecated"]:
        click.echo(click.style("⚠ This license is deprecated", fg="yellow"))


@license.command(name="check")
@click.argument("license1")
@click.argument("license2")
def license_check(license1, license2) -> None:
    """Check compatibility between two licenses."""

    is_compatible, explanation = check_compatibility(license1, license2)

    if is_compatible:
        click.echo(click.style("✓ Compatible", fg="green", bold=True))
        click.echo(f"  {explanation}")
    else:
        click.echo(click.style("✗ Not Compatible", fg="red", bold=True))
        click.echo(f"  {explanation}")


@license.command(name="list")
@click.option("--custom", is_flag=True, help="Show only custom templates")
def license_list(custom) -> None:
    """List available license templates."""

    manager = LicenseManager()
    licenses = manager.get_available_licenses()

    if custom:
        # Filter to only custom templates
        builtin = set(manager.get_available_licenses()) - set(licenses)
        custom_licenses = [l for l in licenses if l not in builtin]
        if not custom_licenses:
            click.echo(click.style("No custom license templates found", fg="yellow"))
            return
        licenses = custom_licenses
        click.echo(click.style("Custom License Templates:", fg="cyan", bold=True))
    else:
        click.echo(click.style("Available License Templates:", fg="cyan", bold=True))

    click.echo()
    for license_id in sorted(licenses):
        is_valid, msg = validate_spdx_id(license_id)
        if is_valid:
            click.echo(f"  {click.style(license_id, fg='green')} - {msg}")
        else:
            click.echo(f"  {click.style(license_id, fg='cyan')} - Custom template")


@license.command(name="template")
@click.argument("license_id")
@click.option("--file", "-f", type=click.Path(exists=True), help="Template file path")
def license_template(license_id, file) -> None:
    """Add or show custom license templates."""

    manager = LicenseManager()

    if file:
        # Add custom template
        try:
            template = Path(file).read_text(encoding="utf-8")
            manager.add_custom_template(license_id, template)
        except Exception as e:
            click.echo(click.style(f"✗ Failed to read template file: {e}", fg="red"))
    else:
        # Show template
        template = manager.get_license_template(license_id)
        if template:
            click.echo()
            click.echo(click.style(f"Template for {license_id}:", fg="cyan", bold=True))
            click.echo("-" * 40)
            click.echo(template)
        else:
            click.echo(click.style(f"✗ No template found for {license_id}", fg="red"))


__all__ = [
    "license",
    "license_create",
    "license_update",
    "license_validate",
    "license_info",
    "license_check",
    "license_list",
    "license_template",
]
