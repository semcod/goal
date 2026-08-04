"""Publishing functions - extracted from cli.py."""

import glob
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, List

import click
import yaml

from goal.git_ops import run_command_tee
from goal.cli.version import PROJECT_TYPES
from goal.toml_validation import validate_project_toml_files
from goal.publish.github_fallback import (
    get_github_release_config,
    github_fallback_actionable,
    is_pypi_blocked,
    try_github_fallback,
)


def makefile_has_target(target: str) -> bool:
    """Check if Makefile has a specific target."""
    makefile = Path("Makefile")
    if not makefile.exists() or not makefile.is_file():
        return False
    try:
        content = makefile.read_text(errors="ignore")
    except Exception:
        return False
    import re

    return re.search(rf"^\s*{re.escape(target)}\s*:", content, re.MULTILINE) is not None


# Matches a `python`/`python3` command token, but never a `python` that is part
# of a path such as ``adapters/python/...`` (negative lookbehind on path chars).
_PYTHON_INTERP_RE = re.compile(r"(?<![\w./\-])python3?(?=\s)")

# Matches a leading ``cd <dir> &&`` so we can resolve build/publish artifacts
# relative to the directory the command actually runs in (monorepo subdirs).
_CD_PREFIX_RE = re.compile(r"^\s*cd\s+([^\s&;|]+)\s*&&")


def _replace_python_interpreter(cmd: str, python_bin: str) -> str:
    """Replace the python interpreter token in a command without touching paths."""
    return _PYTHON_INTERP_RE.sub(lambda _m: python_bin, cmd)


def _command_workdir(cmd: str) -> Path:
    """Return the working directory a command runs in, honoring a leading ``cd``."""
    match = _CD_PREFIX_RE.match(cmd or "")
    return Path(match.group(1)) if match else Path(".")


def _dist_dir_for(cmd: str) -> Path:
    """Return the dist/ directory relative to the command's working directory."""
    return _command_workdir(cmd) / "dist"


def _get_project_strategy(config: Any, project_type: str) -> dict:
    """Get the configured strategy for a project type, if available."""
    if config is None:
        return {}

    if hasattr(config, "get_strategy"):
        try:
            return config.get_strategy(project_type) or {}
        except Exception:
            return {}

    if isinstance(config, dict):
        return config.get("strategies", {}).get(project_type, {}) or {}

    return {}


def _get_configured_project_types(config: Any) -> List[str]:
    """Get project types from the active configuration without default fallbacks."""
    if config is None:
        return []

    if isinstance(config, dict):
        raw_config = config
    else:
        config_path = getattr(config, "config_path", None)
        if not config_path:
            return []

        config_file = Path(config_path)
        if not config_file.exists():
            return []

        try:
            raw_config = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
        except Exception:
            return []

        if not isinstance(raw_config, dict):
            return []

    project_config = raw_config.get("project", {})
    project_types = (
        project_config.get("type", []) if isinstance(project_config, dict) else []
    )

    if isinstance(project_types, str):
        return [project_types]

    if isinstance(project_types, list):
        return [ptype for ptype in project_types if isinstance(ptype, str)]

    return []


def _get_python_bin() -> str:
    """Get the Python binary to use for publishing."""
    import os
    import sys

    # Prefer the active virtualenv (e.g. source ../urisys/.venv/bin/activate)
    active_venv = os.environ.get("VIRTUAL_ENV", "").strip()
    if active_venv:
        active_python = Path(active_venv) / "bin" / "python"
        if active_python.exists():
            return str(active_python.resolve())

    # Check for venv in current directory (priority order: .venv, venv, env)
    for venv_name in [".venv", "venv", "env"]:
        venv_python = Path(".") / venv_name / "bin" / "python"
        if venv_python.exists():
            return str(venv_python.resolve())

    return sys.executable


