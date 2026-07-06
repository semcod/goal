"""Workflow preview rendering — extracted from push/core.py.

Renders the pre-commit workflow preview (files, version bump, commit message)
in either plain terminal or markdown form.
"""

import click


def show_workflow_preview(
    files,
    stats,
    current_version,
    new_version,
    commit_msg,
    commit_body,
    markdown,
    ctx_obj,
) -> None:
    """Show workflow preview for interactive mode."""
    total_adds = sum(s[0] for s in stats.values())
    total_dels = sum(s[1] for s in stats.values())
    denom = (total_adds + total_dels) or 1
    deletion_pct = int((total_dels / denom) * 100)
    net = total_adds - total_dels

    if markdown or ctx_obj.get("markdown"):
        click.echo("\n## GOAL Workflow Preview\n")
        click.echo(
            f"- **Files:** {len(files)} (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)"
        )
        click.echo(f"- **Version:** {current_version} → {new_version}")
        click.echo(f"- **Commit:** `{commit_msg}`")
        if commit_body:
            click.echo(f"\n### Commit Body\n```\n{commit_body}\n```")
    else:
        click.echo(click.style("\n=== GOAL Workflow ===", fg="cyan", bold=True))
        click.echo(
            f"Will commit {len(files)} files (+{total_adds}/-{total_dels} lines, NET {net}, {deletion_pct}% churn deletions)"
        )
        click.echo(f"Version bump: {current_version} -> {new_version}")
        click.echo(f"Commit message: {click.style(commit_msg, fg='green')}")
        if commit_body:
            click.echo(click.style("\nCommit body (preview):", fg="cyan"))
            click.echo(commit_body)
