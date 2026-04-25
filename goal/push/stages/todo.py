"""TODO stage - updates TODO.md and planfile.yaml using prefact."""

import subprocess
import click
from pathlib import Path
from goal.git_ops import run_git

def handle_todo_stage(ctx_obj: dict, yes: bool, dry_run: bool) -> None:
    """Run prefact to update TODO.md and planfile.yaml."""
    if not ctx_obj.get('todo'):
        return

    if dry_run:
        click.echo(click.style("  🤖 [dry-run] Would run prefact -a to update TODO.md", fg='cyan'))
        return

    click.echo(click.style("🔍 Updating TODO.md and planfile.yaml via prefact...", fg='cyan'))
    
    try:
        # Run prefact -a
        # We use -a (autonomous) which updates planfile.yaml and TODO.md
        result = subprocess.run(
            ["prefact", "-a"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            click.echo(click.style("  ✅ TODO and planfile updated", fg='green'))
            
            # Stage changes if any
            todo_file = Path("TODO.md")
            planfile = Path("planfile.yaml")
            
            staged = False
            if todo_file.exists():
                run_git("add", "TODO.md")
                staged = True
            if planfile.exists():
                run_git("add", "planfile.yaml")
                staged = True
                
            if staged:
                click.echo(click.style("  ➕ Staged TODO/planfile changes", fg='dim'))
        else:
            click.echo(click.style(f"  ⚠️  prefact failed: {result.stderr or result.stdout}", fg='yellow'))
            
    except FileNotFoundError:
        click.echo(click.style("  ❌ prefact command not found. Skipping TODO update.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"  ❌ Error running prefact: {e}", fg='red'))