def _ensure_publish_deps(python_bin: str) -> bool:
    """Ensure build and twine are installed for publishing."""
    # Check if build is available
    result = subprocess.run(
        [python_bin, "-m", "build", "--help"], capture_output=True, text=True
    )
    if result.returncode != 0:
        click.echo(click.style("  Installing build module...", fg="cyan"))
        install_result = subprocess.run(
            [python_bin, "-m", "pip", "install", "--quiet", "build"],
            capture_output=True,
            text=True,
            cwd=str(Path(".")),
        )
        if install_result.returncode != 0:
            click.echo(
                click.style(
                    f"  ✗ Failed to install build module: {install_result.stderr}",
                    fg="red",
                )
            )
            return False
        click.echo(click.style("  ✓ build installed", fg="green"))

    # Check if twine is available
    result = subprocess.run(
        [python_bin, "-m", "twine", "--help"], capture_output=True, text=True
    )
    if result.returncode != 0:
        click.echo(click.style("  Installing twine...", fg="cyan"))
        install_result = subprocess.run(
            [python_bin, "-m", "pip", "install", "--quiet", "twine"],
            capture_output=True,
            text=True,
            cwd=str(Path(".")),
        )
        if install_result.returncode != 0:
            click.echo(
                click.style(
                    f"  ✗ Failed to install twine: {install_result.stderr}", fg="red"
                )
            )
            return False
        click.echo(click.style("  ✓ twine installed", fg="green"))

    return True


