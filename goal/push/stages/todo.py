"""TODO stage - updates TODO.md and planfile.yaml using prefact."""

import subprocess
import click
from pathlib import Path
from goal.git_ops import run_git


def handle_todo_stage(ctx_obj: dict, yes: bool, dry_run: bool) -> bool:
    """Run prefact to update TODO/planfile artifacts.

    Returns:
        True when the stage completed successfully or was skipped.
        False when the stage was explicitly requested but failed.
    """
    if not ctx_obj.get("todo"):
        return True

    if dry_run:
        click.echo(
            click.style(
                "  🤖 [dry-run] Would run prefact -a to update TODO.md", fg="cyan"
            )
        )
        return True

    click.echo(
        click.style("🔍 Updating TODO.md and planfile.yaml via prefact...", fg="cyan")
    )

    try:
        # We use -a (autonomous) which updates planfile and TODO artifacts.
        result = subprocess.run(
            ["prefact", "-a"], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            details = (
                result.stderr or result.stdout or "prefact exited with non-zero status"
            ).strip()
            click.echo(click.style(f"  ❌ prefact failed: {details}", fg="red"))
            click.echo(
                click.style(
                    "  Tip: run `prefact -a` manually to inspect/fix the issue.",
                    fg="yellow",
                )
            )
            return False

        click.echo(click.style("  ✅ TODO and planfile updated", fg="green"))

        stage_candidates = (
            "TODO.md",
            "planfile.yaml",
            ".planfile/sprints/current.yaml",
        )
        existing_candidates = [path for path in stage_candidates if Path(path).exists()]
        if not existing_candidates:
            click.echo(
                click.style(
                    "  ℹ️ prefact ran, but no TODO/planfile artifacts were found to stage.",
                    fg="yellow",
                )
            )
            return True

        failed_paths = []
        for artifact in existing_candidates:
            try:
                run_git("add", artifact)
            except Exception:
                failed_paths.append(artifact)

        if failed_paths:
            failed_list = ", ".join(failed_paths)
            click.echo(
                click.style(
                    f"  ❌ Failed to stage prefact artifacts: {failed_list}", fg="red"
                )
            )
            click.echo(
                click.style(
                    "  Tip: inspect git status and stage files manually.", fg="yellow"
                )
            )
            return False

        click.echo(click.style("  ➕ Staged TODO/planfile changes", fg="bright_black"))
        return True
    except FileNotFoundError:
        click.echo(click.style("  ❌ prefact command not found.", fg="red"))
        click.echo(
            click.style(
                "  Tip: install `prefact` or run push without `--todo`.", fg="yellow"
            )
        )
        return False
    except Exception as e:
        click.echo(click.style(f"  ❌ Error running prefact: {e}", fg="red"))
        return False
