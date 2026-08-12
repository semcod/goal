"""Push workflow stages - tag creation."""

from typing import Optional

import click

from goal.git_ops import run_git


def create_tag(new_version: str, no_tag: bool) -> Optional[str]:
    """Create git tag for release."""
    if no_tag:
        return None

    tag_name = f"v{new_version}"
    tag_exists = run_git("rev-parse", "-q", "--verify", f"refs/tags/{tag_name}")

    if tag_exists.returncode == 0:
        click.echo(click.style(f"Warning: Tag already exists: {tag_name}", fg="yellow"))
        return None

    result = run_git("tag", "-a", tag_name, "-m", f"Release {new_version}")
    if result.returncode != 0:
        click.echo(
            click.style(
                f"⚠ Warning: Could not create tag: {result.stderr}", fg="yellow"
            )
        )
        return None

    click.echo(click.style(f"✓ Created tag: {tag_name}", fg="green"))
    return tag_name


def reuse_exact_annotated_tag(new_version: str) -> str:
    """Return an existing release tag only when it is annotated at exact HEAD."""
    tag_name = f"v{new_version}"
    reference = f"refs/tags/{tag_name}"
    object_type = run_git("cat-file", "-t", reference)
    if object_type.returncode != 0 or object_type.stdout.strip() != "tag":
        raise click.ClickException(
            f"existing release tag {tag_name} is missing or is not annotated"
        )

    tagged_commit = run_git("rev-parse", f"{reference}^{{commit}}")
    current_commit = run_git("rev-parse", "HEAD^{commit}")
    if tagged_commit.returncode != 0 or current_commit.returncode != 0:
        raise click.ClickException(
            f"cannot resolve existing release tag {tag_name} against HEAD"
        )
    if tagged_commit.stdout.strip() != current_commit.stdout.strip():
        raise click.ClickException(
            f"existing release tag {tag_name} does not point to current HEAD"
        )

    click.echo(
        click.style(
            f"✓ Reusing exact annotated tag for Release repair: {tag_name}",
            fg="green",
        )
    )
    return tag_name
