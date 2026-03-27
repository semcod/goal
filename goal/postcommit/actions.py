"""Post-commit action implementations."""

import os
import subprocess
import platform
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import click


class PostCommitAction(ABC):
    """Base class for post-commit actions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def execute(self, commit_info: Dict[str, str]) -> bool:
        """Execute the action.
        
        Args:
            commit_info: Dictionary with commit details (hash, message, author, etc.)
            
        Returns:
            True if execution succeeded
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get action name."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate action configuration."""
        pass


class NotificationAction(PostCommitAction):
    """Send desktop notification after commit."""
    
    def get_name(self) -> str:
        return "notification"
    
    def validate_config(self) -> bool:
        return True
    
    def execute(self, commit_info: Dict[str, str]) -> bool:
        title = self.config.get('title', 'Goal Commit')
        message = self.config.get('message', f"Committed: {commit_info.get('message', '')[:50]}...")
        
        system = platform.system()
        
        try:
            if system == 'Darwin':  # macOS
                subprocess.run([
                    'osascript', '-e',
                    f'display notification "{message}" with title "{title}"'
                ], check=True, capture_output=True)
            elif system == 'Linux':
                # Try notify-send
                try:
                    subprocess.run([
                        'notify-send', title, message
                    ], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback to console notification
                    click.echo(click.style(f"📢 {title}: {message}", fg='cyan'))
            elif system == 'Windows':
                # Windows notification (would need additional library)
                click.echo(click.style(f"📢 {title}: {message}", fg='cyan'))
            else:
                click.echo(click.style(f"📢 {title}: {message}", fg='cyan'))
            
            return True
        except Exception as e:
            click.echo(click.style(f"⚠ Notification failed: {e}", fg='yellow'))
            return False


class WebhookAction(PostCommitAction):
    """Send webhook POST request after commit."""
    
    def get_name(self) -> str:
        return "webhook"
    
    def validate_config(self) -> bool:
        return 'url' in self.config
    
    def execute(self, commit_info: Dict[str, str]) -> bool:
        try:
            import requests
        except ImportError:
            click.echo(click.style("⚠ requests library not installed, webhook skipped", fg='yellow'))
            return False
        
        url = self.config.get('url')
        if not url:
            click.echo(click.style("✗ Webhook URL not configured", fg='red'))
            return False
        
        headers = self.config.get('headers', {})
        payload = {
            'commit_hash': commit_info.get('hash'),
            'commit_message': commit_info.get('message'),
            'author': commit_info.get('author'),
            'branch': commit_info.get('branch'),
            'repository': commit_info.get('repository'),
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            click.echo(click.style(f"✓ Webhook sent to {url}", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"✗ Webhook failed: {e}", fg='red'))
            return False


class ScriptAction(PostCommitAction):
    """Run custom script after commit."""
    
    def get_name(self) -> str:
        return "script"
    
    def validate_config(self) -> bool:
        return 'command' in self.config
    
    def execute(self, commit_info: Dict[str, str]) -> bool:
        command = self.config.get('command')
        if not command:
            click.echo(click.style("✗ Script command not configured", fg='red'))
            return False
        
        # Set environment variables with commit info
        env = os.environ.copy()
        env['GOAL_COMMIT_HASH'] = commit_info.get('hash', '')
        env['GOAL_COMMIT_MESSAGE'] = commit_info.get('message', '')
        env['GOAL_COMMIT_AUTHOR'] = commit_info.get('author', '')
        env['GOAL_COMMIT_BRANCH'] = commit_info.get('branch', '')
        
        working_dir = self.config.get('working_dir', '.')
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.config.get('timeout', 60)
            )
            
            if result.returncode == 0:
                click.echo(click.style(f"✓ Script executed: {command}", fg='green'))
                if result.stdout:
                    click.echo(result.stdout)
                return True
            else:
                click.echo(click.style(f"✗ Script failed: {command}", fg='red'))
                if result.stderr:
                    click.echo(result.stderr)
                return False
        except subprocess.TimeoutExpired:
            click.echo(click.style(f"✗ Script timed out: {command}", fg='red'))
            return False
        except Exception as e:
            click.echo(click.style(f"✗ Script error: {e}", fg='red'))
            return False


class GitPushAction(PostCommitAction):
    """Automatically push after commit."""
    
    def get_name(self) -> str:
        return "git_push"
    
    def validate_config(self) -> bool:
        return True
    
    def execute(self, commit_info: Dict[str, str]) -> bool:
        remote = self.config.get('remote', 'origin')
        branch = commit_info.get('branch')
        
        if not branch:
            # Get current branch
            try:
                result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                branch = result.stdout.strip()
            except subprocess.CalledProcessError:
                click.echo(click.style("✗ Could not determine current branch", fg='red'))
                return False
        
        try:
            subprocess.run(
                ['git', 'push', remote, branch],
                check=True,
                capture_output=True
            )
            click.echo(click.style(f"✓ Pushed to {remote}/{branch}", fg='green'))
            return True
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"✗ Push failed: {e}", fg='red'))
            return False


# Registry of available actions
AVAILABLE_ACTIONS = {
    'notification': NotificationAction,
    'webhook': WebhookAction,
    'script': ScriptAction,
    'git_push': GitPushAction,
}
