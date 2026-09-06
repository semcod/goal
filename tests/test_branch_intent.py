"""The CLI must not execute unpinned code or turn readiness into authority."""
import hashlib
import json
import subprocess

import click
import pytest
from click.testing import CliRunner

from goal.cli.governance_cmd import branch_intent_check
from goal.governance import branch_intent


@pytest.fixture
def adopted(tmp_path):
    target = tmp_path / "target with spaces"
    target.mkdir()
    (target / ".governance").mkdir()
    report = tmp_path / "report.json"
    observation = tmp_path / "observation.json"
    report.write_text("{}")
    observation.write_text("{}")
    evidence = tmp_path / "evidence"
    evidence.mkdir()

    def install(code=None, exit_code=0, status="ready-for-owner-review", authority="none", authorized=False):
        result = {"status": status, "authority": authority, "deletionAuthorized": authorized}
        code = code or f"import json\nprint({json.dumps(result)!r})\nraise SystemExit({exit_code})\n"
        data = code.encode()
        (target / branch_intent.CHECKER).write_bytes(data)
        lock = {"schema": "new-project.lock/v1",
                "standard": {"id": "wellmanifest/new-project", "publicationStatus": "published", "sourceRevision": "a" * 40},
                "managedFiles": {branch_intent.CHECKER: hashlib.sha256(data).hexdigest()}}
        content = json.dumps(lock).encode()
        (target / branch_intent.LOCK).write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    pin = install()
    return target, report, observation, evidence, install, pin


def run(adopted, pin=None, timeout=5):
    target, report, observation, evidence, _, default = adopted
    return branch_intent.run_check(target, report, observation, evidence, pin or default, timeout)


@pytest.mark.parametrize("code,status", [(0, "ready-for-owner-review"), (1, "needs-review"), (2, "invalid")])
def test_preserves_readiness_exit_codes_without_writes(adopted, code, status):
    target, report, observation, evidence, install, _ = adopted
    pin = install(exit_code=code, status=status)
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    result = run(adopted, pin)
    assert result.returncode == code
    assert json.loads(result.stdout)["deletionAuthorized"] is False
    assert before == {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    args = ["--target-root", str(target), "--report", str(report), "--observation", str(observation),
            "--evidence-root", str(evidence), "--expected-lock-sha256", pin]
    cli = CliRunner().invoke(branch_intent_check, args)
    assert cli.exit_code == code, cli.output
    assert json.loads(cli.output)["status"] == status


def test_refuses_unpinned_lock_before_execution(adopted, monkeypatch):
    monkeypatch.setattr(branch_intent.subprocess, "run", lambda *a, **k: pytest.fail("must not execute"))
    with pytest.raises(click.ClickException, match="independently supplied digest"):
        run(adopted, "0" * 64)


def test_refuses_tampered_checker(adopted):
    (adopted[0] / branch_intent.CHECKER).write_text("raise Exception('untrusted')")
    with pytest.raises(click.ClickException, match="checker digest mismatch"):
        run(adopted)


@pytest.mark.parametrize("relative", [branch_intent.CHECKER, branch_intent.LOCK])
def test_refuses_missing_adopted_artifact(adopted, relative):
    (adopted[0] / relative).unlink()
    with pytest.raises(click.ClickException, match="adopted artifact is missing"):
        run(adopted)


def test_old_standard_missing_checker_pin_requires_adoption(adopted):
    lock_file = adopted[0] / branch_intent.LOCK
    lock = json.loads(lock_file.read_text())
    lock["managedFiles"] = {}
    data = json.dumps(lock).encode()
    lock_file.write_bytes(data)
    with pytest.raises(click.ClickException, match="adopt a published standard package"):
        run(adopted, hashlib.sha256(data).hexdigest())


def test_refuses_unpublished_standard(adopted):
    lock_file = adopted[0] / branch_intent.LOCK
    lock = json.loads(lock_file.read_text())
    lock["standard"]["publicationStatus"] = "draft"
    data = json.dumps(lock).encode()
    lock_file.write_bytes(data)
    with pytest.raises(click.ClickException, match="published immutable"):
        run(adopted, hashlib.sha256(data).hexdigest())


@pytest.mark.parametrize("relative", [branch_intent.CHECKER, branch_intent.LOCK, ".governance"])
def test_refuses_symlinks_in_managed_paths(adopted, relative):
    source = adopted[0] / relative
    saved = adopted[0] / "saved"
    source.rename(saved)
    source.symlink_to(saved, target_is_directory=saved.is_dir())
    with pytest.raises(click.ClickException, match="symlinked managed path"):
        run(adopted)


@pytest.mark.parametrize("kwargs", [{"authorized": True}, {"authority": "trusted"}, {"status": "needs-review"}, {"exit_code": 5}])
def test_does_not_accept_unauthorized_or_inconsistent_output(adopted, kwargs):
    pin = adopted[4](**kwargs)
    with pytest.raises(click.ClickException, match="invalid result"):
        run(adopted, pin)


def test_executes_frozen_bytes_if_path_changes(adopted, monkeypatch):
    real_run = subprocess.run

    def replace_before_spawn(*args, **kwargs):
        (adopted[0] / branch_intent.CHECKER).write_text("raise Exception('replacement executed')")
        return real_run(*args, **kwargs)

    monkeypatch.setattr(branch_intent.subprocess, "run", replace_before_spawn)
    assert run(adopted).returncode == 0


def test_imports_ignore_target_and_pythonpath(adopted, monkeypatch):
    (adopted[0] / "json.py").write_text("raise Exception('checkout module imported')")
    monkeypatch.setenv("PYTHONPATH", str(adopted[0]))
    assert run(adopted).returncode == 0


def test_timeout_fails_closed(adopted, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("checker", kwargs["timeout"])

    monkeypatch.setattr(branch_intent.subprocess, "run", timeout)
    with pytest.raises(click.ClickException, match="could not complete"):
        run(adopted)


def test_duplicate_lock_keys_are_rejected(adopted):
    data = b'{"schema":"new-project.lock/v1","schema":"other"}'
    (adopted[0] / branch_intent.LOCK).write_bytes(data)
    with pytest.raises(click.ClickException, match="duplicate JSON key"):
        run(adopted, hashlib.sha256(data).hexdigest())


def test_help_explains_trust_and_authority():
    result = CliRunner().invoke(branch_intent_check, ["--help"])
    assert result.exit_code == 0
    assert "never grants" in result.output
    assert "--expected-lock-sha256" in result.output


def test_command_is_registered_in_goal_governance():
    from goal.cli import main

    result = CliRunner().invoke(main, ["governance", "branch-intent-check", "--help"])
    assert result.exit_code == 0, result.output
    assert "--expected-lock-sha256" in result.output


def test_preflight_failure_does_not_masquerade_as_unresolved(adopted):
    target, report, observation, evidence, _, _ = adopted
    result = CliRunner().invoke(branch_intent_check, ["--target-root", str(target),
        "--report", str(report), "--observation", str(observation), "--evidence-root", str(evidence),
        "--expected-lock-sha256", "0" * 64])
    assert result.exit_code == 2
    assert "preflight refused" in result.output
