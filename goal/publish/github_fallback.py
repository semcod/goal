"""GitHub Releases fallback when PyPI (or other registry) upload is blocked."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from goal.git_ops import run_command_tee


@dataclass(frozen=True)
class GitHubReleaseConfig:
    enabled: bool
    owner: str
    repo: str
    token_env: str
    skip_pypi_retries_on_block: bool
    asset_glob: str
    repo_map: dict[str, str]
    # When True, create a GitHub Release for every successful version tag
    # (not only as PyPI-blocked fallback). Keeps github.com/.../releases in
    # sync with git tags that goal already pushes.
    create_on_tag: bool = False


def _publishing_section(config: Any) -> dict[str, Any]:
    if config is None:
        return {}
    if isinstance(config, dict):
        if "publishing" in config:
            publishing = config.get("publishing", {}) or {}
            return publishing if isinstance(publishing, dict) else {}
        return config
    if hasattr(config, "get"):
        try:
            publishing = config.get("publishing", {}) or {}
            return publishing if isinstance(publishing, dict) else {}
        except Exception:
            return {}
    return {}


def get_github_release_config(config: Any) -> GitHubReleaseConfig | None:
    """Return GitHub release fallback settings, or None when disabled."""
    publishing = _publishing_section(config)
    fallback = publishing.get("fallback", {}) or {}
    gh = fallback.get("github_release", {}) or {}
    if not gh.get("enabled", True):
        return None

    owner = str(gh.get("owner", "") or "").strip()
    repo = str(gh.get("repo", "") or "").strip()
    if not owner or not repo:
        detected_owner, detected_repo = detect_github_owner_repo()
        owner = owner or detected_owner
        repo = repo or detected_repo

    repo_map = gh.get("repo_map", {}) or {}
    if not isinstance(repo_map, dict):
        repo_map = {}

    return GitHubReleaseConfig(
        enabled=True,
        owner=owner,
        repo=repo,
        token_env=str(gh.get("token_env", "GITHUB_TOKEN") or "GITHUB_TOKEN"),
        skip_pypi_retries_on_block=bool(gh.get("skip_pypi_retries_on_block", True)),
        asset_glob=str(gh.get("asset_glob", "dist/*") or "dist/*"),
        repo_map={str(k): str(v) for k, v in repo_map.items()},
        create_on_tag=bool(gh.get("create_on_tag", False)),
    )


def detect_github_owner_repo() -> tuple[str, str]:
    """Detect GitHub owner/repo from ``git remote get-url origin``."""
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "", ""
    if proc.returncode != 0:
        return "", ""
    url = (proc.stdout or "").strip()
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
    if not match:
        return "", ""
    return match.group(1), match.group(2)


def resolve_github_repo(
    package_name: str,
    gh_config: GitHubReleaseConfig,
) -> tuple[str, str]:
    """Resolve GitHub owner/repo for a distribution name."""
    owner = gh_config.owner
    if package_name and package_name in gh_config.repo_map:
        repo = gh_config.repo_map[package_name]
    elif gh_config.repo:
        repo = gh_config.repo
    elif package_name:
        repo = package_name
    else:
        _, detected_repo = detect_github_owner_repo()
        repo = detected_repo
    return owner, repo


def is_pypi_blocked(result) -> bool:
    """True when registry upload is blocked (rate limit, auth, permission)."""
    combined = f"{result.stdout or ''}\n{result.stderr or ''}"
    if "429" in combined and "Too Many Requests" in combined:
        return True
    block_markers = (
        "403",
        "Forbidden",
        "does not have permission",
        "Invalid or non-existent authentication",
        "authentication information",
        "denied",
        "Project name already exists",  # squatter / wrong account
    )
    return any(marker in combined for marker in block_markers)


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _env_token_present(token_env: str) -> bool:
    return bool(os.environ.get(token_env, "").strip())


def _token_present(token_env: str) -> bool:
    return _env_token_present(token_env) or _gh_authenticated()


def _gh_authenticated() -> bool:
    """True when gh CLI has an active login (keyring), even without GITHUB_TOKEN."""
    if not _gh_available():
        return False
    try:
        proc = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    combined = f"{proc.stdout or ''}\n{proc.stderr or ''}"
    return proc.returncode == 0 and "Logged in to" in combined


def github_fallback_actionable(gh_config: GitHubReleaseConfig | None) -> bool:
    """True when gh CLI and token are available for a release upload."""
    if gh_config is None:
        return False
    return _gh_available() and _token_present(gh_config.token_env)


def _dist_assets(version: str, package_name: str, asset_glob: str) -> list[Path]:
    dist = Path("dist")
    if not dist.is_dir():
        return []

    suffixes = (".whl", ".tar.gz", ".zip")
    patterns: list[str]
    if package_name:
        candidates = {
            package_name,
            package_name.replace("-", "_"),
            package_name.replace("_", "-"),
        }
        patterns = [f"{c}-{version}*" for c in sorted(candidates)]
    else:
        patterns = [f"*-{version}*"]

    if asset_glob and asset_glob != "dist/*":
        globbed = sorted(dist.glob(asset_glob.removeprefix("dist/")))
        return [p for p in globbed if p.is_file()]

    artifacts: list[Path] = []
    for pattern in patterns:
        for path in dist.glob(pattern):
            if path.is_file() and path.name.endswith(suffixes):
                artifacts.append(path)
    return sorted(set(artifacts))


def publish_github_release(
    version: str,
    *,
    package_name: str = "",
    gh_config: GitHubReleaseConfig,
    artifacts: list[Path] | None = None,
) -> bool:
    """Create or update a GitHub release and upload wheel/sdist assets."""
    if not _gh_available():
        click.echo(
            click.style(
                "  ⚠ GitHub fallback skipped: gh CLI not found (install gh or set PATH)",
                fg="yellow",
            )
        )
        return False

    if not (_env_token_present(gh_config.token_env) or _gh_authenticated()):
        click.echo(
            click.style(
                f"  ⚠ GitHub fallback skipped: run `gh auth login` or set {gh_config.token_env}",
                fg="yellow",
            )
        )
        return False

    owner, repo = resolve_github_repo(package_name, gh_config)
    if not owner or not repo:
        click.echo(
            click.style(
                "  ⚠ GitHub fallback skipped: could not resolve owner/repo "
                "(set publishing.fallback.github_release.owner/repo or git remote)",
                fg="yellow",
            )
        )
        return False

    files = artifacts or _dist_assets(version, package_name, gh_config.asset_glob)
    if not files:
        click.echo(
            click.style(
                f"  ⚠ GitHub fallback skipped: no dist artifacts for version {version}",
                fg="yellow",
            )
        )
        return False

    tag = f"v{version.lstrip('v')}"
    remote = f"{owner}/{repo}"
    click.echo(
        click.style(
            f"  ↻ GitHub fallback: {remote} release {tag} ({len(files)} asset(s))",
            fg="cyan",
        )
    )

    view_cmd = f"gh release view {tag} -R {remote}"
    view = subprocess.run(view_cmd, shell=True, capture_output=True, text=True)
    if view.returncode != 0:
        create_cmd = (
            f"gh release create {tag} -R {remote} "
            f"--title '{package_name or repo} {tag}' "
            f"--notes 'Automated release {tag} (PyPI blocked — parallel GitHub channel)'"
        )
        create = run_command_tee(create_cmd)
        if create.returncode != 0:
            click.echo(
                click.style("  ✗ GitHub release create failed", fg="red"), err=True
            )
            return False

    upload_paths = " ".join(str(p) for p in files)
    upload_cmd = f"gh release upload {tag} -R {remote} {upload_paths} --clobber"
    upload = run_command_tee(upload_cmd)
    if upload.returncode != 0:
        click.echo(click.style("  ✗ GitHub release upload failed", fg="red"), err=True)
        return False

    wheel = next((p for p in files if p.suffix == ".whl"), files[0])
    click.echo(
        click.style(
            f"  ✓ GitHub release OK: https://github.com/{remote}/releases/tag/{tag}",
            fg="green",
        )
    )
    click.echo(
        click.style(
            f"  → pip install: https://github.com/{remote}/releases/download/{tag}/{wheel.name}",
            fg="cyan",
        )
    )
    return True


def try_github_fallback(
    result,
    *,
    version: str,
    package_name: str = "",
    config: Any = None,
    artifacts: list[Path] | None = None,
) -> bool:
    """Attempt GitHub release when PyPI upload failed with a blocking error."""
    gh_config = get_github_release_config(config)
    if gh_config is None:
        return False
    if not is_pypi_blocked(result):
        return False

    click.echo(
        click.style(
            "  ⚠ PyPI upload blocked — deploying to GitHub Releases (parallel channel)",
            fg="yellow",
        )
    )
    return publish_github_release(
        version,
        package_name=package_name,
        gh_config=gh_config,
        artifacts=artifacts,
    )


def try_github_release_on_tag(
    *,
    version: str,
    package_name: str = "",
    config: Any = None,
    artifacts: list[Path] | None = None,
) -> bool:
    """Create a GitHub Release for *version* when ``create_on_tag`` is enabled.

    Complements git tags (which goal always creates when releasing): tags can
    exist without a GitHub Release object, so the Releases page stays stuck on
    an old version unless something calls ``gh release create``.
    """
    gh_config = get_github_release_config(config)
    if gh_config is None or not gh_config.create_on_tag:
        return False
    click.echo(
        click.style(
            "  ↻ create_on_tag: publishing GitHub Release for this tag",
            fg="cyan",
        )
    )
    return publish_github_release(
        version,
        package_name=package_name,
        gh_config=gh_config,
        artifacts=artifacts,
    )
