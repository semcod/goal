"""AI costs helpers and README badge generation for project bootstrap."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

import click

from goal.bootstrap.configurator import _find_git_root

logger = logging.getLogger(__name__)

try:
    from git.exc import InvalidGitRepositoryError
except ImportError:  # pragma: no cover - gitpython optional

    class InvalidGitRepositoryError(Exception):
        """Fallback when gitpython is unavailable."""


_AI_INDICATORS = (
    "🤖",
    "ai:",
    "[ai]",
    "(ai)",
    "automat",
    "cascade",
    "claude",
    "gpt",
    "llm",
)


def _install_costs_package(project_dir: Path, python_bin: str) -> bool:
    """Check if costs is installed; install it if not. Returns True on success."""
    result = subprocess.run(
        [python_bin, "-c", "import costs; print(costs.__version__)"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )
    if result.returncode == 0:
        click.echo(
            click.style(
                f"  ✓ Costs package already installed ({result.stdout.strip()})",
                fg="green",
            )
        )
        return True

    click.echo(click.style("  Installing costs package...", fg="cyan"))
    install_result = subprocess.run(
        [python_bin, "-m", "pip", "install", "costs>=0.1.20"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )
    if install_result.returncode != 0:
        click.echo(click.style("  ⚠ Could not install costs package", fg="yellow"))
        return False
    click.echo(click.style("  ✓ Costs package installed", fg="green"))
    return True


def _load_costs_api():
    """Import costs API functions, falling back to older API versions."""
    try:
        from costs import calculate_human_time, update_readme_badge
    except ImportError:
        from collections import defaultdict

        from costs.reports import update_readme_badge

        def calculate_human_time(commits):
            """Calculate human hours from commit history."""
            if not commits:
                return 0.0
            daily_commits = defaultdict(lambda: defaultdict(list))
            for commit in commits:
                date = commit.get("date", "")[:10]
                author = commit.get("author", "Unknown")
                daily_commits[date][author].append(commit)
            total_hours = 0.0
            for date, authors in daily_commits.items():
                for author, author_commits in authors.items():
                    total_hours += min(len(author_commits) * 0.5, 8.0)
            return total_hours

    return calculate_human_time, update_readme_badge


def _commit_blob_lower(commit_obj, parsed_tail) -> str:
    msg = getattr(commit_obj, "message", "") or ""
    tail = parsed_tail if isinstance(parsed_tail, str) else ""
    return f"{msg} {tail}".lower()


def _filter_ai_commits(all_commits_data, indicators=_AI_INDICATORS):
    return [
        c
        for c in all_commits_data
        if any(ind in _commit_blob_lower(c[0], c[1]) for ind in indicators)
    ]


def _parsed_diff_is_usable(parsed_diff: object) -> bool:
    if not isinstance(parsed_diff, str):
        return False
    return (
        "diff --git" in parsed_diff
        or "\n@@ " in parsed_diff
        or parsed_diff.startswith("@@")
    )


def _fetch_commit_diff(repo_root: Path, commit_obj, parsed_diff: str, get_commit_diff):
    if _parsed_diff_is_usable(parsed_diff):
        return parsed_diff
    try:
        return get_commit_diff(
            str(repo_root), getattr(commit_obj, "hexsha", commit_obj)
        )
    except (OSError, ValueError, TypeError, AttributeError):
        from git import Repo as _GitRepo

        return get_commit_diff(_GitRepo(str(repo_root)), commit_obj)


def _single_commit_ai_cost(
    repo_root, commit_obj, parsed_diff, get_commit_diff, ai_cost
):
    try:
        diff = _fetch_commit_diff(repo_root, commit_obj, parsed_diff, get_commit_diff)
        if not diff:
            return 0.0
        return ai_cost(diff, model="openrouter/qwen/qwen3-coder-next").get("cost", 0.0)
    except (
        OSError,
        ValueError,
        TypeError,
        AttributeError,
        ImportError,
        InvalidGitRepositoryError,
    ) as exc:
        commit_hash = getattr(commit_obj, "hexsha", "unknown")
        logger.debug("Unable to evaluate AI cost for commit %s: %s", commit_hash, exc)
        return 0.15


def _calculate_ai_costs(repo_root: Path):
    """Parse commits and calculate AI-related costs.

    Returns (total_cost, total_commits, all_commits_data).
    """
    from costs.calculator import ai_cost
    from costs.git_parser import get_commit_diff, parse_commits

    all_commits_data = parse_commits(
        str(repo_root), max_count=500, ai_only=False, full_history=True
    )
    ai_commits = _filter_ai_commits(all_commits_data)

    total_cost = sum(
        _single_commit_ai_cost(
            repo_root, commit_obj, parsed_diff, get_commit_diff, ai_cost
        )
        for commit_obj, parsed_diff in ai_commits[:50]
    )
    total_commits = len(ai_commits)

    if total_cost == 0 and all_commits_data:
        total_cost = len(all_commits_data) * 0.15
        total_commits = len(all_commits_data)

    return total_cost, total_commits, all_commits_data


def _read_model_from_pyproject(project_dir: Path) -> str:
    """Read default_model from pyproject.toml, or return a default."""
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'default_model\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "openrouter/qwen/qwen3-coder-next"


def _generate_costs_badge(project_dir: Path) -> None:
    """Generate an AI cost badge in the project README."""
    click.echo(click.style("  Generating AI cost badge...", fg="cyan"))
    try:
        repo_root = _find_git_root(project_dir) or project_dir
        calculate_human_time, update_readme_badge = _load_costs_api()
        from costs.git_parser import get_repo_stats

        repo_stats = get_repo_stats(str(repo_root))
        total_cost, total_commits, all_commits_data = _calculate_ai_costs(repo_root)
        model = _read_model_from_pyproject(project_dir)

        all_commits_list = [
            {"date": c[0].committed_datetime.isoformat(), "author": c[0].author.name}
            for c in all_commits_data
        ]
        human_hours = calculate_human_time(all_commits_list)

        results = {
            "summary": {
                "total_cost": total_cost,
                "total_cost_formatted": f"${total_cost:.4f}",
                "total_commits": total_commits,
                "model": model,
                "version": repo_stats.get("repo_name", "unknown"),
                "human_time": human_hours,
                "human_cost": human_hours * 100,
            }
        }

        readme_path = repo_root / "README.md"
        if readme_path.exists():
            success = update_readme_badge(repo_root, results)
            if success:
                click.echo(
                    click.style("  ✓ AI cost badge updated in README", fg="green")
                )
            else:
                click.echo(
                    click.style("  ⚠ Failed to update README badge", fg="yellow")
                )
        else:
            click.echo(click.style("  ⚠ README.md not found", fg="yellow"))
    except (
        OSError,
        ValueError,
        TypeError,
        ImportError,
        InvalidGitRepositoryError,
    ) as e:
        logger.warning("AI badge generation failed in %s: %s", project_dir, e)
        click.echo(
            click.style(f"  ⚠ Badge generation failed: {str(e)[:100]}", fg="yellow")
        )
