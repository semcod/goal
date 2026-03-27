"""Pre-commit hooks manager for Goal.

This module provides functionality to install, manage, and run pre-commit hooks
that integrate with Goal's validation system.
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import click

from ..validators.file_validator import (
    validate_files,
    ValidationError,
    FileSizeError,
    TokenDetectedError,
    DotFolderError
)
from ..git_ops import get_staged_files, run_git


class HooksManager:
    """Manages pre-commit hooks for Goal."""
    
    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize hooks manager.
        
        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.precommit_file = self.project_dir / '.pre-commit-config.yaml'
        self.goal_hook_script = self.project_dir / '.goal' / 'pre-commit-hook.py'
        
    def is_precommit_installed(self) -> bool:
        """Check if pre-commit is installed."""
        try:
            result = subprocess.run(['pre-commit', '--version'], 
                                  capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def is_hooks_configured(self) -> bool:
        """Check if Goal hooks are configured."""
        return self.precommit_file.exists() and self.goal_hook_script.exists()
    
    def install_precommit(self) -> bool:
        """Install pre-commit if not already installed."""
        if self.is_precommit_installed():
            click.echo(click.style("✓ pre-commit is already installed", fg='green'))
            return True
        
        click.echo("Installing pre-commit...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pre-commit'], 
                         check=True)
            click.echo(click.style("✓ pre-commit installed successfully", fg='green'))
            return True
        except subprocess.CalledProcessError:
            click.echo(click.style("✗ Failed to install pre-commit", fg='red'))
            click.echo("Please install it manually: pip install pre-commit")
            return False
    
    def create_hook_script(self) -> None:
        """Create the Goal hook script."""
        hook_dir = self.goal_hook_script.parent
        hook_dir.mkdir(exist_ok=True)
        
        hook_content = '''#!/usr/bin/env python3
"""Goal pre-commit hook.

