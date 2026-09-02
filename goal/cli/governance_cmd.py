"""Adopt pinned wellmanifest/new-project governance into existing projects."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
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
    run_source_hub_health,
)

DEFAULT_STANDARD_REPOSITORY = "https://github.com/wellmanifest/new-project.git"
CANONICAL_STANDARD_RELEASES_API = (
    "https://api.github.com/repos/wellmanifest/new-project/releases/tags"
)
CANONICAL_STANDARD_LATEST_RELEASE_API = (
    "https://api.github.com/repos/wellmanifest/new-project/releases/latest"
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


def _github_api_headers():
    credential = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not credential:
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            credential = result.stdout.strip() if result.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            credential = ""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "goal-governance-adoption",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if credential:
        headers["Authorization"] = f"Bearer {credential}"
    return headers


def _load_github_release(tag):
    request = Request(
        f"{CANONICAL_STANDARD_RELEASES_API}/{quote(tag, safe='')}",
        headers=_github_api_headers(),
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


def _load_latest_github_release():
    request = Request(
        CANONICAL_STANDARD_LATEST_RELEASE_API,
        headers=_github_api_headers(),
    )
    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read(MAX_RELEASE_METADATA_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise click.ClickException(
            "the canonical standard has no verifiable latest GitHub Release"
        ) from error
    if len(raw) > MAX_RELEASE_METADATA_BYTES:
        raise click.ClickException(
            "the canonical latest GitHub Release metadata is unexpectedly large"
        )
    try:
        release = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise click.ClickException(
            "the canonical latest GitHub Release metadata is invalid"
        ) from error
    if not isinstance(release, dict):
        raise click.ClickException(
            "the canonical latest GitHub Release metadata is invalid"
        )
    tag = release.get("tag_name")
    published_at = release.get("published_at")
    if (
        not isinstance(tag, str)
        or re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag) is None
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(published_at, str)
        or not published_at.strip()
    ):
        raise click.ClickException(
            "the canonical latest GitHub Release is not a final semantic release"
        )
    return release


def _resolve_latest_published_revision(repository):
    """Resolve the latest final Release through its peeled annotated tag."""
    if repository != DEFAULT_STANDARD_REPOSITORY:
        raise click.UsageError(
            "--latest is restricted to the canonical wellmanifest/new-project repository"
        )
    tag = _load_latest_github_release()["tag_name"]
    refs = _run_git(
        [
            "ls-remote",
            "--tags",
            repository,
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
        ]
    )
    if refs.returncode != 0:
        raise click.ClickException(
            f"could not resolve the canonical standard release tag {tag}"
        )
    resolved = {}
    for line in refs.stdout.splitlines():
        fields = line.split("\t", 1)
        if len(fields) == 2 and FULL_SHA_PATTERN.fullmatch(fields[0]):
            resolved[fields[1]] = fields[0]
    tag_ref = f"refs/tags/{tag}"
    peeled_ref = f"{tag_ref}^{{}}"
    if tag_ref not in resolved or peeled_ref not in resolved:
        raise click.ClickException(
            f"the canonical standard release tag {tag} must be annotated"
        )
    return resolved[peeled_ref]


def _staged_text(target, relative_path):
    staged = _run_git(["show", f":{relative_path}"], cwd=target)
    if staged.returncode != 0:
        raise click.ClickException(
            "GOV-STANDARD-UPDATE-001: pre-commit standard update requires "
            f"staged {relative_path}"
        )
    return staged.stdout


def _staged_json(target, relative_path):
    try:
        value = json.loads(_staged_text(target, relative_path))
    except json.JSONDecodeError as error:
        raise click.ClickException(
            "GOV-STANDARD-UPDATE-001: pre-commit standard update found invalid "
            f"staged {relative_path}"
        ) from error
    if not isinstance(value, dict):
        raise click.ClickException(
            "GOV-STANDARD-UPDATE-001: pre-commit standard update requires an "
            f"object in staged {relative_path}"
        )
    return value


def _authorize_precommit_adoption(target, ticket, current_revision, revision):
    """Bind mutation to the staged ticket snapshot, never worktree-only prose."""
    if re.fullmatch(r"ticket-[0-9]{3,}", ticket) is None:
        raise click.BadParameter(
            "GOV-STANDARD-UPDATE-001: must use the canonical ticket-NNN "
            "identifier",
            param_hint="--ticket",
        )
    readme = _staged_text(target, f"project/{ticket}/README.md")
    if "- **Status**: IN_PROGRESS" not in readme:
        raise click.ClickException(
            "GOV-STANDARD-UPDATE-001: pre-commit standard update requires "
            f"staged {ticket} status IN_PROGRESS"
        )
    intent = _staged_json(target, f"project/{ticket}/intent.json")
    delivery = intent.get("delivery")
    adoption = (
        delivery.get("standardAdoption", {}) if isinstance(delivery, dict) else {}
    )
    expected = {
        "sourceRepository": "wellmanifest/new-project",
        "fromRevision": current_revision,
        "toRevision": revision,
    }
    if (
        intent.get("ticket") != ticket
        or intent.get("workstream") != "governance"
        or not isinstance(adoption, dict)
        or any(adoption.get(key) != value for key, value in expected.items())
    ):
        raise click.ClickException(
            "GOV-STANDARD-UPDATE-001: pre-commit standard update requires a "
            "staged governance adoption intent binding "
            f"{current_revision} to {revision} in {ticket}"
        )


def _staged_standard_revision(target):
    lock = _staged_json(target, ".governance/manifest.lock.json")
    standard = lock.get("standard")
    revision = standard.get("sourceRevision") if isinstance(standard, dict) else None
    if not isinstance(revision, str) or FULL_SHA_PATTERN.fullmatch(revision) is None:
        raise click.ClickException(
            "pre-commit standard update requires a valid staged standard sourceRevision"
        )
    return revision


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
            if validator_args:
                raise click.UsageError(
                    "source-hub health does not accept target-validator arguments"
                )
            result = run_source_hub_health(target)
            if result.stdout:
                click.echo(result.stdout, nl=False)
            if result.stderr:
                click.echo(result.stderr, err=True, nl=False)
            if result.returncode != 0:
                raise click.exceptions.Exit(result.returncode)
            return
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
@click.option(
    "--format", "output_format", type=click.Choice(("text", "json")), default="text"
)
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
    policy = resolve_delivery_policy(config, delivery_mode, all_flags=True)
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
    help="Published lowercase 40-character standard commit SHA.",
)
@click.option(
    "--latest",
    is_flag=True,
    help="Resolve the latest final canonical release to its immutable commit SHA.",
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
@click.option(
    "--pre-commit",
    is_flag=True,
    help="Prepare an authorized stale standard adoption and stop the commit.",
)
@click.option(
    "--ticket",
    help="Active governance adoption ticket used by --pre-commit.",
)
def adopt(
    standard_repository,
    source_revision,
    latest,
    target_root,
    check,
    upgrade,
    allow_unpublished_for_testing,
    pre_commit,
    ticket,
):
    """Adopt an immutable new-project revision into an existing project."""
    if bool(source_revision) == bool(latest):
        raise click.UsageError("provide exactly one of --source-revision or --latest")
    if source_revision and FULL_SHA_PATTERN.fullmatch(source_revision) is None:
        raise click.BadParameter(
            "must be a full lowercase 40-character commit SHA",
            param_hint="--source-revision",
        )
    if check and upgrade:
        raise click.UsageError("--check and --upgrade are mutually exclusive")
    if pre_commit and (not latest or not ticket):
        raise click.UsageError("--pre-commit requires --latest and --ticket")
    if pre_commit and (check or upgrade or allow_unpublished_for_testing):
        raise click.UsageError(
            "--pre-commit cannot be combined with --check, --upgrade, or "
            "--allow-unpublished-for-testing"
        )

    target = target_root.resolve()
    if not target.is_dir():
        raise click.BadParameter(
            "must identify an existing directory", param_hint="--target-root"
        )

    if latest:
        source_revision = _resolve_latest_published_revision(standard_repository)

    if pre_commit:
        current_revision = _staged_standard_revision(target)
        if current_revision == source_revision:
            click.echo(
                f"standard is current at {source_revision}; no pre-commit update needed"
            )
            return
        _authorize_precommit_adoption(target, ticket, current_revision, source_revision)
        upgrade = True

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
        if pre_commit:
            click.echo(
                f"prepared standard update {current_revision}..{source_revision} "
                f"for {ticket}; review and stage the generated changes"
            )
            raise click.exceptions.Exit(3)


__all__ = [
    "adopt",
    "delivery_hook",
    "governance",
    "governance_check",
    "verify_delivery",
    "workspace_check",
]
