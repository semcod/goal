"""Catalog boundaries, exact-target resolution and read-only CLI checks."""

import json
import subprocess

from click.testing import CliRunner
import pytest

from goal import internal_dependencies as deps


def metadata(*versions):
    return {
        "releases": {
            version: [{"yanked": False, "requires_python": ">=3.9"}]
            for version in versions
        }
    }


def lock_text(version="0.1.53", source='registry = "https://pypi.org/simple"'):
    return (
        f'[[package]]\nname = "costs"\nversion = "{version}"\nsource = {{ {source} }}\n'
    )


@pytest.fixture
def project(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="demo"\nversion="0.1.0"\nrequires-python=">=3.10"\ndependencies=["costs"]\n'
    )
    (tmp_path / "uv.lock").write_text(lock_text())
    for args in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "base",
        ],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


@pytest.fixture
def catalog():
    return {
        "costs": {
            "name": "costs",
            "repository": "semcod/costs",
            "registry": "pypi",
            "versioning": "semver",
        }
    }


def observe(project, catalog):
    return deps.audit(project, catalog, fetch=lambda name: metadata("0.1.53", "0.2.0"))


def resolver(monkeypatch, callback):
    original = deps._run

    def run(command, cwd, timeout=120):
        if command[0] == "git":
            return original(command, cwd, timeout)
        return callback(command, cwd)

    monkeypatch.setattr(deps, "_run", run)


def test_stable_semver_uses_numeric_order_excludes_empty_yanked_and_prerelease():
    doc = metadata("0.9.0", "0.10.0", "0.11.0rc1", "0.11.0.dev1", "1.0.0")
    doc["releases"]["1.0.0"][0]["yanked"] = True
    doc["releases"]["2.0.0"] = []
    assert deps.latest_release(doc)["target"] == "0.10.0"


def test_no_stable_artifact_is_an_error():
    with pytest.raises(ValueError, match="No published"):
        deps.latest_release(metadata("1.0.0rc1"))


@pytest.mark.parametrize(
    "change",
    [
        {"name": "costs;touch /tmp/unexpected"},
        {"registry": "private"},
        {"versioning": "pep440"},
        {"repository": ""},
    ],
)
def test_catalog_rejects_unsupported_or_ambiguous_inputs(tmp_path, catalog, change):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            {"schema": deps.SCHEMA, "packages": [{**catalog["costs"], **change}]}
        )
    )
    with pytest.raises(ValueError):
        deps.read_catalog(path)


def test_catalog_normalization_and_duplicate_detection(tmp_path, catalog):
    path = tmp_path / "catalog.json"
    item = {**catalog["costs"], "name": "My_Tool"}
    path.write_text(json.dumps({"schema": deps.SCHEMA, "packages": [item]}))
    assert list(deps.read_catalog(path)) == ["my-tool"]
    path.write_text(
        json.dumps(
            {"schema": deps.SCHEMA, "packages": [item, {**item, "name": "my-tool"}]}
        )
    )
    with pytest.raises(ValueError, match="Duplicate"):
        deps.read_catalog(path)


@pytest.mark.parametrize(
    "source",
    [
        'editable = "."',
        'git = "https://example.com/pkg"',
        'registry = "https://private.example/simple"',
    ],
)
def test_source_policy_never_queries_public_registry(project, catalog, source):
    (project / "uv.lock").write_text(lock_text(source=source))
    report = deps.audit(
        project, catalog, fetch=lambda _: pytest.fail("must not query PyPI")
    )
    assert report["packages"][0]["status"] == "alternate-source"
    assert not report["fresh"]


def test_manifest_override_prevents_public_resolution(project, catalog):
    with (project / "pyproject.toml").open("a") as stream:
        stream.write('\n[tool.uv.sources]\ncosts={path="../costs"}\n')
    assert (
        deps.audit(project, catalog, fetch=lambda _: pytest.fail())["packages"][0][
            "status"
        ]
        == "alternate-source"
    )


def test_lock_variants_and_unrelated_names(project, catalog):
    with (project / "uv.lock").open("a") as stream:
        stream.write(lock_text("0.2.0"))
        stream.write('[[package]]\nname="third-party"\nversion="1.0.0"\n')
    report = observe(project, catalog)
    assert len(report["packages"]) == 1
    assert report["packages"][0]["locked"] == ["0.1.53", "0.2.0"]
    assert report["update_command"] == [
        "uv",
        "lock",
        "--upgrade-package",
        "costs==0.2.0",
    ]


def test_empty_matching_set_does_not_claim_freshness(project):
    report = deps.audit(project, {})
    assert not report["fresh"]
    with pytest.raises(ValueError, match="No catalogued"):
        deps.update_lock(project, report)


