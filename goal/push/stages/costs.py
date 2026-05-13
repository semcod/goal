"""AI cost badge tracking — extracted from push/core.py."""

from pathlib import Path
from typing import Any, Dict, Optional

import click


def _is_cost_tracking_enabled() -> bool:
    """Check pyproject.toml to see if cost badge/readme update is enabled."""
    import tomllib

    config_path = Path("pyproject.toml")
    if not config_path.exists():
        return True
    try:
        with open(config_path, "rb") as f:
            tool_costs = tomllib.load(f).get("tool", {}).get("costs", {})
        return (
            tool_costs.get("badge") is not False
            or tool_costs.get("update_readme") is not False
        )
    except Exception:
        return True


def _compute_ai_costs(project_dir: Path, model: str, api_key: Optional[str]):
    """Parse commits and calculate AI-related costs.

    Returns (total_cost, total_commits, all_commits_data).
    """
    from costs.git_parser import parse_commits, get_commit_diff
    from costs.calculator import ai_cost

    all_commits_data = parse_commits(
        str(project_dir), max_count=500, ai_only=False, full_history=True
    )
    ai_commits = [c for c in all_commits_data if c[1].get("is_ai", False)]

    total_cost = 0.0
    total_commits = len(ai_commits)

    for commit_obj, _data in ai_commits[:50]:
        try:
            diff = get_commit_diff(str(project_dir), commit_obj.hexsha)
            if diff:
                total_cost += ai_cost(diff, model=model, api_key=api_key).get(
                    "cost", 0.0
                )
        except Exception:
            total_cost += 0.15

    if total_cost == 0 and all_commits_data:
        total_cost = len(all_commits_data) * 0.15
        total_commits = len(all_commits_data)

    return total_cost, total_commits, all_commits_data


def update_cost_badges(
    ctx_obj: Dict[str, Any],
    version: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> bool:
    """Update AI cost badges in README using costs package."""
    try:
        try:
            from costs import calculate_human_time, update_readme_badge
        except ImportError:
            from costs.reports import update_readme_badge
            from collections import defaultdict

            def calculate_human_time(commits):
                """Fallback estimator: assume each commit takes ~30 minutes, capped at 8h/author/day."""
                if not commits:
                    return 0.0
                daily = defaultdict(lambda: defaultdict(list))
                for c in commits:
                    daily[c.get("date", "")[:10]][c.get("author", "Unknown")].append(c)
                return sum(
                    min(len(ac) * 0.5, 8.0)
                    for authors in daily.values()
                    for ac in authors.values()
                )

        from costs.git_parser import get_repo_stats

        if not _is_cost_tracking_enabled():
            return False

        model = model or ctx_obj.get("cost_model") or "openrouter/qwen/qwen3-coder-next"
        api_key = api_key or ctx_obj.get("cost_api_key")
        project_dir = Path(".")

        repo_stats = get_repo_stats(str(project_dir))
        total_cost, total_commits, all_commits_data = _compute_ai_costs(
            project_dir, model, api_key
        )

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
                "version": version,
                "human_time": human_hours,
                "human_cost": human_hours * 100,
            }
        }

        success = update_readme_badge(project_dir, results)
        if success:
            click.echo(click.style("✓ Updated AI cost badges in README", fg="green"))
            return True
        return False

    except ImportError:
        return False
    except Exception as e:
        if ctx_obj.get("verbose"):
            click.echo(click.style(f"⚠ Could not update cost badges: {e}", fg="yellow"))
        return False
