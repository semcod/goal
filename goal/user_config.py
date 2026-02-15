"""User configuration management for goal.

Stores user preferences in ~/.goal including:
- Git author information (name, email)
- Default license preference
- Other user-specific settings
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

import click


# Available licenses with their identifiers
AVAILABLE_LICENSES = {
    '1': {'id': 'Apache-2.0', 'name': 'Apache License 2.0', 'classifier': 'License :: OSI Approved :: Apache Software License'},
    '2': {'id': 'MIT', 'name': 'MIT License', 'classifier': 'License :: OSI Approved :: MIT License'},
    '3': {'id': 'GPL-3.0', 'name': 'GNU General Public License v3.0', 'classifier': 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'},
    '4': {'id': 'BSD-3-Clause', 'name': 'BSD 3-Clause License', 'classifier': 'License :: OSI Approved :: BSD License'},
    '5': {'id': 'GPL-2.0', 'name': 'GNU General Public License v2.0', 'classifier': 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'},
    '6': {'id': 'LGPL-3.0', 'name': 'GNU Lesser General Public License v3.0', 'classifier': 'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'},
    '7': {'id': 'AGPL-3.0', 'name': 'GNU Affero General Public License v3.0', 'classifier': 'License :: OSI Approved :: GNU Affero General Public License v3'},
    '8': {'id': 'MPL-2.0', 'name': 'Mozilla Public License 2.0', 'classifier': 'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)'},
}


class UserConfig:
    """Manages user-specific configuration stored in ~/.goal"""
    
    def __init__(self):
        self.config_path = Path.home() / '.goal'
        self.config: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """Load configuration from ~/.goal file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
        else:
            self.config = {}
    
    def _save(self):
        """Save configuration to ~/.goal file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            click.echo(click.style(f"Warning: Could not save user config: {e}", fg='yellow'))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save."""
        self.config[key] = value
        self._save()
    
    def is_initialized(self) -> bool:
        """Check if user configuration is initialized."""
        return 'author_name' in self.config and 'author_email' in self.config and 'license' in self.config


def get_git_user_name() -> Optional[str]:
    """Get git user.name from git config."""
    try:
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_user_email() -> Optional[str]:
    """Get git user.email from git config."""
    try:
        result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def prompt_for_license() -> Dict[str, str]:
    """Interactive prompt for license selection."""
    click.echo()
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo(click.style("  📄 License Selection", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo()
    click.echo("Please select your preferred default license:")
    click.echo()
    
    for num, info in sorted(AVAILABLE_LICENSES.items()):
        click.echo(f"  {click.style(num, fg='green', bold=True)}. {click.style(info['name'], fg='white', bold=True)}")
    
    click.echo()
    
    while True:
        choice = click.prompt(
            click.style("Enter your choice", fg='cyan'),
            type=str,
            default='1'
        ).strip()
        
        if choice in AVAILABLE_LICENSES:
            selected = AVAILABLE_LICENSES[choice]
            click.echo()
            click.echo(click.style(f"✓ Selected: {selected['name']} ({selected['id']})", fg='green', bold=True))
            return selected
        else:
            click.echo(click.style(f"Invalid choice '{choice}'. Please enter a number from 1-{len(AVAILABLE_LICENSES)}.", fg='red'))


def initialize_user_config(force: bool = False) -> UserConfig:
    """Initialize user configuration interactively if not already done.
    
    Args:
        force: Force re-initialization even if config exists
    
    Returns:
        UserConfig instance
    """
    config = UserConfig()
    
    if config.is_initialized() and not force:
        return config
    
    click.echo()
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo(click.style("  🎯 Goal - First Time Setup", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo()
    
    # Get git user information
    git_name = get_git_user_name()
    git_email = get_git_user_email()
    
    if git_name:
        click.echo(f"✓ Detected git user.name: {click.style(git_name, fg='green', bold=True)}")
    if git_email:
        click.echo(f"✓ Detected git user.email: {click.style(git_email, fg='green', bold=True)}")
    
    if not git_name or not git_email:
        click.echo()
        click.echo(click.style("⚠ Git user information not configured!", fg='yellow', bold=True))
        click.echo("Please configure git first:")
        click.echo()
        if not git_name:
            click.echo("  git config --global user.name \"Your Name\"")
        if not git_email:
            click.echo("  git config --global user.email \"your.email@example.com\"")
        click.echo()
        
        if not git_name:
            git_name = click.prompt(
                click.style("Enter your name", fg='cyan'),
                type=str,
                default="Unknown Author"
            )
        
        if not git_email:
            git_email = click.prompt(
                click.style("Enter your email", fg='cyan'),
                type=str,
                default="unknown@example.com"
            )
    
    # Prompt for license
    license_info = prompt_for_license()
    
    # Save configuration
    config.set('author_name', git_name)
    config.set('author_email', git_email)
    config.set('license', license_info['id'])
    config.set('license_name', license_info['name'])
    config.set('license_classifier', license_info['classifier'])
    
    click.echo()
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo(click.style("✓ Configuration saved to ~/.goal", fg='green', bold=True))
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo()
    click.echo("Your preferences:")
    click.echo(f"  Author: {click.style(git_name, fg='white', bold=True)} <{click.style(git_email, fg='white', bold=True)}>")
    click.echo(f"  License: {click.style(license_info['name'], fg='white', bold=True)}")
    click.echo()
    click.echo(click.style("💡 Tip: Run 'goal config' to view or change these settings anytime", fg='cyan'))
    click.echo()
    
    return config


def get_user_config() -> UserConfig:
    """Get user configuration, initializing if necessary.
    
    Returns:
        UserConfig instance
    """
    config = UserConfig()
    if not config.is_initialized():
        return initialize_user_config()
    return config


def show_user_config():
    """Display current user configuration."""
    config = UserConfig()
    
    if not config.is_initialized():
        click.echo(click.style("No user configuration found. Run any goal command to initialize.", fg='yellow'))
        return
    
    click.echo()
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo(click.style("  📋 Goal User Configuration", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo()
    click.echo(f"Config file: {click.style(str(config.config_path), fg='white', bold=True)}")
    click.echo()
    click.echo("Current settings:")
    click.echo(f"  Author name:  {click.style(config.get('author_name', 'Not set'), fg='green', bold=True)}")
    click.echo(f"  Author email: {click.style(config.get('author_email', 'Not set'), fg='green', bold=True)}")
    click.echo(f"  License:      {click.style(config.get('license_name', 'Not set'), fg='green', bold=True)} ({config.get('license', 'Not set')})")
    click.echo()
    click.echo(click.style("💡 Tip: Run 'goal config --reset' to reconfigure", fg='cyan'))
    click.echo()
