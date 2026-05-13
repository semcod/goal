"""Project configuration and scaffolding - extracted from project_bootstrap.py."""

import os
from pathlib import Path
from typing import Optional

import click

from goal.bootstrap.templates import PROJECT_TEMPLATES
from goal.bootstrap.detector import guess_package_name


def scaffold_test_file(project_dir: Path, project_type: str) -> bool:
    """Create a sample test file if none exist."""
    cfg = PROJECT_TEMPLATES.get(project_type)
    if not cfg:
        return True

    # Check if any test files already exist
    has_tests = False
    for test_dir_name in cfg.test_dirs:
        test_dir = project_dir / test_dir_name
        if test_dir.exists():
            for pattern in cfg.test_patterns:
                if list(test_dir.glob(pattern)):
                    has_tests = True
                    break
            if has_tests:
                break

    if has_tests:
        return True  # Tests exist, nothing to do

    # No tests found, scaffold one
    template = cfg.scaffold_test
    if not template:
        return True  # No template for this project type

    package_name = guess_package_name(project_dir, project_type)
    test_content = template.format(package_name=package_name)

    # Write to first test dir
    test_dir = project_dir / cfg.test_dirs[0]
    test_dir.mkdir(exist_ok=True)

    if project_type == "python":
        test_file = test_dir / f"test_{package_name}.py"
    elif project_type == "nodejs":
        test_file = test_dir / f"{package_name}.test.js"
    elif project_type == "rust":
        test_file = project_dir / "src" / "lib.rs"
    elif project_type == "go":
        test_file = test_dir / f"{package_name}_test.go"
    else:
        return True  # Unknown type

    if test_file.exists():
        return True

    test_file.write_text(test_content)
    click.echo(
        click.style(
            f"  ✓ Created sample test: {test_file.relative_to(project_dir)}", fg="green"
        )
    )
    return True


def _find_python_bin(project_dir: Path) -> str:
    """Return the best python binary path for a project directory."""
    # Check common venv names in order of preference
    for venv_name in [".venv", "venv", "env"]:
        venv_python = project_dir / venv_name / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
    # Check active virtualenv
    venv_env = os.environ.get("VIRTUAL_ENV")
    if venv_env:
        candidate = Path(venv_env) / "bin" / "python"
        if candidate.exists():
            return str(candidate)
    # sys.executable
    import sys

    return sys.executable


def _read_openrouter_api_key(env_file: Path) -> str:
    """Extract OPENROUTER_API_KEY from a .env file."""
    try:
        content = env_file.read_text(encoding="utf-8")
    except Exception:
        return ""

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()

        key_name, sep, value = stripped.partition("=")
        if not sep or key_name.strip() != "OPENROUTER_API_KEY":
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1].strip()
        return value

    return ""


def _find_openrouter_api_key(project_dir: Path) -> tuple[Optional[Path], str]:
    """Find an OpenRouter API key in the environment or any ancestor .env file."""
    env_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env_key:
        return None, env_key

    search_dir = project_dir.resolve()
    while True:
        candidate = search_dir / ".env"
        if candidate.exists():
            api_key = _read_openrouter_api_key(candidate)
            if api_key:
                return candidate, api_key

        if search_dir == search_dir.parent:
            break
        search_dir = search_dir.parent

    return None, ""


def _find_git_root(project_dir: Path) -> Optional[Path]:
    """Find the git repository root for a project directory."""
    current = project_dir.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None
