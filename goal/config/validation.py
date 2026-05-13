"""Configuration validation for Goal.

This module provides validation for goal.yaml configuration files,
ensuring that configurations are valid, complete, and follow best practices.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

import click


class ConfigValidationError(Exception):
    """Error raised when configuration validation fails."""

    def __init__(self, errors: List[str], warnings: List[str] = None):
        self.errors = errors or []
        self.warnings = warnings or []
        nl = "\n"
        message = f"Configuration validation failed:\n{nl.join(f'  ❌ {e}' for e in self.errors)}"
        if self.warnings:
            message += f"\n\nWarnings:\n{nl.join(f'  ⚠️  {w}' for w in self.warnings)}"
        super().__init__(message)


class ConfigValidator:
    """Validates Goal configuration files."""

    # Valid project types
    VALID_PROJECT_TYPES = {
        "python",
        "nodejs",
        "rust",
        "go",
        "ruby",
        "php",
        "dotnet",
        "java",
        "generic",
    }

    # Valid commit types
    VALID_COMMIT_TYPES = {"auto", "conventional", "simple", "semantic"}

    # Valid version strategies
    VALID_VERSION_STRATEGIES = {"auto", "manual", "semantic", "calver", "semver"}

    # Valid bump strategies
    VALID_BUMP_STRATEGIES = {"auto", "manual", "conventional"}

    def __init__(self, config: Dict[str, Any]):
        """Initialize validator with configuration dict."""
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, strict: bool = False) -> Tuple[bool, List[str], List[str]]:
        """Validate the configuration.

        Args:
            strict: If True, warnings are treated as errors

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Validate required sections
        self._validate_required_sections()

        # Validate project section
        self._validate_project_section()

        # Validate git section
        self._validate_git_section()

        # Validate versioning section
        self._validate_versioning_section()

        # Validate publishing section
        self._validate_publishing_section()

        # Validate advanced section
        self._validate_advanced_section()

        # Check for unknown keys
        self._validate_no_unknown_keys()

        is_valid = len(self.errors) == 0
        if strict and self.warnings:
            is_valid = False
            self.errors.extend(self.warnings)
            self.warnings = []

        return is_valid, self.errors, self.warnings

    def _validate_required_sections(self):
        """Validate that required sections exist."""
        required_sections = ["project", "git", "versioning"]
        for section in required_sections:
            if section not in self.config:
                self.errors.append(f"Missing required section: '{section}'")

    def _validate_project_section(self):
        """Validate project configuration."""
        project = self.config.get("project", {})

        # Validate project name
        if not project.get("name"):
            self.warnings.append("Project name is not set (will be auto-detected)")
        elif not isinstance(project.get("name"), str):
            self.errors.append("Project name must be a string")
        elif len(project.get("name", "")) > 100:
            self.warnings.append("Project name is very long (>100 chars)")

        # Validate project type
        project_type = project.get("type")
        if project_type:
            if isinstance(project_type, str):
                if project_type not in self.VALID_PROJECT_TYPES:
                    self.errors.append(
                        f"Invalid project type: '{project_type}'. "
                        f"Valid types: {', '.join(sorted(self.VALID_PROJECT_TYPES))}"
                    )
            elif isinstance(project_type, list):
                invalid_types = set(project_type) - self.VALID_PROJECT_TYPES
                if invalid_types:
                    self.errors.append(
                        f"Invalid project types: {', '.join(invalid_types)}. "
                        f"Valid types: {', '.join(sorted(self.VALID_PROJECT_TYPES))}"
                    )
            else:
                self.errors.append("Project type must be a string or list of strings")

        # Validate description
        description = project.get("description")
        if description and not isinstance(description, str):
            self.errors.append("Project description must be a string")

    def _validate_git_section(self):
        """Validate git configuration."""
        git = self.config.get("git", {})

        # Validate commit configuration
        commit = git.get("commit", {})

        # Validate commit type
        commit_type = commit.get("type")
        if commit_type and commit_type not in self.VALID_COMMIT_TYPES:
            self.errors.append(
                f"Invalid commit type: '{commit_type}'. "
                f"Valid types: {', '.join(sorted(self.VALID_COMMIT_TYPES))}"
            )

        # Validate scope
        scope = commit.get("scope")
        if scope and not isinstance(scope, str):
            self.errors.append("Commit scope must be a string")

        # Validate require_ticket
        require_ticket = commit.get("require_ticket")
        if require_ticket is not None and not isinstance(require_ticket, bool):
            self.errors.append("require_ticket must be a boolean (true/false)")

        # Validate remote configuration
        remote = git.get("remote", {})

        # Validate auto_push
        auto_push = remote.get("auto_push")
        if auto_push is not None and not isinstance(auto_push, bool):
            self.errors.append("auto_push must be a boolean (true/false)")

        # Validate branch naming
        branch_prefix = remote.get("branch_prefix")
        if branch_prefix:
            if not isinstance(branch_prefix, str):
                self.errors.append("branch_prefix must be a string")
            elif not re.match(r"^[a-z]+/$", branch_prefix):
                self.warnings.append(
                    f"Branch prefix '{branch_prefix}' doesn't follow conventional naming (e.g., 'feature/')"
                )

        # Validate hooks
        hooks = git.get("hooks", {})
        if not isinstance(hooks, dict):
            self.errors.append("hooks must be a dictionary")

    def _validate_versioning_section(self):
        """Validate versioning configuration."""
        versioning = self.config.get("versioning", {})

        # Validate strategy
        strategy = versioning.get("strategy")
        if strategy and strategy not in self.VALID_VERSION_STRATEGIES:
            self.errors.append(
                f"Invalid version strategy: '{strategy}'. "
                f"Valid strategies: {', '.join(sorted(self.VALID_VERSION_STRATEGIES))}"
            )

        # Validate bump_strategy
        bump_strategy = versioning.get("bump_strategy")
        if bump_strategy and bump_strategy not in self.VALID_BUMP_STRATEGIES:
            self.errors.append(
                f"Invalid bump strategy: '{bump_strategy}'. "
                f"Valid strategies: {', '.join(sorted(self.VALID_BUMP_STRATEGIES))}"
            )

        # Validate files
        files = versioning.get("files")
        if files:
            if not isinstance(files, list):
                self.errors.append("versioning.files must be a list")
            else:
                for i, f in enumerate(files):
                    if not isinstance(f, str):
                        self.errors.append(
                            f"versioning.files[{i}] must be a string path"
                        )

        # Validate changelog
        changelog = versioning.get("changelog")
        if changelog is not None:
            if not isinstance(changelog, bool):
                self.errors.append("versioning.changelog must be a boolean")

        # Validate tag_format
        tag_format = versioning.get("tag_format")
        if tag_format:
            if not isinstance(tag_format, str):
                self.errors.append("tag_format must be a string")
            elif "{version}" not in tag_format:
                self.warnings.append(
                    f"tag_format '{tag_format}' doesn't contain '{version}' placeholder"
                )

    def _validate_publishing_section(self):
        """Validate publishing configuration."""
        publishing = self.config.get("publishing", {})

        # Validate enabled
        enabled = publishing.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            self.errors.append("publishing.enabled must be a boolean")

        # Validate registries
        registries = publishing.get("registries", [])
        if registries:
            if not isinstance(registries, list):
                self.errors.append("publishing.registries must be a list")
            else:
                valid_registries = {
                    "pypi",
                    "npm",
                    "crates.io",
                    "rubygems",
                    "packagist",
                    "nuget",
                    "maven",
                }
                for registry in registries:
                    if registry not in valid_registries:
                        self.warnings.append(
                            f"Unknown registry: '{registry}'. "
                            f"Known registries: {', '.join(sorted(valid_registries))}"
                        )

        # Validate dry_run
        dry_run = publishing.get("dry_run")
        if dry_run is not None and not isinstance(dry_run, bool):
            self.errors.append("publishing.dry_run must be a boolean")

    def _check_bool(self, section: Dict, key: str, label: str = "") -> None:
        """Append an error if *key* exists in *section* but is not a bool."""
        val = section.get(key)
        if val is not None and not isinstance(val, bool):
            self.errors.append(f"{label or key} must be a boolean")

    def _check_numeric(
        self,
        section: Dict,
        key: str,
        lo: float = None,
        hi: float = None,
        warn_lo: float = None,
        warn_hi: float = None,
    ) -> None:
        """Validate a numeric field, appending errors/warnings as needed."""
        val = section.get(key)
        if val is None:
            return
        if not isinstance(val, (int, float)):
            self.errors.append(f"{key} must be a number")
            return
        if lo is not None and hi is not None and not (lo <= val <= hi):
            self.errors.append(f"{key} must be between {lo} and {hi}")
        elif (
            warn_lo is not None
            and warn_hi is not None
            and not (warn_lo <= val <= warn_hi)
        ):
            self.warnings.append(
                f"{key} ({val}) seems unusual (typical: {warn_lo}-{warn_hi})"
            )

    def _validate_advanced_section(self):
        """Validate advanced configuration."""
        advanced = self.config.get("advanced", {})

        file_validation = advanced.get("file_validation", {})
        if file_validation:
            self._check_numeric(
                file_validation, "max_file_size_mb", warn_lo=0.1, warn_hi=1000
            )
            self._check_bool(file_validation, "block_large_files")
            self._check_bool(file_validation, "detect_api_tokens")

        tests = advanced.get("tests", {})
        if tests:
            self._check_bool(tests, "require_tests")
            self._check_numeric(tests, "coverage_threshold", lo=0, hi=100)

        recovery = advanced.get("recovery", {})
        if recovery:
            self._check_bool(recovery, "enabled", "recovery.enabled")
            self._check_bool(recovery, "auto_recover", "recovery.auto_recover")

    def _validate_no_unknown_keys(self):
        """Check for unknown/deprecated keys in configuration."""

        def check_keys(config: Dict, valid_keys: set, path: str = ""):
            for key in config:
                current_path = f"{path}.{key}" if path else key
                if key not in valid_keys:
                    self.warnings.append(f"Unknown configuration key: '{current_path}'")

        # Top-level keys
        valid_top_keys = {"project", "git", "versioning", "publishing", "advanced"}
        check_keys(self.config, valid_top_keys)

        # Project keys
        if "project" in self.config:
            valid_project_keys = {"name", "type", "description", "author", "license"}
            check_keys(self.config["project"], valid_project_keys, "project")

        # Git keys
        if "git" in self.config:
            valid_git_keys = {"commit", "remote", "hooks"}
            check_keys(self.config["git"], valid_git_keys, "git")

            if "commit" in self.config.get("git", {}):
                valid_commit_keys = {"type", "scope", "require_ticket", "template"}
                check_keys(
                    self.config["git"]["commit"], valid_commit_keys, "git.commit"
                )

            if "remote" in self.config.get("git", {}):
                valid_remote_keys = {"auto_push", "branch_prefix"}
                check_keys(
                    self.config["git"]["remote"], valid_remote_keys, "git.remote"
                )

        # Versioning keys
        if "versioning" in self.config:
            valid_version_keys = {
                "strategy",
                "bump_strategy",
                "files",
                "changelog",
                "tag_format",
                "initial_version",
            }
            check_keys(self.config["versioning"], valid_version_keys, "versioning")

        # Publishing keys
        if "publishing" in self.config:
            valid_pub_keys = {"enabled", "registries", "dry_run"}
            check_keys(self.config["publishing"], valid_pub_keys, "publishing")


