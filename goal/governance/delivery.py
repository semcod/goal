"""Governed delivery policy, local push authorization, and PR delivery."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import subprocess
import sys
import time
from typing import Any, Callable, Iterator

import click


DELIVERY_MODES = ("direct-main", "publish-only", "pull-request")
HOOK_START = "# GOAL-GOVERNANCE-DELIVERY:START"
HOOK_END = "# GOAL-GOVERNANCE-DELIVERY:END"
TRANSACTION_ENV = "GOAL_DELIVERY_TRANSACTION"
CAPABILITY_ENV = "GOAL_DELIVERY_CAPABILITY"
TRANSACTION_TTL_SECONDS = 300
PULL_REQUEST_HEAD_ATTEMPTS = 4
PULL_REQUEST_HEAD_RETRY_SECONDS = 1.0
GOVERNANCE_PACKAGE_FILES = {
    "validator": ".governance/governance_check.py",
    "manifest": ".governance/manifest.json",
    "lock": ".governance/manifest.lock.json",
    "stack profiles": ".governance/stack-profiles.json",
}
GOVERNANCE_DIAGNOSTICS = ".governance/diagnostics.json"
SOURCE_HUB_FILES = (
    "governance/package-manifest.json",
    "governance/manifest.default.json",
    "scripts/governance_check.py",
)
SOURCE_HUB_WORKFLOW = ".github/workflows/ci.yml"
SOURCE_HUB_REQUIRED_CHECKS = "scripts/check_required_checks.py"
SOURCE_HUB_JSON_DIRECTORY = "governance"
SOURCE_HUB_TEST_DIRECTORY = "tests"
SOURCE_HUB_DIAGNOSTIC = "GOV-HUB-001"
DIAGNOSTIC_CODE_PATTERN = re.compile(r"\bGOV-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")


@dataclass(frozen=True)
class DeliveryPolicy:
    """Resolved, validated delivery policy for one Goal invocation."""

    mode: str
    require_goal_a: bool
    allowed_modes: tuple[str, ...]
    remote: str
    base_branch: str
    require_clean_governance: bool


@dataclass(frozen=True)
class SourceHubHealthResult:
    """Bounded output from one source-hub health execution."""

    returncode: int
    stdout: str
    stderr: str
    completed_checks: int


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _delivery_section(config: Any) -> Any:
    if config is None:
        return None
    if isinstance(config, dict):
        governance = config.get("governance")
        if governance is None:
            return None
        if not isinstance(governance, dict):
            raise click.ClickException("governance must be a mapping")
        return governance.get("delivery")
    if hasattr(config, "get"):
        return config.get("governance.delivery", None)
    return None


def _clean_name(value: Any, field: str) -> str:
    result = str(value or "").strip()
    if not result or re.fullmatch(r"[A-Za-z0-9._/-]+", result) is None:
        raise click.ClickException(f"governance.delivery.{field} is invalid")
    return result


def resolve_delivery_policy(
    config: Any,
    requested_mode: str | None,
    *,
    all_flags: bool,
) -> DeliveryPolicy | None:
    """Resolve config plus CLI selection, preserving legacy behavior when absent."""
    section = _delivery_section(config)
    if section is None and requested_mode is None:
        return None
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise click.ClickException("governance.delivery must be a mapping")

    allowed_raw = section.get("allowed_modes", list(DELIVERY_MODES))
    if not isinstance(allowed_raw, list) or not allowed_raw:
        raise click.ClickException(
            "governance.delivery.allowed_modes must be a non-empty list"
        )
    allowed = tuple(str(item).strip() for item in allowed_raw)
    invalid = sorted(set(allowed) - set(DELIVERY_MODES))
    if invalid:
        raise click.ClickException(
            "unsupported governance delivery mode(s): " + ", ".join(invalid)
        )

    default_mode = str(section.get("default_mode", "pull-request") or "").strip()
    mode = str(requested_mode or default_mode).strip()
    if mode not in DELIVERY_MODES:
        raise click.ClickException(f"unsupported governance delivery mode: {mode}")
    if mode not in allowed:
        raise click.ClickException(
            f"delivery mode '{mode}' is forbidden by governance.delivery.allowed_modes"
        )

    require_goal_a = section.get("require_goal_a", True)
    require_clean = section.get("require_clean_governance", True)
    if not isinstance(require_goal_a, bool) or not isinstance(require_clean, bool):
        raise click.ClickException(
            "require_goal_a and require_clean_governance must be booleans"
        )
    if require_goal_a and not all_flags:
        raise click.ClickException(
            "governance requires the full workflow; use `goal -a`"
        )

    return DeliveryPolicy(
        mode=mode,
        require_goal_a=require_goal_a,
        allowed_modes=allowed,
        remote=_clean_name(section.get("remote", "origin"), "remote"),
        base_branch=_clean_name(section.get("base_branch", "main"), "base_branch"),
        require_clean_governance=require_clean,
    )


def _run(arguments: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        arguments,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_value(*arguments: str, cwd: Path | None = None) -> str:
    result = _run(["git", *arguments], cwd=cwd)
    if result.returncode != 0:
        raise click.ClickException(
            (result.stderr or "git command failed").strip()
        )
    return result.stdout.strip()


def _repository_root(cwd: Path | None = None) -> Path:
    return Path(_git_value("rev-parse", "--show-toplevel", cwd=cwd)).resolve()


def _git_dir(root: Path) -> Path:
    raw = Path(_git_value("rev-parse", "--git-dir", cwd=root))
    return (raw if raw.is_absolute() else root / raw).resolve()


def missing_governance_package_files(root: Path) -> list[str]:
    """Return missing files from the adopted target package contract."""
    return [
        relative
        for relative in GOVERNANCE_PACKAGE_FILES.values()
        if not (root / relative).is_file()
    ]


def is_new_project_source_hub(root: Path) -> bool:
    return all((root / relative).is_file() for relative in SOURCE_HUB_FILES)


def _source_hub_failure(
    message: str, *, stdout: str = "", completed: int = 0
) -> SourceHubHealthResult:
    return SourceHubHealthResult(
        returncode=1,
        stdout=stdout,
        stderr=f"{SOURCE_HUB_DIAGNOSTIC}: {message}\n",
        completed_checks=completed,
    )


def _source_hub_contract(
    root: Path,
) -> tuple[list[Path], list[list[str]]] | SourceHubHealthResult:
    workflow = root / SOURCE_HUB_WORKFLOW
    required_checks = root / SOURCE_HUB_REQUIRED_CHECKS
    if not workflow.is_file():
        return _source_hub_failure(
            f"missing authoritative workflow {SOURCE_HUB_WORKFLOW}"
        )
    if not required_checks.is_file():
        return _source_hub_failure(
            f"missing required-check comparison {SOURCE_HUB_REQUIRED_CHECKS}"
        )

    json_files = sorted((root / SOURCE_HUB_JSON_DIRECTORY).glob("*.json"))
    suites = sorted((root / SOURCE_HUB_TEST_DIRECTORY).glob("*.test.sh"))
    if not json_files:
        return _source_hub_failure(
            "no canonical governance JSON documents were found"
        )
    if not suites:
        return _source_hub_failure("no source-hub shell test suites were found")

    try:
        workflow_text = workflow.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return _source_hub_failure(f"cannot read {SOURCE_HUB_WORKFLOW}: {error}")

    unwired = [
        suite.relative_to(root).as_posix()
        for suite in suites
        if f"bash {suite.relative_to(root).as_posix()}" not in workflow_text
    ]
    if unwired:
        return _source_hub_failure(
            "CI does not execute source-hub suite(s): " + ", ".join(unwired)
        )

    bash = shutil.which("bash")
    if bash is None:
        return _source_hub_failure(
            "bash is required to execute source-hub Linux suites"
        )
    commands = [[sys.executable, str(required_checks)]]
    commands.extend([bash, str(suite)] for suite in suites)
    return json_files, commands


def _source_hub_git_status(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def run_source_hub_health(
    root: Path,
    *,
    runner: Runner = subprocess.run,
) -> SourceHubHealthResult:
    """Execute the canonical source-hub Linux contract without repository writes."""
    target = root.resolve()
    contract = _source_hub_contract(target)
    if isinstance(contract, SourceHubHealthResult):
        return contract
    json_files, commands = contract
    initial_status = _source_hub_git_status(target)

    for document in json_files:
        try:
            with document.open(encoding="utf-8") as stream:
                json.load(stream)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            relative = document.relative_to(target).as_posix()
            return _source_hub_failure(
                f"invalid canonical JSON {relative}: {error}"
            )

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    completed = 0
    for command in commands:
        try:
            result = runner(
                command,
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            return _source_hub_failure(
                f"cannot execute source-hub check {Path(command[-1]).name}: {error}",
                stdout="".join(stdout_parts),
                completed=completed,
            )
        stdout_parts.append(result.stdout or "")
        if result.returncode != 0:
            stderr_parts.append(result.stderr or "")
            label = Path(command[-1]).relative_to(target).as_posix()
            stderr_parts.append(
                f"{SOURCE_HUB_DIAGNOSTIC}: source-hub check failed: {label}\n"
            )
            return SourceHubHealthResult(
                returncode=result.returncode,
                stdout="".join(stdout_parts),
                stderr="".join(stderr_parts),
                completed_checks=completed,
            )
        completed += 1

    final_status = _source_hub_git_status(target)
    if initial_status is not None and final_status != initial_status:
        return _source_hub_failure(
            "source-hub health changed the repository working tree",
            stdout="".join(stdout_parts),
            completed=completed,
        )

    stdout_parts.append(
        "GOV-HUB-PASS: source-hub health passed "
        f"({len(json_files)} JSON documents, {len(commands) - 1} shell suites)\n"
    )
    return SourceHubHealthResult(
        returncode=0,
        stdout="".join(stdout_parts),
        stderr="".join(stderr_parts),
        completed_checks=completed,
    )


def _safe_runbook(root: Path, raw_path: Any) -> str | None:
    if not isinstance(raw_path, str) or not raw_path.strip() or "\\" in raw_path:
        return None
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    try:
        package = (root / ".governance").resolve()
        candidate = (package / Path(*relative.parts)).resolve()
        valid = candidate.is_relative_to(package) and candidate.is_file()
    except (OSError, RuntimeError, ValueError):
        return None
    if not valid:
        return None
    return (Path(".governance") / Path(*relative.parts)).as_posix()


def governance_diagnostic_guidance(root: Path, output: str) -> list[str]:
    """Resolve safe canonical v2 guidance for codes emitted by a validator."""
    catalog_path = root / GOVERNANCE_DIAGNOSTICS
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    if (
        not isinstance(catalog, dict)
        or catalog.get("schema") not in {
            "new-project.diagnostics/v1",
            "new-project.diagnostics/v2",
        }
        or not isinstance(catalog.get("codes"), dict)
    ):
        return []

    codes = list(dict.fromkeys(DIAGNOSTIC_CODE_PATTERN.findall(output)))
    guidance: list[str] = []
    for code in codes:
        entry = catalog["codes"].get(code)
        # v1 intentionally contains messages only. Preserve compatibility but
        # do not invent a remediation that the pinned standard did not publish.
        if catalog["schema"] == "new-project.diagnostics/v1":
            continue
        if not isinstance(entry, dict):
            continue
        remediation = entry.get("remediation")
        if isinstance(remediation, str) and remediation.strip():
            guidance.append(
                f"canonical remediation for {code}: {remediation.strip()}"
            )
        runbook = _safe_runbook(root, entry.get("documentation"))
        if runbook is not None:
            guidance.append(f"runbook for {code}: {runbook}")
    return guidance


def _governance_gate(root: Path) -> None:
    missing = missing_governance_package_files(root)
    if missing:
        if is_new_project_source_hub(root):
            result = run_source_hub_health(root)
            if result.returncode == 0:
                return
            detail = "\n".join(
                part.strip()
                for part in (result.stdout, result.stderr)
                if part.strip()
            ) or "source-hub health failed"
            raise click.ClickException(detail)
        raise click.ClickException(
            "GOV-MANIFEST-001: governance delivery requires a complete adopted "
            "package; missing: "
            + ", ".join(missing)
            + "; run `goal governance adopt` with a published source revision"
        )

    gate = root / "project" / "governance-check.sh"
    if not gate.is_file():
        raise click.ClickException(
            "governance delivery requires project/governance-check.sh"
        )
    result = _run([str(gate)], cwd=root)
    if result.returncode != 0:
        detail = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        ) or "governance gate failed"
        guidance = governance_diagnostic_guidance(root, detail)
        if guidance:
            detail += "\n" + "\n".join(guidance)
        raise click.ClickException(detail)


def validate_delivery_ready(policy: DeliveryPolicy, *, cwd: Path | None = None) -> None:
    """Fail before workflow side effects when delivery prerequisites are unmet."""
    root = _repository_root(cwd)
    if policy.require_clean_governance:
        _governance_gate(root)

    if policy.mode == "publish-only":
        status = _git_value("status", "--porcelain", cwd=root)
        if status:
            raise click.ClickException(
                "publish-only requires a clean working tree before bootstrap"
            )

        remote_ref = f"refs/heads/{policy.base_branch}"
        remote = _run(
            ["git", "ls-remote", "--heads", policy.remote, remote_ref],
            cwd=root,
        )
        if remote.returncode != 0:
            detail = (remote.stderr or "remote base lookup failed").strip()
            raise click.ClickException(
                f"publish-only could not resolve authoritative {policy.remote}/{policy.base_branch}: {detail}"
            )
        remote_rows = [line.split() for line in remote.stdout.splitlines() if line.strip()]
        if len(remote_rows) != 1 or len(remote_rows[0]) != 2:
            raise click.ClickException(
                f"publish-only requires exactly one authoritative {policy.remote}/{policy.base_branch} head"
            )
        local_head = _git_value("rev-parse", "HEAD", cwd=root)
        remote_head = remote_rows[0][0]
        if local_head != remote_head:
            raise click.ClickException(
                "publish-only requires HEAD to equal the authoritative remote base "
                f"({local_head[:12]} != {remote_head[:12]})"
            )

    if policy.mode == "direct-main":
        branch = _git_value("branch", "--show-current", cwd=root)
        if branch != policy.base_branch:
            raise click.ClickException(
                f"direct-main requires branch '{policy.base_branch}', current branch is '{branch}'"
            )

    if policy.mode == "pull-request":
        if shutil.which("gh") is None:
            raise click.ClickException(
                "pull-request delivery requires the authenticated `gh` CLI"
            )
        auth = _run(["gh", "auth", "status"], cwd=root)
        if auth.returncode != 0:
            raise click.ClickException(
                "pull-request delivery requires `gh auth login`"
            )


def _audit_path(root: Path) -> Path:
    directory = root / ".governance"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "delivery-events.jsonl"


def record_delivery_event(
    policy: DeliveryPolicy,
    result: str,
    *,
    detail: str = "",
    head: str = "",
    cwd: Path | None = None,
) -> None:
    """Append a credential-free delivery event."""
    root = _repository_root(cwd)
    commit = _git_value("rev-parse", "HEAD", cwd=root)
    branch = _git_value("branch", "--show-current", cwd=root)
    event = {
        "base": policy.base_branch,
        "branch": branch,
        "commit": commit,
        "detail": detail,
        "head": head,
        "mode": policy.mode,
        "remote": policy.remote,
        "result": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with _audit_path(root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


@contextmanager
def authorized_push(
    policy: DeliveryPolicy,
    *,
    cwd: Path | None = None,
) -> Iterator[None]:
    """Create a short-lived file-backed capability inherited by Git hooks."""
    root = _repository_root(cwd)
    directory = _git_dir(root) / "goal-delivery"
    directory.mkdir(parents=True, exist_ok=True)
    capability = secrets.token_urlsafe(32)
    transaction = directory / f"{secrets.token_hex(16)}.json"
    payload = {
        "expires": int(time.time()) + TRANSACTION_TTL_SECONDS,
        "mode": policy.mode,
        "remote": policy.remote,
        "tokenHash": hashlib.sha256(capability.encode("utf-8")).hexdigest(),
    }
    transaction.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    transaction.chmod(0o600)
    previous_path = os.environ.get(TRANSACTION_ENV)
    previous_capability = os.environ.get(CAPABILITY_ENV)
    os.environ[TRANSACTION_ENV] = str(transaction)
    os.environ[CAPABILITY_ENV] = capability
    try:
        yield
    finally:
        if previous_path is None:
            os.environ.pop(TRANSACTION_ENV, None)
        else:
            os.environ[TRANSACTION_ENV] = previous_path
        if previous_capability is None:
            os.environ.pop(CAPABILITY_ENV, None)
        else:
            os.environ[CAPABILITY_ENV] = previous_capability
        transaction.unlink(missing_ok=True)


def authorize_hook_push(
    policy: DeliveryPolicy | None,
    remote_name: str,
    *,
    cwd: Path | None = None,
) -> bool:
    """Validate a Goal-created capability for a managed pre-push hook."""
    if policy is None or not policy.require_goal_a:
        return True
    root = _repository_root(cwd)
    raw_path = os.environ.get(TRANSACTION_ENV, "")
    capability = os.environ.get(CAPABILITY_ENV, "")
    if not raw_path or not capability:
        raise click.ClickException(
            "governance blocks raw git push; run `goal -a`"
        )
    transaction = Path(raw_path).resolve()
    allowed_directory = (_git_dir(root) / "goal-delivery").resolve()
    if not transaction.is_relative_to(allowed_directory) or not transaction.is_file():
        raise click.ClickException("invalid Goal delivery transaction")
    try:
        payload = json.loads(transaction.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise click.ClickException("invalid Goal delivery transaction") from error
    expected = hashlib.sha256(capability.encode("utf-8")).hexdigest()
    valid = (
        secrets.compare_digest(str(payload.get("tokenHash", "")), expected)
        and int(payload.get("expires", 0)) >= int(time.time())
        and payload.get("remote") == remote_name
        and payload.get("remote") == policy.remote
        and payload.get("mode") in policy.allowed_modes
    )
    if not valid:
        raise click.ClickException("expired or mismatched Goal delivery transaction")
    return True


def _hook_path(root: Path) -> Path:
    return _git_dir(root) / "hooks" / "pre-push"


def _managed_hook_block() -> str:
    return (
        f"{HOOK_START}\n"
        "if ! command -v goal >/dev/null 2>&1; then\n"
        "  echo 'governance requires Goal, but goal is not on PATH' >&2\n"
        "  exit 1\n"
        "fi\n"
        "goal governance authorize-push \"$@\" || exit $?\n"
        f"{HOOK_END}\n"
    )


def install_delivery_hook(*, cwd: Path | None = None) -> Path:
    """Append the managed block while preserving an existing pre-push hook."""
    root = _repository_root(cwd)
    path = _hook_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "#!/bin/sh\n"
    if HOOK_START not in existing:
        separator = "" if existing.endswith("\n") else "\n"
        path.write_text(existing + separator + _managed_hook_block(), encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    return path


def check_delivery_hook(*, cwd: Path | None = None) -> bool:
    path = _hook_path(_repository_root(cwd))
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return HOOK_START in text and HOOK_END in text and os.access(path, os.X_OK)


def remove_delivery_hook(*, cwd: Path | None = None) -> Path:
    """Remove only Goal's bounded block and preserve project-owned hook logic."""
    root = _repository_root(cwd)
    path = _hook_path(root)
    if not path.exists():
        return path
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"\n?{re.escape(HOOK_START)}.*?{re.escape(HOOK_END)}\n?",
        re.DOTALL,
    )
    cleaned = pattern.sub("\n", text).rstrip() + "\n"
    path.write_text(cleaned, encoding="utf-8")
    return path


