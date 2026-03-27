"""Wizard command for guided setup."""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

import click

from goal.cli import main
from goal.config import ensure_config, GoalConfig
from goal.user_config import (
    UserConfig, 
    get_git_user_name, 
    get_git_user_email,
    prompt_for_license
)


@main.command()
@click.option('--reset', is_flag=True, help='Reset and reconfigure everything')
@click.option('--skip-git', is_flag=True, help='Skip git repository setup')
@click.option('--skip-user', is_flag=True, help='Skip user configuration')
@click.option('--skip-project', is_flag=True, help='Skip project configuration')
def wizard(reset, skip_git, skip_user, skip_project):
    """Interactive wizard for complete Goal setup."""
    
    click.echo()
    click.echo(click.style("🧙‍♂️  Welcome to the Goal Setup Wizard!", fg='cyan', bold=True))
    click.echo(click.style("=" * 70, fg='cyan'))
    click.echo()
    click.echo("This wizard will guide you through setting up:")
    click.echo("  • Git repository configuration")
    click.echo("  • User preferences (name, email, license)")
    click.echo("  • Project-specific settings")
    click.echo("  • Build and deployment strategies")
    click.echo()
    
    if not click.confirm(click.style("Continue with setup?", fg='cyan'), default=True):
        click.echo("Setup cancelled.")
        return
    
    # Step 1: Git Repository Setup
    if not skip_git:
        _setup_git_repository()
    
    # Step 2: User Configuration
    if not skip_user:
        _setup_user_config(reset)
    
    # Step 3: Project Configuration
    if not skip_project:
        _setup_project_config()
    
    # Step 4: Final Summary
    _show_setup_summary()
    
    click.echo()
    click.echo(click.style("✨ Setup complete! You're ready to use Goal.", fg='green', bold=True))
    click.echo()
    click.echo(click.style("Next steps:", fg='cyan', bold=True))
    click.echo("  1. Make some changes to your code")
    click.echo("  2. Run: goal commit")
    click.echo("  3. Review and confirm the generated commit message")
    click.echo()