def _read_pyproject_package_name() -> str:
    """Return the distribution name from pyproject.toml, if available."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        return ""

    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError:
        return ""

    try:
        import tomllib

        data = tomllib.loads(content)
        return data.get("project", {}).get("name", "") or ""
    except Exception:
        match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
        return match.group(1) if match else ""


def _read_setup_py_package_name() -> str:
    """Return the distribution name from setup.py, if available."""
    setup_py = Path("setup.py")
    if not setup_py.exists():
        return ""

    try:
        content = setup_py.read_text(encoding="utf-8")
    except OSError:
        return ""

    match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
    return match.group(1) if match else ""


def _read_python_package_name() -> str:
    """Return the Python distribution name from supported metadata files."""
    return _read_pyproject_package_name() or _read_setup_py_package_name()


def _normalized_name_candidates(package_name: str) -> list[str]:
    if not package_name:
        return []
    candidates = {
        package_name,
        package_name.replace("-", "_"),
        package_name.replace("_", "-"),
    }
    return sorted(candidates)


def _python_artifacts_for_version(
    version: str, package_name: str = "", dist_dir: Path = Path("dist")
) -> list[Path]:
    """Return built Python artifacts that exactly match the requested version."""
    dist = dist_dir
    if not dist.exists():
        return []

    suffixes = (".whl", ".tar.gz", ".zip")
    if package_name:
        patterns = [
            f"{candidate}-{version}*"
            for candidate in _normalized_name_candidates(package_name)
        ]
    else:
        patterns = [f"*-{version}*"]

    artifacts: list[Path] = []
    for pattern in patterns:
        for path in dist.glob(pattern):
            if path.is_file() and path.name.endswith(suffixes):
                artifacts.append(path)

    return sorted(set(artifacts))


def _format_artifact_args(artifacts: list[Path]) -> str:
    return " ".join(shlex.quote(str(path)) for path in artifacts)


def _resolve_python_publish_cmd(publish_cmd: str, version: str) -> str:
    """Use exact built artifacts for the requested version.

    This avoids uploading stale files from ``dist/*`` and fixes stale project-name
    globs such as ``dist/oldname-{version}*`` when the current metadata produces
    a different distribution name.
    """
    publish_cmd = publish_cmd.replace("{version}", version)
    # Capture the full artifact path token, including any directory prefix such
    # as ``adapters/python/dist/...`` so monorepo subdir paths survive intact.
    match = re.search(r"\S*dist/[^\s'\"]+", publish_cmd)
    if not match:
        return publish_cmd

    pattern = match.group(0)
    dist_dir = Path(pattern).parent
    project_name = _read_python_package_name()
    artifacts = _python_artifacts_for_version(version, project_name, dist_dir)
    if not artifacts:
        artifacts = _python_artifacts_for_version(version, "", dist_dir)
    if not artifacts:
        return publish_cmd

    corrected = _format_artifact_args(artifacts)
    if sorted(glob.glob(pattern)) == [str(path) for path in artifacts]:
        return publish_cmd

    click.echo(
        click.style(
            f"  Corrected publish pattern: {pattern} -> {corrected}",
            fg="yellow",
        )
    )
    return publish_cmd.replace(pattern, corrected)


def _run_python_build(build_cmd: str, python_bin: str) -> bool:
    if not build_cmd:
        return True

    build_cmd = _replace_python_interpreter(build_cmd, python_bin)
    click.echo(click.style(f"  Build command: {build_cmd}", fg="cyan"))
    build_result = run_command_tee(build_cmd)
    if build_result.returncode == 0:
        return True

    click.echo(
        click.style(
            f"  Build failed with exit code {build_result.returncode}", fg="red"
        ),
        err=True,
    )
    if build_result.stderr:
        click.echo(
            click.style(f"  stderr: {build_result.stderr}", fg="red"), err=True
        )
    if build_result.stdout:
        click.echo(
            click.style(f"  stdout: {build_result.stdout}", fg="yellow"),
            err=True,
        )
    return False


def _available_dist_artifacts(dist_dir: Path = Path("dist")) -> str:
    artifacts = sorted(path.name for path in dist_dir.glob("*") if path.is_file())
    return ", ".join(artifacts) if artifacts else "(none)"


def _ensure_python_artifacts_for_version(
    version: str, build_cmd: str, python_bin: str
) -> bool:
    dist_dir = _dist_dir_for(build_cmd)
    package_name = _read_python_package_name()
    if _python_artifacts_for_version(
        version, package_name, dist_dir
    ) or _python_artifacts_for_version(version, "", dist_dir):
        return True

    click.echo(
        click.style(
            f"  No Python dist artifacts found for version {version}. "
            "Re-syncing version files and rebuilding...",
            fg="yellow",
        )
    )

    try:
        from goal.cli.version_sync import sync_all_versions

        updated = sync_all_versions(version)
        if updated:
            click.echo(
                click.style(
                    f"  Re-synced version in: {', '.join(updated)}",
                    fg="cyan",
                )
            )
    except Exception as exc:
        click.echo(
            click.style(f"  Version re-sync failed: {exc}", fg="red"),
            err=True,
        )
        return False

    if not _run_python_build(build_cmd, python_bin):
        return False

    if _python_artifacts_for_version(
        version, package_name, dist_dir
    ) or _python_artifacts_for_version(version, "", dist_dir):
        return True

    click.echo(
        click.style(
            f"  Build did not produce artifacts for version {version}. "
            f"Available dist artifacts: {_available_dist_artifacts(dist_dir)}",
            fg="red",
        ),
        err=True,
    )
    return False


def _prepare_python_publish(strategy: dict, version: str) -> tuple:
    """Build the Python project and return (publish_cmd, ok). Returns ('', False) on failure."""
    python_bin = _get_python_bin()
    click.echo(click.style(f"  Using Python: {python_bin}", fg="cyan"))
    if not _ensure_publish_deps(python_bin):
        return "", False

    build_cmd = strategy.get("build", "") or "python -m build"
    if not _run_python_build(build_cmd, python_bin):
        return "", False

    if not _ensure_python_artifacts_for_version(version, build_cmd, python_bin):
        return "", False

    return python_bin, True


_RETRY_DELAYS = [60, 120, 300]


def _read_nodejs_package_name() -> str:
    """Return the npm package name from package.json."""
    try:
        import json
        with open("package.json") as f:
            return (json.load(f).get("name") or "").strip()
    except Exception:
        return ""


def _nodejs_artifacts_for_version(version: str) -> list[Path]:
    """Return npm pack artifacts matching the requested version."""
    dist = Path("dist")
    if not dist.exists():
        return []
    patterns = [f"*-{version}.tgz"]
    artifacts: list[Path] = []
    for pattern in patterns:
        for path in dist.glob(pattern):
            if path.is_file():
                artifacts.append(path)
    return sorted(set(artifacts))


def _is_rate_limited(result) -> bool:
    """Check if a publish result indicates PyPI rate limiting (HTTP 429)."""
    combined = f"{result.stdout or ''}\n{result.stderr or ''}"
    return "429" in combined and "Too Many Requests" in combined


def _run_publish_command(
    ptype: str,
    publish_cmd: str,
    *,
    version: str | None = None,
    config: Any = None,
) -> bool:
    """Execute the publish command and handle output. Returns True on success.

    When PyPI returns a blocking error (429, 403, permission), and GitHub fallback
    is enabled in goal.yaml, deploys to GitHub Releases immediately without
    waiting through PyPI retry backoff.
    """
    click.echo(f"  Publishing {ptype}: {publish_cmd}")
    gh_config = get_github_release_config(config) if ptype in ("python", "nodejs") else None
    package_name = (
        _read_python_package_name()
        if ptype == "python"
        else _read_nodejs_package_name() if ptype == "nodejs" else ""
    )
    artifacts = (
        _python_artifacts_for_version(version or "", package_name)
        if ptype == "python" and version
        else _nodejs_artifacts_for_version(version or "")
        if ptype == "nodejs" and version
        else []
    )

    attempts = 1 + len(_RETRY_DELAYS)  # first try + retries
    for attempt in range(attempts):
        try:
            result = run_command_tee(publish_cmd)
            if result.returncode == 0:
                click.echo(
                    click.style(f"  ✓ Published {ptype} successfully", fg="green")
                )
                return True
            combined_output = f"{result.stdout or ''}\n{result.stderr or ''}"
            if "File already exists" in combined_output:
                click.echo(
                    click.style(
                        "  ⚠  Artifact already exists on registry; skipping upload.",
                        fg="yellow",
                    )
                )
                return True  # Not a failure

            blocked = is_pypi_blocked(result)
            if blocked and gh_config is not None and gh_config.skip_pypi_retries_on_block and version:
                click.echo(
                    click.style(
                        "  ⚠ PyPI blocked — deploying to GitHub Releases (parallel channel, no retry)",
                        fg="yellow",
                    )
                )
                if try_github_fallback(
                    result,
                    version=version,
                    package_name=package_name,
                    config=config,
                    artifacts=artifacts or None,
                ):
                    return True
                click.echo(
                    click.style(
                        "  ✗ GitHub fallback failed (check gh CLI and token). Skipping PyPI retry.",
                        fg="red",
                    )
                )
                return False

            if blocked and version:
                if try_github_fallback(
                    result,
                    version=version,
                    package_name=package_name,
                    config=config,
                    artifacts=artifacts or None,
                ):
                    return True

            if _is_rate_limited(result) and attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                click.echo(
                    click.style(
                        f"  ⏳ PyPI rate limit (429). Retrying in {delay}s "
                        f"(attempt {attempt + 2}/{attempts})...",
                        fg="yellow",
                    )
                )
                time.sleep(delay)
                continue

            click.echo(
                click.style(
                    f"  Publish failed with exit code {result.returncode}", fg="red"
                ),
                err=True,
            )
            if result.stderr:
                click.echo(
                    click.style(f"  stderr: {result.stderr}", fg="red"), err=True
                )
            if result.stdout:
                click.echo(
                    click.style(f"  stdout: {result.stdout}", fg="yellow"), err=True
                )
            return False
        except Exception as e:
            click.echo(click.style(f"  Publish exception: {e}", fg="red"), err=True)
            return False
    click.echo(
        click.style(
            f"  ✗ Publish failed after {attempts} attempts due to PyPI rate limiting.",
            fg="red",
        ),
        err=True,
    )
    if version:
        exhausted = type(
            "Result",
            (),
            {
                "stdout": "",
                "stderr": "HTTPError: 429 Too Many Requests\nToo Many Requests",
            },
        )()
        if try_github_fallback(
            exhausted,
            version=version,
            package_name=package_name,
            config=config,
            artifacts=artifacts or None,
        ):
            return True
    return False


def publish_project(
    project_types: List[str],
    version: str,
    yes: bool = False,
    config: Any = None,
) -> bool:
    """Publish project to appropriate package registries."""
    all_valid, errors = validate_project_toml_files()
    if not all_valid:
        for error in errors:
            click.echo(click.style(error, fg="red", bold=True), err=True)
        click.echo(
            click.style(
                "\nFix the TOML syntax error(s) before publishing.", fg="yellow"
            ),
            err=True,
        )
        return False

    success = True
    configured_project_types = _get_configured_project_types(config)

    for ptype in project_types:
        strategy = _get_project_strategy(config, ptype)
        if strategy.get("publish_enabled") is False:
            click.echo(
                click.style(
                    f"  Skipping {ptype} publish (disabled in config)", fg="yellow"
                )
            )
            continue

        if ptype == "nodejs" and "nodejs" not in configured_project_types:
            click.echo(
                click.style(
                    "  Skipping nodejs publish (npm publish not configured for this project)",
                    fg="yellow",
                )
            )
            continue

        publish_cmd = strategy.get("publish", "") or PROJECT_TYPES.get(ptype, {}).get(
            "publish_command", ""
        )
        if not publish_cmd:
            continue

        if ptype == "python":
            python_bin, ok = _prepare_python_publish(strategy, version)
            if not ok:
                success = False
                continue
            publish_cmd = _replace_python_interpreter(publish_cmd, python_bin)
            click.echo(click.style(f"  Command: {publish_cmd}", fg="cyan"))

        if ptype == "python":
            publish_cmd = _resolve_python_publish_cmd(publish_cmd, version)
        elif "{version}" in publish_cmd:
            publish_cmd = publish_cmd.replace("{version}", version)

        if not _run_publish_command(
            ptype, publish_cmd, version=version, config=config
        ):
            success = False

    return success


__all__ = [
    "makefile_has_target",
    "publish_project",
]
