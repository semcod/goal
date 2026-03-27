"""Post-commit manager for Goal."""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import click

from .actions import AVAILABLE_ACTIONS, PostCommitAction


class PostCommitManager:
    """Manages post-commit actions for Goal."""
    
    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize post-commit manager.
        
        Args:
            project_dir: Project directory (defaults to current directory)
        """
        self.project_dir = project_dir or Path.cwd()
        self.config_file = self.project_dir / 'goal.yaml'
    
    def get_config(self) -> List[Dict[str, Any]]:
        """Get post-commit actions configuration.
        
        Returns:
            List of action configurations
        """
        if not self.config_file.exists():
            return []
        
        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)
                if config and 'post_commit' in config:
                    return config['post_commit']
        except (yaml.YAMLError, IOError):
            pass
        
        return []
    
    def get_commit_info(self) -> Dict[str, str]:
        """Get information about the last commit.
        
        Returns:
            Dictionary with commit details
        """
        info = {
            'hash': '',
            'message': '',
            'author': '',
            'branch': '',
            'repository': str(self.project_dir.name),
        }
        
        try:
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, check=True
            )
            info['hash'] = result.stdout.strip()
            
            # Get commit message
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True, text=True, check=True
            )
            info['message'] = result.stdout.strip()
            
            # Get author
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%an <%ae>'],
                capture_output=True, text=True, check=True
            )
            info['author'] = result.stdout.strip()
            
            # Get branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, check=True
            )
            info['branch'] = result.stdout.strip()
            
        except subprocess.CalledProcessError:
            pass
        
        return info
    
    def run_actions(self) -> bool:
        """Run all configured post-commit actions.
        
        Returns:
            True if all actions succeeded
        """
        actions_config = self.get_config()
        if not actions_config:
            return True
        
        commit_info = self.get_commit_info()
        
        click.echo()
        click.echo(click.style("🚀 Running post-commit actions...", fg='cyan', bold=True))
        click.echo("-" * 40)
        
        all_succeeded = True
        
        for action_config in actions_config:
            action_type = action_config.get('type')
            
            if action_type not in AVAILABLE_ACTIONS:
                click.echo(click.style(f"⚠ Unknown action type: {action_type}", fg='yellow'))
                continue
            
            action_class = AVAILABLE_ACTIONS[action_type]
            action = action_class(action_config)
            
            if not action.validate_config():
                click.echo(click.style(f"✗ Invalid configuration for {action_type}", fg='red'))
                all_succeeded = False
                continue
            
            success = action.execute(commit_info)
            if not success:
                all_succeeded = False
        
        return all_succeeded
    
    def list_actions(self) -> None:
        """List configured post-commit actions."""
        actions = self.get_config()
        
        if not actions:
            click.echo(click.style("No post-commit actions configured", fg='yellow'))
            click.echo("Add actions to goal.yaml under 'post_commit:'")
            return
        
        click.echo()
        click.echo(click.style("Configured Post-Commit Actions:", fg='cyan', bold=True))
        click.echo("-" * 40)
        
        for i, action in enumerate(actions, 1):
            action_type = action.get('type', 'unknown')
            enabled = action.get('enabled', True)
            status = click.style('✓', fg='green') if enabled else click.style('✗', fg='red')
            click.echo(f"{i}. {status} {action_type}")
    
    def validate_actions(self) -> bool:
        """Validate all configured actions.
        
        Returns:
            True if all actions are valid
        """
        actions = self.get_config()
        
        if not actions:
            return True
        
        all_valid = True
        
        for action_config in actions:
            action_type = action_config.get('type')
            
            if action_type not in AVAILABLE_ACTIONS:
                click.echo(click.style(f"✗ Unknown action type: {action_type}", fg='red'))
                all_valid = False
                continue
            
            action_class = AVAILABLE_ACTIONS[action_type]
            action = action_class(action_config)
            
            if not action.validate_config():
                click.echo(click.style(f"✗ Invalid configuration for {action_type}", fg='red'))
                all_valid = False
            else:
                click.echo(click.style(f"✓ {action_type} configuration valid", fg='green'))
        
        return all_valid


def run_post_commit_actions(project_dir: Optional[Path] = None) -> bool:
    """Run post-commit actions.
    
    Args:
        project_dir: Project directory (defaults to current directory)
        
    Returns:
        True if all actions succeeded
    """
    manager = PostCommitManager(project_dir)
    return manager.run_actions()