def validate_config_file(
    config_path: Optional[Union[str, Path]] = None, strict: bool = False
) -> bool:
    """Validate a goal.yaml configuration file.

    Args:
        config_path: Path to config file. If None, looks for goal.yaml
        strict: If True, treat warnings as errors

    Returns:
        True if valid, False otherwise
    """
    from goal.config import GoalConfig

    config_manager = GoalConfig(config_path)

    if not config_manager.exists():
        click.echo(
            click.style("❌ Configuration file not found: ", fg="red")
            + f"{config_manager.config_path}"
        )
        click.echo(
            click.style(
                "   Run 'goal init' to create a configuration file.", fg="yellow"
            )
        )
        return False

    try:
        config = config_manager.load()
    except Exception as e:
        click.echo(click.style("❌ Failed to load configuration: ", fg="red") + str(e))
        return False

    validator = ConfigValidator(config)
    is_valid, errors, warnings = validator.validate(strict=strict)

    # Display results
    if is_valid:
        click.echo(click.style("✅ Configuration is valid!", fg="green", bold=True))
        if warnings and not strict:
            click.echo(click.style("\n⚠️  Warnings:", fg="yellow"))
            for warning in warnings:
                click.echo(f"  • {warning}")
        return True
    else:
        click.echo(
            click.style("❌ Configuration validation failed!", fg="red", bold=True)
        )
        click.echo(click.style("\nErrors:", fg="red"))
        for error in errors:
            click.echo(f"  • {error}")
        if warnings and not strict:
            click.echo(click.style("\nWarnings:", fg="yellow"))
            for warning in warnings:
                click.echo(f"  • {warning}")
        return False


