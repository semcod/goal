"""Validation rule manager for Goal."""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import click

from goal.git_ops import get_staged_files, get_diff_stats
from .rules import AVAILABLE_RULES


class ValidationRuleManager:
    """Manages custom validation rules for Goal."""

    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize validation rule manager.

        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.config_file = self.project_dir / "goal.yaml"

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get custom validation rules from configuration.

        Returns:
            List of rule configurations
        """
        if not self.config_file.exists():
            return []

        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)
                if config and "validation_rules" in config:
                    return config["validation_rules"]
        except (yaml.YAMLError, IOError):
            pass

        return []

    def get_validation_context(self) -> Dict[str, Any]:
        """Get context for validation.

        Returns:
            Dictionary with validation context
        """
        context = {
            "files": get_staged_files(),
            "stats": get_diff_stats(),
            "message": "",
            "hash": "",
        }

        # Get last commit message
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                check=True,
            )
            context["message"] = result.stdout.strip()

            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            context["hash"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

        return context

    def validate_all(self) -> bool:
        """Run all custom validation rules.

        Returns:
            True if all validations passed
        """
        rules_config = self.get_rules()
        if not rules_config:
            return True

        context = self.get_validation_context()

        click.echo()
        click.echo(
            click.style("🔍 Running custom validation rules...", fg="cyan", bold=True)
        )
        click.echo("-" * 40)

        all_passed = True

        for rule_config in rules_config:
            if not rule_config.get("enabled", True):
                continue

            rule_type = rule_config.get("type")
            rule_name = rule_config.get("name", rule_type)

            if rule_type not in AVAILABLE_RULES:
                click.echo(
                    click.style(f"⚠ Unknown rule type: {rule_type}", fg="yellow")
                )
                continue

            rule_class = AVAILABLE_RULES[rule_type]
            rule = rule_class(rule_config)

            if not rule.validate_config():
                click.echo(
                    click.style(f"✗ {rule_name}: Invalid configuration", fg="red")
                )
                all_passed = False
                continue

            success, error = rule.validate(context)

            if success:
                click.echo(click.style(f"✓ {rule_name}", fg="green"))
            else:
                click.echo(click.style(f"✗ {rule_name}: {error}", fg="red"))
                all_passed = False

        return all_passed

    def list_rules(self) -> None:
        """List configured validation rules."""
        rules = self.get_rules()

        if not rules:
            click.echo(
                click.style("No custom validation rules configured", fg="yellow")
            )
            click.echo("Add rules to goal.yaml under 'validation_rules:'")
            return

        click.echo()
        click.echo(click.style("Configured Validation Rules:", fg="cyan", bold=True))
        click.echo("-" * 40)

        for i, rule in enumerate(rules, 1):
            rule_type = rule.get("type", "unknown")
            rule_name = rule.get("name", rule_type)
            enabled = rule.get("enabled", True)
            status = (
                click.style("✓", fg="green") if enabled else click.style("✗", fg="red")
            )
            click.echo(f"{i}. {status} {rule_name} ({rule_type})")

    def validate_config(self) -> bool:
        """Validate all rule configurations.

        Returns:
            True if all rules are valid
        """
        rules = self.get_rules()

        if not rules:
            click.echo(click.style("No validation rules to validate", fg="yellow"))
            return True

        click.echo()
        click.echo(click.style("Validating rule configurations...", fg="cyan"))

        all_valid = True

        for rule_config in rules:
            rule_type = rule_config.get("type")
            rule_name = rule_config.get("name", rule_type)

            if rule_type not in AVAILABLE_RULES:
                click.echo(
                    click.style(
                        f"✗ {rule_name}: Unknown rule type '{rule_type}'", fg="red"
                    )
                )
                all_valid = False
                continue

            rule_class = AVAILABLE_RULES[rule_type]
            rule = rule_class(rule_config)

            if rule.validate_config():
                click.echo(click.style(f"✓ {rule_name}: Valid", fg="green"))
            else:
                click.echo(
                    click.style(f"✗ {rule_name}: Invalid configuration", fg="red")
                )
                all_valid = False

        return all_valid


def run_custom_validations(project_dir: Optional[Path] = None) -> bool:
    """Run custom validation rules.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        True if all validations passed
    """
    manager = ValidationRuleManager(project_dir)
    return manager.validate_all()