This script runs Goal's validation checks before commit.
"""

import sys
from pathlib import Path

# Add goal to Python path
goal_path = Path(__file__).parent.parent
sys.path.insert(0, str(goal_path))

from goal.hooks.manager import HooksManager

def main():
    """Run pre-commit validation."""
    manager = HooksManager()
    success = manager.run_validation()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
'''
        
        self.goal_hook_script.write_text(hook_content)
        self.goal_hook_script.chmod(0o755)
    
    def create_precommit_config(self, force: bool = False) -> bool:
        """Create .pre-commit-config.yaml with Goal hooks.
        
        Args:
            force: Overwrite existing config
            
        Returns:
            True if config was created
        """
        if self.precommit_file.exists() and not force:
            click.echo(click.style("⚠ .pre-commit-config.yaml already exists", fg='yellow'))
            click.echo("Use --force to overwrite")
            return False
        
        config = {
            'repos': [
                {
                    'repo': 'local',
                    'hooks': [
                        {
                            'id': 'goal-validation',
                            'name': 'Goal validation',
                            'entry': str(self.goal_hook_script),
                            'language': 'system',
                            'always_run': True,
                            'pass_filenames': False
                        }
                    ]
                }
            ]
        }
        
        with open(self.precommit_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        click.echo(click.style(f"✓ Created {self.precommit_file}", fg='green'))
        return True
    
    def install_hooks(self, force: bool = False) -> bool:
        """Install Goal pre-commit hooks.
        
        Args:
            force: Reinstall even if already installed
            
        Returns:
            True if installation succeeded
        """
        click.echo(click.style("🔧 Installing Goal pre-commit hooks...", fg='cyan'))
        
        # Install pre-commit if needed
        if not self.install_precommit():
            return False
        
        # Create hook script
        self.create_hook_script()
        click.echo(click.style(f"✓ Created hook script", fg='green'))
        
        # Create config
        if not self.create_precommit_config(force):
            return False
        
        # Install hooks
        try:
            subprocess.run(['pre-commit', 'install'], check=True, cwd=self.project_dir)
            click.echo(click.style("✓ Pre-commit hooks installed", fg='green'))
            click.echo()
            click.echo(click.style("Hooks will now run before each commit:", fg='cyan'))
            click.echo("  • File size validation")
            click.echo("  • API token detection")
            click.echo("  • Dot folder detection")
            return True
        except subprocess.CalledProcessError:
            click.echo(click.style("✗ Failed to install pre-commit hooks", fg='red'))
            return False
    
    def uninstall_hooks(self) -> bool:
        """Uninstall Goal pre-commit hooks.
        
        Returns:
            True if uninstallation succeeded
        """
        click.echo(click.style("🗑️  Uninstalling Goal pre-commit hooks...", fg='cyan'))
        
        # Uninstall hooks
        try:
            subprocess.run(['pre-commit', 'uninstall'], check=True, cwd=self.project_dir)
        except subprocess.CalledProcessError:
            pass  # Hooks might not be installed
        
        # Remove config
        if self.precommit_file.exists():
            self.precommit_file.unlink()
            click.echo(click.style(f"✓ Removed {self.precommit_file}", fg='green'))
        
        # Remove hook script
        if self.goal_hook_script.exists():
            self.goal_hook_script.unlink()
            click.echo(click.style(f"✓ Removed hook script", fg='green'))
        
        click.echo(click.style("✓ Pre-commit hooks uninstalled", fg='green'))
        return True
    
    def run_validation(self, files: Optional[List[str]] = None) -> bool:
        """Run Goal validation checks.
        
        Args:
            files: List of files to validate (defaults to staged files)
            
        Returns:
            True if all validations passed
        """
        if files is None:
            files = get_staged_files()
        
        if not files:
            return True
        
        try:
            validate_files(files)
            return True
        except ValidationError as e:
            click.echo(click.style(f"✗ Validation Error: {e}", fg='red'))
            return False
    
    def run_hooks(self, all_files: bool = False) -> bool:
        """Run pre-commit hooks manually.
        
        Args:
            all_files: Run on all files instead of just staged
            
        Returns:
            True if all hooks passed
        """
        if not self.is_hooks_configured():
            click.echo(click.style("⚠ Goal hooks are not installed", fg='yellow'))
            click.echo("Run 'goal hooks install' to set them up")
            return False
        
        click.echo(click.style("🔍 Running pre-commit hooks...", fg='cyan'))
        
        try:
            cmd = ['pre-commit', 'run', '--all-files'] if all_files else ['pre-commit', 'run']
            subprocess.run(cmd, check=True, cwd=self.project_dir)
            click.echo(click.style("✓ All hooks passed", fg='green'))
            return True
        except subprocess.CalledProcessError:
            click.echo(click.style("✗ Some hooks failed", fg='red'))
            return False
    
    def status(self) -> None:
        """Show hooks status."""
        click.echo()
        click.echo(click.style("Pre-commit Hooks Status:", fg='cyan', bold=True))
        click.echo("-" * 30)
        
        # Check pre-commit installation
        if self.is_precommit_installed():
            result = subprocess.run(['pre-commit', '--version'], 
                                  capture_output=True, text=True)
            click.echo(f"pre-commit: {click.style(result.stdout.strip(), fg='green')}")
        else:
            click.echo(f"pre-commit: {click.style('Not installed', fg='red')}")
        
        # Check Goal hooks
        if self.is_hooks_configured():
            click.echo(f"Goal hooks: {click.style('Configured', fg='green')}")
        else:
            click.echo(f"Goal hooks: {click.style('Not configured', fg='yellow')}")


def install_hooks(project_dir: Optional[Path] = None, force: bool = False) -> bool:
    """Install Goal pre-commit hooks.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        force: Reinstall even if already installed
        
    Returns:
        True if installation succeeded
    """
    manager = HooksManager(project_dir)
    return manager.install_hooks(force)


def uninstall_hooks(project_dir: Optional[Path] = None) -> bool:
    """Uninstall Goal pre-commit hooks.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        True if uninstallation succeeded
    """
    manager = HooksManager(project_dir)
    return manager.uninstall_hooks()


def run_hooks(project_dir: Optional[Path] = None, all_files: bool = False) -> bool:
    """Run pre-commit hooks manually.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        all_files: Run on all files instead of just staged
        
    Returns:
        True if all hooks passed
    """
    manager = HooksManager(project_dir)
    return manager.run_hooks(all_files)
