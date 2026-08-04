"""Commit command - extracted from cli.py."""

import click

from goal.commit_generator import CommitMessageGenerator
from goal.git_ops import get_staged_files, get_diff_stats
from goal.cli import main, apply_ticket_prefix
from goal.authors.utils import (
    get_co_authors_from_command_line,
    add_co_authors_to_message,
)


def _output_detailed(title: str, body: str, use_markdown: bool) -> None:
    """Print a detailed commit message in markdown or plain style."""
    if use_markdown:
        click.echo(f"## Commit Message\n\n**{title}**\n\n{body}")
    else:
        click.echo(click.style("Generated commit message:", fg="cyan", bold=True))
        click.echo(f"\n{click.style(title, fg='green', bold=True)}")
        if body:
            click.echo(f"\n{body}")


def _output_simple(title: str, co_authors: list, use_markdown: bool) -> None:
    """Print a simple commit message (with optional co-authors)."""
    if use_markdown:
        click.echo(f"## Commit Message\n\n**{title}**")
        if co_authors:
            click.echo()
            for author in co_authors:
                click.echo(f"Co-authored-by: {author['name']} <{author['email']}>")
    else:
        click.echo(click.style("Generated commit message:", fg="cyan"))
        click.echo(click.style(title, fg="green"))
        if co_authors:
            click.echo()
            for author in co_authors:
                click.echo(
                    click.style(
                        f"Co-authored-by: {author['name']} <{author['email']}>",
                        fg="cyan",
                    )
                )


@main.command()
@click.option(
    "--detailed", is_flag=True, help="Generate detailed commit message with body"
)
@click.option("--unstaged", is_flag=True, help="Include unstaged changes")
@click.option("--markdown/--ascii", default=False, help="Output format")
@click.option("--ticket", default=None, help="Ticket ID for commit prefix")
@click.option(
    "--abstraction", default=None, help="Abstraction level for commit message"
)
@click.option(
    "--co-author", multiple=True, help="Add co-author (Name <email> or email)"
)
@click.pass_context
def commit(ctx, detailed, unstaged, markdown, ticket, abstraction, co_author) -> None:
    """Generate a smart commit message for current changes."""
    files = get_staged_files()

    if not files or files == [""]:
        click.echo(
            click.style(
                "No staged changes. Stage files first with 'git add'.", fg="yellow"
            )
        )
        return

    config_obj = ctx.obj.get("config")
    config_dict = config_obj.to_dict() if config_obj else None

    generator = CommitMessageGenerator(config=config_dict)
    co_authors = get_co_authors_from_command_line(list(co_author))
    use_markdown = markdown or ctx.obj.get("markdown")

    if detailed:
        result = generator.generate_detailed_message(cached=not unstaged)
        if result:
            title = apply_ticket_prefix(result.get("title"), ticket)
            body = result.get("body", "")
            if co_authors:
                body = add_co_authors_to_message(body, co_authors)
            _output_detailed(title, body, use_markdown)
        else:
            click.echo(click.style("Could not generate detailed message.", fg="yellow"))
    else:
        message = generator.generate_commit_message(cached=not unstaged)
        title = apply_ticket_prefix(message, ticket)
        _output_simple(title, co_authors, use_markdown)


@main.command()
@click.option("--fix", is_flag=True, help="Auto-fix issues")
@click.option("--preview", is_flag=True, help="Show preview only")
@click.option("--cached", is_flag=True, default=True, help="Use cached/staged changes")
@click.pass_context
def fix_summary(ctx, fix, preview, cached):
    """Auto-fix commit summary quality issues."""
    from ..enhanced_summary import QualityValidator

    files = get_staged_files()
    stats = get_diff_stats()

    if not files:
        click.echo(click.style("No changes to analyze.", fg="yellow"))
        return

    config_obj = ctx.obj.get("config")
    config_dict = config_obj.to_dict() if config_obj else {}

    generator = CommitMessageGenerator(config=config_dict)
    detailed = generator.generate_detailed_message(cached=cached)

    if not detailed:
        click.echo(click.style("Could not generate summary.", fg="yellow"))
        return

    validator = QualityValidator(config_dict)

    summary = {
        "title": detailed.get("title", ""),
        "body": detailed.get("body", ""),
        "intent": detailed.get("intent", ""),
        "metrics": {
            "lines_added": sum(s[0] for s in stats.values()),
            "lines_deleted": sum(s[1] for s in stats.values()),
        },
    }

    validation = validator.validate(summary, files)

    if validation.get("valid", True):
        click.echo(click.style("✓ Summary passes quality gates", fg="green"))
        return

    if preview or not fix:
        click.echo(click.style("Quality issues found:", fg="yellow", bold=True))
        for error in validation.get("errors", []):
            click.echo(f"  ✗ {error}")

        fixed = validator.auto_fix(summary, files)
        if fixed:
            click.echo(
                f"\nSuggested title: {click.style(fixed.get('title', ''), fg='cyan')}"
            )
    else:
        # Apply fixes
        fixed = validator.auto_fix(summary, files)
        if fixed:
            click.echo(click.style(f"✓ Fixed: {fixed.get('title', '')}", fg="green"))


@main.command()
@click.option("--fix", is_flag=True, help="Auto-fix issues")
@click.option("--cached", is_flag=True, default=True, help="Use cached/staged changes")
@click.pass_context
def validate(ctx, fix, cached):
    """Validate commit summary against quality gates."""

    files = get_staged_files()
    stats = get_diff_stats()

    if not files:
        click.echo(click.style("No changes to validate.", fg="yellow"))
        return

    config_obj = ctx.obj.get("config")
    config_dict = config_obj.to_dict() if config_obj else {}

    generator = CommitMessageGenerator(config=config_dict)
    detailed = generator.generate_detailed_message(cached=cached)

    if not detailed:
        click.echo(click.style("Could not generate summary.", fg="yellow"))
        return

    validator = QualityValidator(config_dict)

    summary = {
        "title": detailed.get("title", ""),
        "body": detailed.get("body", ""),
        "intent": detailed.get("intent", ""),
        "metrics": {
            "lines_added": sum(s[0] for s in stats.values()),
            "lines_deleted": sum(s[1] for s in stats.values()),
        },
    }

    validation = validator.validate(summary, files)
    score = validation.get("score", 0)

    click.echo(click.style(f"Quality Score: {score}/100", fg="cyan", bold=True))

    if validation.get("errors"):
        click.echo(click.style("\nErrors:", fg="red"))
        for error in validation.get("errors"):
            click.echo(f"  ✗ {error}")

    if validation.get("warnings"):
        click.echo(click.style("\nWarnings:", fg="yellow"))
        for warning in validation.get("warnings"):
            click.echo(f"  ⚠ {warning}")

    if validation.get("valid", True):
        click.echo(click.style("\n✓ Validation passed", fg="green"))
    else:
        click.echo(click.style("\n✗ Validation failed", fg="red"))
        if fix:
            fixed = validator.auto_fix(summary, files)
            if fixed:
                click.echo(
                    click.style(
                        f"\n✓ Fixed title: {fixed.get('title', '')}", fg="green"
                    )
                )
        else:
            click.echo("\nRun with --fix to auto-correct issues")


__all__ = [
    "commit",
    "fix_summary",
    "validate",
]
