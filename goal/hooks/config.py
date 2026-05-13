"""Configuration management for pre-commit hooks."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


DEFAULT_HOOK_CONFIG = {
    "file_validation": {
        "enabled": True,
        "max_file_size_mb": 10,
    },
    "token_detection": {
        "enabled": True,
        "patterns": [
            "ghp_[a-zA-Z0-9]{36}",  # GitHub Personal Access Token
            "gho_[a-zA-Z0-9]{36}",  # GitHub OAuth Token
            "ghu_[a-zA-Z0-9]{36}",  # GitHub User Token
            "AKIA[0-9A-Z]{16}",  # AWS Access Key
            "sk_live_[a-zA-Z0-9]{24}",  # Stripe Live Key
            "xoxb-[a-zA-Z0-9-]{10,48}",  # Slack Bot Token
            "xoxp-[a-zA-Z0-9-]{10,48}",  # Slack User Token
            "glpat-[a-zA-Z0-9-]{20}",  # GitLab Personal Token
            r"Bearer\s+[a-zA-Z0-9_\-\.]+",  # Bearer tokens
            r"Token\s+[a-zA-Z0-9_\-\.]+",  # API tokens
        ],
    },
    "dot_folder_detection": {
        "enabled": True,
        "safe_files": [
            ".gitignore",
            ".github",
            ".editorconfig",
            ".gitattributes",
            ".gitlab-ci.yml",
        ],
    },
}


def get_hook_config(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Get hook configuration.

    Args:
        project_dir: Project directory (defaults to current directory)

    Returns:
        Hook configuration dictionary
    """
    project_dir = project_dir or Path.cwd()
    config_file = project_dir / "goal.yaml"

    config = DEFAULT_HOOK_CONFIG.copy()

    if config_file.exists():
        try:
            with open(config_file) as f:
                goal_config = yaml.safe_load(f)
                if goal_config and "advanced" in goal_config:
                    advanced = goal_config["advanced"]
                    if "file_validation" in advanced:
                        config["file_validation"].update(advanced["file_validation"])
                    if "token_detection" in advanced:
                        config["token_detection"].update(advanced["token_detection"])
        except (yaml.YAMLError, IOError):
            pass

    return config


def create_precommit_config(
    project_dir: Optional[Path] = None, include_goal: bool = True
) -> str:
    """Create .pre-commit-config.yaml content.

    Args:
        project_dir: Project directory
        include_goal: Include Goal validation hook

    Returns:
        YAML content as string
    """
    project_dir = project_dir or Path.cwd()

    config = {"repos": []}

    # Add Goal hook
    if include_goal:
        hook_script = project_dir / ".goal" / "pre-commit-hook.py"
        config["repos"].append(
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "goal-validation",
                        "name": "Goal validation",
                        "entry": str(hook_script),
                        "language": "system",
                        "always_run": True,
                        "pass_filenames": False,
                    }
                ],
            }
        )

    return yaml.dump(config, default_flow_style=False)