def validate_config_interactive(config_path: Optional[Union[str, Path]] = None) -> bool:
    """Interactively validate and optionally fix configuration.

    Args:
        config_path: Path to config file

    Returns:
        True if valid or fixed, False otherwise
    """
    from goal.config import GoalConfig

    config_manager = GoalConfig(config_path)

    if not config_manager.exists():
        click.echo(click.style("Configuration file not found.", fg="red"))
        if click.confirm("Would you like to create a new configuration?"):
            from goal.config import init_config

            init_config()
            return True
        return False

    config = config_manager.load()
    validator = ConfigValidator(config)
    is_valid, errors, warnings = validator.validate(strict=False)

    if is_valid and not warnings:
        click.echo(click.style("✅ Configuration looks good!", fg="green"))
        return True

    if warnings:
        click.echo(click.style("\n⚠️  The following issues were found:", fg="yellow"))
        for warning in warnings:
            click.echo(f"  • {warning}")

        if click.confirm("\nWould you like to auto-fix these issues?"):
            # Apply fixes
            fixed_config = _auto_fix_config(config, warnings)
            config_manager.save(fixed_config)
            click.echo(click.style("✅ Configuration updated!", fg="green"))
            return True

    if errors:
        click.echo(
            click.style("\n❌ The following errors must be fixed manually:", fg="red")
        )
        for error in errors:
            click.echo(f"  • {error}")
        return False

    return True


def _auto_fix_config(config: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
    """Auto-fix configuration warnings.

    Args:
        config: Current configuration
        warnings: List of warnings to fix

    Returns:
        Fixed configuration
    """
    import copy

    fixed = copy.deepcopy(config)

    for warning in warnings:
        if "Project name is not set" in warning:
            # Will be auto-detected on next load
            pass
        elif (
            "doesn't follow conventional naming" in warning
            and "Branch prefix" in warning
        ):
            # Suggest conventional prefix
            if "git" not in fixed:
                fixed["git"] = {}
            if "remote" not in fixed["git"]:
                fixed["git"]["remote"] = {}
            fixed["git"]["remote"]["branch_prefix"] = "feature/"
        elif "doesn't contain '{version}'" in warning:
            # Fix tag format
            if "versioning" not in fixed:
                fixed["versioning"] = {}
            fixed["versioning"]["tag_format"] = "v{version}"

    return fixed