def _pr_head(ticket: str | None, root: Path) -> str:
    identity = ticket or _git_value("rev-parse", "--short=12", "HEAD", cwd=root)
    slug = re.sub(r"[^a-z0-9-]+", "-", identity.lower()).strip("-")
    return f"goal/{slug or 'change'}"


def _find_open_pull_request(
    policy: DeliveryPolicy,
    head: str,
    root: Path,
) -> str | None:
    """Resolve one open PR and bind it to the currently pushed commit."""
    expected_head = _git_value("rev-parse", "HEAD", cwd=root)
    for attempt in range(PULL_REQUEST_HEAD_ATTEMPTS):
        result = _run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--head",
                head,
                "--base",
                policy.base_branch,
                "--limit",
                "2",
                "--json",
                "url,headRefOid",
            ],
            cwd=root,
        )
        if result.returncode != 0:
            raise click.ClickException(
                "could not query open pull requests: "
                + (result.stderr or "unknown gh error").strip()
            )
        try:
            matches = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise click.ClickException(
                "could not query open pull requests: gh returned invalid JSON"
            ) from error
        if not isinstance(matches, list):
            raise click.ClickException(
                "could not query open pull requests: gh returned an invalid result"
            )
        if len(matches) > 1:
            raise click.ClickException(
                f"multiple open pull requests use governed branch '{head}'"
            )
        if not matches:
            return None

        match = matches[0]
        if not isinstance(match, dict):
            raise click.ClickException(
                "could not query open pull requests: gh returned an invalid entry"
            )
        url = str(match.get("url", "")).strip()
        actual_head = str(match.get("headRefOid", "")).strip()
        if not url or not actual_head:
            raise click.ClickException(
                "open pull request is missing its URL or head commit"
            )
        if actual_head == expected_head:
            return url
        if attempt + 1 < PULL_REQUEST_HEAD_ATTEMPTS:
            time.sleep(PULL_REQUEST_HEAD_RETRY_SECONDS)
            continue
        raise click.ClickException(
            f"open pull request for '{head}' targets {actual_head}, "
            f"not current pushed HEAD {expected_head}"
        )

    raise AssertionError("pull-request head retry loop exhausted unexpectedly")


