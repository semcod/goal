"""Adopt pinned wellmanifest/new-project governance into existing projects."""

from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import click

from goal.cli import main
from goal.config import load_config
from goal.governance.delivery import (
    GOVERNANCE_PACKAGE_FILES,
    authorize_hook_push,
    check_delivery_hook,
    governance_diagnostic_guidance,
    install_delivery_hook,
    is_new_project_source_hub,
    missing_governance_package_files,
    policy_payload,
    remove_delivery_hook,
    resolve_delivery_policy,
)


DEFAULT_STANDARD_REPOSITORY = "https://github.com/wellmanifest/new-project.git"
CANONICAL_STANDARD_RELEASES_API = (
    "https://api.github.com/repos/wellmanifest/new-project/releases/tags"
)
MAX_RELEASE_METADATA_BYTES = 1024 * 1024
FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
WORKSPACE_LIFECYCLE_CHECKER = ".governance/workspace_lifecycle_check.py"
RESERVED_VALIDATOR_OPTIONS = (
    "--root",
    "--manifest",
    "--lock",
    "--stack-profiles",
)


def _run_git(arguments, cwd=None):
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _load_github_release(tag):
    request = Request(
        f"{CANONICAL_STANDARD_RELEASES_API}/{quote(tag, safe='')}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "goal-governance-adoption",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read(MAX_RELEASE_METADATA_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise click.ClickException(
            f"the canonical standard has no verifiable published GitHub Release {tag}"
        ) from error
    if len(raw) > MAX_RELEASE_METADATA_BYTES:
        raise click.ClickException(
            f"the canonical GitHub Release metadata for {tag} is unexpectedly large"
        )
    try:
        release = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise click.ClickException(
            f"the canonical GitHub Release metadata for {tag} is invalid"
        ) from error
    if not isinstance(release, dict):
        raise click.ClickException(
            f"the canonical GitHub Release metadata for {tag} is invalid"
        )
    return release


def _verify_published_standard(revision, standard):
    version_path = standard / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise click.ClickException(
            "the requested standard revision does not publish VERSION"
        ) from error
    if VERSION_PATTERN.fullmatch(version) is None:
        raise click.ClickException(
            f"the requested standard VERSION is invalid: {version!r}"
        )
    tag = f"v{version}"
    fetched = _run_git(
        [
            "fetch",
            "--quiet",
            "--depth",
            "1",
            "origin",
            f"refs/tags/{tag}:refs/tags/{tag}",
        ],
        cwd=standard,
    )
    if fetched.returncode != 0:
        raise click.ClickException(
            f"the requested standard revision has no published release tag {tag}"
        )
    tag_type = _run_git(["cat-file", "-t", f"refs/tags/{tag}"], cwd=standard)
    if tag_type.returncode != 0 or tag_type.stdout.strip() != "tag":
        raise click.ClickException(
            f"the standard release tag {tag} must be an annotated Git tag"
        )
    peeled = _run_git(["rev-parse", f"refs/tags/{tag}^{{commit}}"], cwd=standard)
    if peeled.returncode != 0 or peeled.stdout.strip() != revision:
        raise click.ClickException(
            f"the standard release tag {tag} does not identify requested revision {revision}"
        )

    release = _load_github_release(tag)
    if release.get("tag_name") != tag:
        raise click.ClickException(
            f"the canonical GitHub Release does not identify standard tag {tag}"
        )
    published_at = release.get("published_at")
    if (
        release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(published_at, str)
        or not published_at.strip()
    ):
        raise click.ClickException(
            f"the canonical GitHub Release {tag} is not a final published release"
        )


def _checkout_standard(
    repository,
    revision,
    destination,
    *,
    allow_unpublished_for_testing=False,
):
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
    if not allow_unpublished_for_testing:
        _verify_published_standard(revision, destination)


@main.group()
def governance():
    """Adopt and verify pinned repository governance."""


def _reject_reserved_validator_options(arguments):
    for argument in arguments:
        if any(
            argument == option or argument.startswith(f"{option}=")
            for option in RESERVED_VALIDATOR_OPTIONS
        ):
            raise click.UsageError(
                f"{argument.split('=', 1)[0]} is managed by Goal and cannot be overridden"
            )


@governance.command(
    "check",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--target-root",
    default=".",
    type=click.Path(file_okay=False, path_type=Path),
    show_default=True,
    help="Repository containing an adopted .governance package.",
)
@click.argument("validator_args", nargs=-1, type=click.UNPROCESSED)
def governance_check(target_root, validator_args):
    """Run the deterministic validator from the adopted governance package."""
    target = target_root.resolve()
    missing = missing_governance_package_files(target)
    if missing:
        if is_new_project_source_hub(target):
            raise click.ClickException(
                "the target is the maintained wellmanifest/new-project source "
                "hub, not an adopted repository; run the source-hub checks "
                "declared in .github/workflows/ci.yml and do not adopt a "
                "target .governance package into the hub"
            )
        raise click.ClickException(
            "adopted governance package is incomplete; missing: "
            + ", ".join(missing)
            + "; run `goal governance adopt` with a published source revision"
        )

    _reject_reserved_validator_options(validator_args)
    command = [
        sys.executable,
        str(target / GOVERNANCE_PACKAGE_FILES["validator"]),
        "--root",
        str(target),
        "--manifest",
        GOVERNANCE_PACKAGE_FILES["manifest"],
        "--lock",
        GOVERNANCE_PACKAGE_FILES["lock"],
        "--stack-profiles",
        GOVERNANCE_PACKAGE_FILES["stack profiles"],
        *validator_args,
    ]
    result = subprocess.run(
        command,
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        click.echo(result.stdout, nl=False)
    if result.stderr:
        click.echo(result.stderr, err=True, nl=False)
    if result.returncode != 0:
        output = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        )
        for line in governance_diagnostic_guidance(target, output):
            click.echo(line, err=True)
        raise click.exceptions.Exit(result.returncode)