def _setup_git_repository():
    """Setup or verify git repository."""
    click.echo()
    click.echo(click.style("📁 Step 1: Git Repository Setup", fg='blue', bold=True))
    click.echo("-" * 40)
    
    # Check if we're in a git repo
    git_root = _find_git_root()
    
    if git_root:
        click.echo(f"✓ Already in a git repository: {click.style(str(git_root), fg='green')}")
        
        # Check for remote
        try:
            result = subprocess.run(
                ['git', 'remote', '-v'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                click.echo("✓ Git remotes configured:")
                for line in result.stdout.strip().split('\n'):
                    click.echo(f"  {line}")
            else:
                click.echo(click.style("⚠ No git remotes configured", fg='yellow'))
                if click.confirm(click.style("Add a remote now?", fg='cyan'), default=False):
                    _add_git_remote()
        except Exception as e:
            click.echo(click.style(f"⚠ Could not check git remotes: {e}", fg='yellow'))
    else:
        click.echo(click.style("⚠ Not in a git repository", fg='yellow'))
        if click.confirm(click.style("Initialize a git repository?", fg='cyan'), default=True):
            try:
                subprocess.run(['git', 'init'], check=True, capture_output=True)
                click.echo(click.style("✓ Git repository initialized", fg='green'))
            except Exception as e:
                click.echo(click.style(f"✗ Failed to initialize git repository: {e}", fg='red'))
                return
            
            # Optionally add remote
            if click.confirm(click.style("Add a remote repository?", fg='cyan'), default=False):
                _add_git_remote()


def _find_git_root() -> Optional[Path]:
    """Find the git repository root."""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return None


def _add_git_remote():
    """Add a git remote."""
    remote_name = click.prompt(
        click.style("Remote name", fg='cyan'),
        default='origin'
    )
    
    remote_url = click.prompt(
        click.style("Remote URL", fg='cyan'),
        type=str
    )
    
    try:
        result = subprocess.run(['git', 'remote', 'add', remote_name, remote_url], capture_output=True, check=False)
        if result.returncode == 0:
            click.echo(click.style(f"✓ Added remote {remote_name} -> {remote_url}", fg='green'))
        else:
            click.echo(click.style(f"✗ Failed to add remote: {result.stderr.decode()}", fg='red'))
    except Exception as e:
        click.echo(click.style(f"✗ Failed to add remote: {e}", fg='red'))


def _setup_user_config(reset: bool):
    """Setup user configuration."""
    click.echo()
    click.echo(click.style("👤 Step 2: User Configuration", fg='blue', bold=True))
    click.echo("-" * 40)
    
    config = UserConfig()
    
    if config.is_initialized() and not reset:
        click.echo("✓ User configuration already exists:")
        click.echo(f"  Name: {click.style(config.get('author_name'), fg='green')}")
        click.echo(f"  Email: {click.style(config.get('author_email'), fg='green')}")
        click.echo(f"  License: {click.style(config.get('license_name', 'Not set'), fg='green')}")
        
        if not click.confirm(click.style("Update user configuration?", fg='cyan'), default=False):
            return
    
    # Get git user info
    git_name = get_git_user_name()
    git_email = get_git_user_email()
    
    click.echo()
    if git_name:
        click.echo(f"✓ Detected git name: {click.style(git_name, fg='green')}")
    if git_email:
        click.echo(f"✓ Detected git email: {click.style(git_email, fg='green')}")
    
    # Prompt for name if not detected or if updating
    if not git_name or reset:
        git_name = click.prompt(
            click.style("Author name", fg='cyan'),
            default=git_name or "Unknown Author"
        )
    
    # Prompt for email if not detected or if updating
    if not git_email or reset:
        git_email = click.prompt(
            click.style("Author email", fg='cyan'),
            default=git_email or "unknown@example.com"
        )
    
    # License selection
    click.echo()
    click.echo("Select your preferred license for new projects:")
    license_info = prompt_for_license()
    
    # Save configuration
    config.set('author_name', git_name)
    config.set('author_email', git_email)
    config.set('license', license_info['id'])
    config.set('license_name', license_info['name'])
    config.set('license_classifier', license_info['classifier'])
    
    click.echo(click.style("✓ User configuration saved", fg='green'))


def _setup_project_config():
    """Setup project-specific configuration."""
    click.echo()
    click.echo(click.style("⚙️  Step 3: Project Configuration", fg='blue', bold=True))
    click.echo("-" * 40)
    
    # Ensure goal.yaml exists
    config = ensure_config(auto_update=False)
    
    if config.exists():
        click.echo("✓ Found existing goal.yaml")
        if not click.confirm(click.style("Update project configuration?", fg='cyan'), default=False):
            return
    
    # Show detected project info
    detected = {
        'name': config.get('project.name'),
        'type': config.get('project.type', []),
        'description': config.get('project.description'),
        'version': config.get('project.version')
    }
    
    click.echo()
    click.echo("Detected project information:")
    for key, value in detected.items():
        if value:
            if isinstance(value, list):
                value = ', '.join(value)
            click.echo(f"  {key.title()}: {click.style(value, fg='green')}")
    
    click.echo()
    
    # Allow user to modify project settings
    if click.confirm(click.style("Customize project settings?", fg='cyan'), default=False):
        # Project name
        name = click.prompt(
            click.style("Project name", fg='cyan'),
            default=detected['name'] or Path.cwd().name
        )
        config.set('project.name', name)
        
        # Project description
        description = click.prompt(
            click.style("Project description", fg='cyan'),
            default=detected['description'] or ""
        )
        config.set('project.description', description)
        
        # Versioning strategy
        click.echo()
        click.echo("Versioning strategy:")
        click.echo("  1. Semantic Versioning (1.2.3)")
        click.echo("  2. Calendar Versioning (2024.03.15)")
        click.echo("  3. Date Versioning (20240315)")
        
        strategy_choice = click.prompt(
            click.style("Choose strategy", fg='cyan'),
            type=click.Choice(['1', '2', '3']),
            default='1'
        )
        
        strategy_map = {'1': 'semver', '2': 'calver', '3': 'date'}
        config.set('versioning.strategy', strategy_map[strategy_choice])
        
        # Commit strategy
        click.echo()
        click.echo("Commit message strategy:")
        click.echo("  1. Conventional Commits (feat, fix, docs, etc.)")
        click.echo("  2. Semantic Commits (with scope)")
        click.echo("  3. Custom format")
        
        commit_choice = click.prompt(
            click.style("Choose strategy", fg='cyan'),
            type=click.Choice(['1', '2', '3']),
            default='1'
        )
        
        commit_map = {'1': 'conventional', '2': 'semantic', '3': 'custom'}
        config.set('git.commit.strategy', commit_map[commit_choice])
        
        # Auto-update changelog
        auto_changelog = click.confirm(
            click.style("Automatically update CHANGELOG.md?", fg='cyan'),
            default=True
        )
        config.set('changelog.auto_update', auto_changelog)
    
    # Save configuration
    config.save()
    click.echo(click.style("✓ Project configuration saved to goal.yaml", fg='green'))


def _show_setup_summary():
    """Show a summary of the configuration."""
    click.echo()
    click.echo(click.style("📋 Setup Summary", fg='blue', bold=True))
    click.echo("=" * 40)
    
    # User config
    user_config = UserConfig()
    if user_config.is_initialized():
        click.echo()
        click.echo(click.style("User Configuration:", fg='cyan', bold=True))
        click.echo(f"  Author: {user_config.get('author_name')} <{user_config.get('author_email')}>")
        click.echo(f"  License: {user_config.get('license_name')}")
    
    # Project config
    project_config = ensure_config()
    if project_config.exists():
        click.echo()
        click.echo(click.style("Project Configuration:", fg='cyan', bold=True))
        click.echo(f"  Name: {project_config.get('project.name')}")
        if project_config.get('project.description'):
            click.echo(f"  Description: {project_config.get('project.description')}")
        click.echo(f"  Versioning: {project_config.get('versioning.strategy')}")
        click.echo(f"  Commits: {project_config.get('git.commit.strategy')}")
    
    # Git status
    git_root = _find_git_root()
    if git_root:
        click.echo()
        click.echo(click.style("Git Repository:", fg='cyan', bold=True))
        click.echo(f"  Root: {git_root}")
        
        # Check if there are uncommitted changes
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                click.echo(click.style("  Status: Has uncommitted changes", fg='yellow'))
            else:
                click.echo(click.style("  Status: Clean", fg='green'))
        except subprocess.CalledProcessError:
            pass


__all__ = ['wizard']