def test_metadata_failure_is_not_reported_as_current(project, catalog):
    def fail(name):
        raise TimeoutError("registry unavailable")

    report = deps.audit(project, catalog, fetch=fail)
    assert report["packages"][0]["status"] == "registry-error"
    assert not report["fresh"]


def test_successful_update_verifies_candidate_and_replaces_only_lock(
    project, catalog, monkeypatch
):
    report = observe(project, catalog)
    manifest = (project / "pyproject.toml").read_bytes()

    def resolve(command, candidate):
        assert candidate != project
        (candidate / "uv.lock").write_text(lock_text("0.2.0"))
        return subprocess.CompletedProcess(command, 0, "", "")

    resolver(monkeypatch, resolve)
    updated = deps.update_lock(project, report)
    assert updated["updated"] and updated["fresh"]
    assert updated["packages"][0]["locked"] == ["0.2.0"]
    assert not updated["application_tests_run"]
    assert (project / "pyproject.toml").read_bytes() == manifest
    assert not (project / ".venv").exists()
    assert not (project / ".git/goal-internal-dependencies.lock").exists()


@pytest.mark.parametrize(
    "failure", ["conflict", "timeout", "old-version", "wrong-source"]
)
def test_failed_resolution_never_changes_original_lock(
    project, catalog, monkeypatch, failure
):
    report = observe(project, catalog)
    original = (project / "uv.lock").read_bytes()

    def resolve(command, candidate):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 120)
        if failure == "conflict":
            return subprocess.CompletedProcess(command, 1, "", "Python >=3.12 required")
        if failure == "wrong-source":
            (candidate / "uv.lock").write_text(lock_text("0.2.0", 'editable = "."'))
        return subprocess.CompletedProcess(command, 0, "", "")

    resolver(monkeypatch, resolve)
    with pytest.raises((ValueError, subprocess.TimeoutExpired)):
        deps.update_lock(project, report)
    assert (project / "uv.lock").read_bytes() == original
    assert not (project / ".git/goal-internal-dependencies.lock").exists()


def test_concurrent_user_edit_survives_failed_candidate(project, catalog, monkeypatch):
    report = observe(project, catalog)

    def resolve(command, candidate):
        (candidate / "uv.lock").write_text(lock_text("0.2.0"))
        (project / "uv.lock").write_text("# user's concurrent work\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    resolver(monkeypatch, resolve)
    with pytest.raises(ValueError, match="changed during"):
        deps.update_lock(project, report)
    assert (project / "uv.lock").read_text() == "# user's concurrent work\n"


def test_other_update_guard_is_preserved(project, catalog):
    guard = project / ".git/goal-internal-dependencies.lock"
    guard.write_text("another invocation")
    with pytest.raises(FileExistsError):
        deps.update_lock(project, observe(project, catalog))
    assert guard.read_text() == "another invocation"


def test_governed_checkout_requires_managed_delivery(project, catalog):
    (project / ".governance").mkdir()
    (project / ".governance/manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="delivery ticket"):
        deps.update_lock(project, observe(project, catalog))


@pytest.mark.parametrize("prefix", [[], ["-a"], ["auto"]])
def test_cli_check_and_global_dry_run_do_not_bootstrap_or_update(
    project, catalog, monkeypatch, prefix
):
    from goal.cli import main

    path = project.parent / "catalog.json"
    path.write_text(
        json.dumps({"schema": deps.SCHEMA, "packages": list(catalog.values())})
    )
    monkeypatch.chdir(project)
    monkeypatch.setattr(deps, "fetch_metadata", lambda _: metadata("0.2.0"))
    monkeypatch.setattr("goal.cli.ensure_config", lambda *a: pytest.fail("bootstrap"))
    monkeypatch.setattr(
        "goal.cli._maybe_self_update", lambda *a: pytest.fail("self update")
    )
    monkeypatch.setattr(
        "goal.cli.dependencies_cmd.update_lock", lambda *a: pytest.fail("update")
    )
    runner = CliRunner()
    result = runner.invoke(main, ["dependencies", "--catalog", str(path), "--check"])
    assert result.exit_code == 1, result.output
    assert json.loads(result.output)["packages"][0]["target"] == "0.2.0"
    result = runner.invoke(
        main, prefix + ["--dry-run", "dependencies", "--catalog", str(path), "--update"]
    )
    assert result.exit_code == 0, result.output
    assert not (project / "goal.yaml").exists()


def test_input_limits_and_symlinks(tmp_path, monkeypatch):
    path = tmp_path / "data"
    path.write_bytes(b"12345")
    monkeypatch.setattr(deps, "MAX_BYTES", 4)
    with pytest.raises(ValueError, match="exceeds"):
        deps.read_bytes(path)
    link = tmp_path / "linked"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="Symlink"):
        deps.read_bytes(link)