def deliver_pull_request(
    policy: DeliveryPolicy,
    *,
    ticket: str | None,
    title: str,
    cwd: Path | None = None,
) -> tuple[str, str]:
    """Push a controlled head branch and create or reuse its pull request."""
    root = _repository_root(cwd)
    head = _pr_head(ticket, root)
    current = _git_value("branch", "--show-current", cwd=root)
    if current != head:
        switch = _run(["git", "switch", "-c", head], cwd=root)
        if switch.returncode != 0:
            raise click.ClickException(
                f"could not create controlled PR branch '{head}': "
                + (switch.stderr or "unknown git error").strip()
            )
    with authorized_push(policy, cwd=root):
        pushed = _run(["git", "push", "-u", policy.remote, head], cwd=root)
    if pushed.returncode != 0:
        raise click.ClickException(
            f"could not push PR branch '{head}': "
            + (pushed.stderr or "unknown git error").strip()
        )

    existing_url = _find_open_pull_request(policy, head, root)
    if existing_url is not None:
        return head, existing_url

    created = _run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            policy.base_branch,
            "--head",
            head,
            "--title",
            title,
            "--body",
            "Created by governed goal -a pull-request delivery.",
        ],
        cwd=root,
    )
    if created.returncode != 0:
        raise click.ClickException(
            "could not create pull request: "
            + (created.stderr or "unknown gh error").strip()
        )
    created_url = _find_open_pull_request(policy, head, root)
    if created_url is None:
        raise click.ClickException(
            "gh pr create reported success, but no matching open pull request exists"
        )
    return head, created_url


def policy_payload(policy: DeliveryPolicy | None) -> dict[str, Any]:
    if policy is None:
        return {
            "enabled": False,
            "localHookIsSecurityBoundary": False,
            "serverEnforcementRequired": True,
        }
    payload = asdict(policy)
    payload["allowed_modes"] = list(policy.allowed_modes)
    return {
        "enabled": True,
        "policy": payload,
        "localHookIsSecurityBoundary": False,
        "serverEnforcementRequired": True,
    }
