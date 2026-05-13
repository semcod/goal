"""Pyproject dev-dependency injection and costs-related env templates."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import click

logger = logging.getLogger(__name__)

_REQUIRED_DEV_DEPS = (
    ("goal", '"goal>=2.1.0"'),
    ("costs", '"costs>=0.1.20"'),
    ("pfix", '"pfix>=0.1.60"'),
)


def _find_dep_list_end(content: str, start_idx: int) -> int:
    """Find the matching closing bracket for a dependency list."""
    bracket_count = 1
    in_string = False
    escape_next = False
    quote_char = None

    for i in range(start_idx, len(content)):
        char = content[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char in ('"', "'") and not in_string:
            in_string = True
            quote_char = char
        elif char == quote_char and in_string:
            in_string = False
            quote_char = None
        elif not in_string:
            if char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
                if bracket_count == 0:
                    return i

    return -1


def _try_merge_optional_dev_deps(content: str) -> tuple[str, bool]:
    """Strategy 1: [project.optional-dependencies] dev = [...]"""
    if (
        "[project.optional-dependencies]" not in content
        or "dev = [" not in content.lower()
    ):
        return content, False
    dev_match = re.search(r"(dev\s*=\s*\[)", content, flags=re.IGNORECASE)
    if not dev_match:
        return content, False
    match_start = dev_match.start()
    start = dev_match.end()
    end = _find_dep_list_end(content, start)
    if end == -1:
        return content, False
    section_start = dev_match.group(1)
    existing = content[start:end]
    new_content = _add_deps_to_section_match(section_start, existing)
    old_content = content[match_start : end + 1]
    if new_content == old_content:
        return content, False
    return content[:match_start] + new_content + content[end + 1 :], True


def _try_merge_hatch_default_deps(content: str) -> tuple[str, bool]:
    """Strategy 2: [tool.hatch.envs.default] dependencies = [...]"""
    if "[tool.hatch.envs.default]" not in content or "dependencies = [" not in content:
        return content, False
    dep_match = re.search(r"(dependencies\s*=\s*\[)", content, flags=re.IGNORECASE)
    if not dep_match:
        return content, False
    match_start = dep_match.start()
    start = dep_match.end()
    end = _find_dep_list_end(content, start)
    if end == -1:
        return content, False
    section_start = dep_match.group(1)
    existing = content[start:end]
    new_content = _add_deps_to_section_match(section_start, existing)
    old_content = content[match_start : end + 1]
    if new_content == old_content:
        return content, False
    return content[:match_start] + new_content + content[end + 1 :], True


def _try_add_deps(content: str) -> tuple[str, bool]:
    """Try adding missing dev deps to pyproject.toml content.

    Returns (updated_content, changed).
    """
    if all(name in content.lower() for name, _ in _REQUIRED_DEV_DEPS):
        return content, False

    content, changed = _try_merge_optional_dev_deps(content)
    if changed:
        return content, True
    return _try_merge_hatch_default_deps(content)


def _add_deps_to_section_match(
    section_start: str, existing: str, required_deps=_REQUIRED_DEV_DEPS
) -> str:
    """Add missing deps to a TOML section."""
    to_add = [spec for name, spec in required_deps if name not in existing.lower()]
    if not to_add:
        return f"{section_start}{existing}]"

    existing_stripped = existing.rstrip()
    indent = "    "
    for line in existing.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith('"'):
            indent = line[: len(line) - len(stripped)] or indent
            break
    new_entries = "\n".join(f"{indent}{dep}," for dep in to_add)
    if existing_stripped and not existing_stripped.endswith(","):
        existing_stripped += ","
    return f"{section_start}{existing_stripped}\n{new_entries}\n]"


_COSTS_CONFIG_TEMPLATE = """\n[tool.costs]
# AI Cost tracking configuration
badge = true
update_readme = true
readme_path = "README.md"
default_model = "openrouter/qwen/qwen3-coder-next"
analysis_mode = "byok"
full_history = true
max_commits = 500

# Cost thresholds for badge colors (USD)
badge_color_thresholds = { low = 1.0, medium = 5.0, high = 10.0, critical = 50.0 }
"""


def _ensure_costs_config(project_dir: Path) -> bool:
    """Ensure [tool.costs] section exists in pyproject.toml.

    Also adds goal and costs as dev dependencies.

    Returns True if config was added or already exists.
    """
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists():
        return False

    content = pyproject.read_text(encoding="utf-8")

    content, deps_updated = _try_add_deps(content)
    if deps_updated:
        pyproject.write_text(content, encoding="utf-8")
        click.echo(
            click.style(
                "  ✓ Added goal, costs and pfix to dev dependencies", fg="green"
            )
        )

    if "[tool.costs]" in content:
        return True

    try:
        with open(pyproject, "a", encoding="utf-8") as f:
            f.write(_COSTS_CONFIG_TEMPLATE)
        click.echo(click.style("  ✓ Added [tool.costs] to pyproject.toml", fg="green"))
        return True
    except OSError as e:
        logger.warning("Failed to append [tool.costs] config to %s: %s", pyproject, e)
        click.echo(click.style(f"  ⚠ Could not add costs config: {e}", fg="yellow"))
        return False


def _ensure_env_template(project_dir: Path) -> bool:
    """Ensure .env file exists with API key template.

    Returns True if .env was created or already exists.
    """
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"

    if env_file.exists():
        return True

    env_template = """# AI Cost Tracking Configuration
# Get your API key from: https://openrouter.ai/keys

# OpenRouter API Key (required for real cost calculation)
OPENROUTER_API_KEY=sk-or-v1-...

# Default AI model for cost analysis
LLM_MODEL=openrouter/qwen/qwen3-coder-next

# Optional: SaaS token for managed billing
# SAAS_TOKEN=your-saas-token
"""

    try:
        env_file.write_text(env_template, encoding="utf-8")

        if not env_example.exists():
            env_example.write_text(env_template, encoding="utf-8")

        gitignore = project_dir / ".gitignore"
        if gitignore.exists():
            gitignore_content = gitignore.read_text(encoding="utf-8")
            if ".env" not in gitignore_content:
                with open(gitignore, "a", encoding="utf-8") as f:
                    f.write("\n# Environment variables\n.env\n")
        else:
            gitignore.write_text(".env\n.env.local\n", encoding="utf-8")

        click.echo(
            click.style(
                "  ✓ Created .env template (add your OPENROUTER_API_KEY)", fg="green"
            )
        )
        return True
    except OSError as e:
        logger.warning("Failed to create .env template in %s: %s", project_dir, e)
        click.echo(click.style(f"  ⚠ Could not create .env: {e}", fg="yellow"))
        return False
