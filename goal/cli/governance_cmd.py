"""Adopt pinned wellmanifest/new-project governance into existing projects."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile

import click

from goal.cli import main


DEFAULT_STANDARD_REPOSITORY = "https://github.com/wellmanifest/new-project.git"
FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _run_git(arguments, cwd=None):
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _checkout_standard(repository, revision, destination):
    init = _run_git(["init", "--quiet", str(destination)])
    if init.returncode != 0:
        raise click.ClickException(
            "could not initialize the temporary standard checkout"
        )

    remote = _run_git(["remote", "add", "origin", repository], cwd=destination)
    if remote.returncode != 0:
        raise click.ClickException("could not configure the standard repository")

    fetch = _run_git(
        ["fetch", "--quiet", "--depth", "1", "origin", revision], cwd=destination
    )
    if fetch.returncode != 0:
        raise click.ClickException(
            "could not fetch the requested standard revision; verify that the full SHA is published"
        )

    checkout = _run_git(
        ["checkout", "--quiet", "--detach", "FETCH_HEAD"], cwd=destination
    )
    if checkout.returncode != 0:
        raise click.ClickException(
            "could not check out the requested standard revision"
        )

    resolved = _run_git(["rev-parse", "HEAD"], cwd=destination)
    if resolved.returncode != 0 or resolved.stdout.strip() != revision:
        raise click.ClickException(
            "checked-out standard revision does not match the requested SHA"
        )


@main.group()
def governance():
    """Adopt and verify pinned repository governance."""


@governance.command("adopt")
@click.option(
    "--standard-repository",
    envvar="NEW_PROJECT_STANDARD_REPOSITORY",
    default=DEFAULT_STANDARD_REPOSITORY,
    show_default=True,
    help="Git URL or local path of wellmanifest/new-project.",
)
@click.option(
    "--source-revision",
    required=True,
    help="Published lowercase 40-character standard commit SHA.",
)
@click.option(
    "--target-root",
    default=".",
    type=click.Path(file_okay=False, path_type=Path),
    show_default=True,
    help="Existing project to adopt or check.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Report drift and the adoption plan without writing files.",
)
@click.option(
    "--upgrade",
    is_flag=True,
    help="Replace reviewed standard-managed drift.",
)
def adopt(standard_repository, source_revision, target_root, check, upgrade):
    """Adopt an immutable new-project revision into an existing project."""
    if FULL_SHA_PATTERN.fullmatch(source_revision) is None:
        raise click.BadParameter(
            "must be a full lowercase 40-character commit SHA",
            param_hint="--source-revision",
        )
    if check and upgrade:
        raise click.UsageError("--check and --upgrade are mutually exclusive")

    target = target_root.resolve()
    if not target.is_dir():
        raise click.BadParameter(
            "must identify an existing directory", param_hint="--target-root"
        )

    with tempfile.TemporaryDirectory(prefix="goal-governance-") as temporary:
        standard = Path(temporary) / "standard"
        _checkout_standard(standard_repository, source_revision, standard)
        generator = standard / "scripts" / "create_adoption_lock.py"
        if not generator.is_file():
            raise click.ClickException(
                "the requested standard revision does not publish create_adoption_lock.py"
            )

        command = [
            sys.executable,
            str(generator),
            "--target-root",
            str(target),
            "--source-revision",
            source_revision,
        ]
        if check:
            command.append("--check")
        if upgrade:
            command.append("--upgrade")

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, err=True, nl=False)
        if result.returncode != 0:
            raise click.exceptions.Exit(result.returncode)


__all__ = ["governance", "adopt"]