@governance.command("workspace-check")
@click.option(
    "--target-root",
    default=".",
    type=click.Path(file_okay=False, path_type=Path),
    show_default=True,
    help="Repository containing the adopted workspace lifecycle checker.",
)
@click.option(
    "--workspace-root",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory whose immediate repository checkouts are audited.",
)
@click.option(
    "--allow",
    multiple=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Exact active secondary checkout allowed for a non-terminal audit.",
)
@click.option("--format", "output_format", type=click.Choice(("text", "json")), default="text")
def workspace_check(target_root, workspace_root, allow, output_format):
    """Run the read-only checker from the adopted governance package."""
    target = target_root.resolve()
    checker = target / WORKSPACE_LIFECYCLE_CHECKER
    if not checker.is_file():
        raise click.ClickException(
            f"adopted workspace lifecycle checker is missing: {WORKSPACE_LIFECYCLE_CHECKER}; "
            "run `goal governance adopt` with a published source revision"
        )

    command = [
        sys.executable,
        str(checker),
        "--workspace-root",
        str(workspace_root.resolve()),
    ]
    for path in allow:
        command.extend(("--allow", str(path.resolve())))
    command.extend(("--format", output_format))
    result = subprocess.run(
        command,
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        click.echo(result.stdout, nl=False)
    if result.stderr:
        click.echo(result.stderr, err=True, nl=False)
    if result.returncode != 0:
        raise click.exceptions.Exit(result.returncode)


@governance.group("delivery-hook")
def delivery_hook():
    """Manage the local fail-fast pre-push guard."""


@delivery_hook.command("install")
def delivery_hook_install():
    path = install_delivery_hook()
    click.echo(f"installed governed pre-push block in {path}")


@delivery_hook.command("check")
def delivery_hook_check():
    if not check_delivery_hook():
        raise click.ClickException(
            "governed pre-push block is missing; run `goal governance delivery-hook install`"
        )
    click.echo("governed pre-push block is installed")


@delivery_hook.command("remove")
def delivery_hook_remove():
    path = remove_delivery_hook()
    click.echo(f"removed governed block from {path}; project-owned hook code preserved")


@governance.command("authorize-push", hidden=True)
@click.argument("remote_name")
@click.argument("remote_url", required=False)
@click.pass_context
def authorize_push(ctx, remote_name, remote_url):
    config = (ctx.find_root().obj or {}).get("config") or load_config()
    if hasattr(config, "exists") and not config.exists():
        raise click.ClickException(
            "governed pre-push authorization requires an existing goal.yaml "
            "with governance.delivery configuration"
        )
    policy = resolve_delivery_policy(config, None, all_flags=True)
    if policy is None:
        raise click.ClickException(
            "governed pre-push authorization requires governance.delivery "
            "configuration in goal.yaml"
        )
    authorize_hook_push(policy, remote_name)


@governance.command("verify-delivery")
@click.option(
    "--delivery-mode",
    type=click.Choice(["direct-main", "publish-only", "pull-request"]),
    default=None,
)
@click.pass_context
def verify_delivery(ctx, delivery_mode):
    """Print the resolved policy and local/server enforcement boundary."""
    config = (ctx.find_root().obj or {}).get("config") or load_config()
    policy = resolve_delivery_policy(
        config, delivery_mode, all_flags=True
    )
    payload = policy_payload(policy)
    payload["hookInstalled"] = check_delivery_hook()
    payload["serverGuidance"] = (
        "Protect the base branch and require a CI governance status; local hooks "
        "can be bypassed with --no-verify or removed."
    )
    click.echo(json.dumps(payload, indent=2, sort_keys=True))


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
@click.option(
    "--allow-unpublished-for-testing",
    is_flag=True,
    help=(
        "Allow an unpublished candidate only for bounded tests; the pinned "
        "generator must record non-production provenance."
    ),
)
def adopt(
    standard_repository,
    source_revision,
    target_root,
    check,
    upgrade,
    allow_unpublished_for_testing,
):
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
        _checkout_standard(
            standard_repository,
            source_revision,
            standard,
            allow_unpublished_for_testing=allow_unpublished_for_testing,
        )
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
        if allow_unpublished_for_testing:
            command.append("--allow-unpublished-for-testing")

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, err=True, nl=False)
        if result.returncode != 0:
            raise click.exceptions.Exit(result.returncode)


__all__ = [
    "governance",
    "governance_check",
    "workspace_check",
    "adopt",
    "delivery_hook",
    "verify_delivery",
]
