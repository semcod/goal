"""No-network regression coverage for deterministic advisory adoption planning."""

from hashlib import sha256
import json
import subprocess

import pytest
from click.testing import CliRunner

from goal.cli.governance_cmd import governance
from goal.governance import adoption_plan as planner


A, B, C, D = (character * 40 for character in "abcd")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def edge(source, target):
    return {"fromRevision": source, "toRevision": target, "recipe": planner.RECIPE}


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "target"
    (root / ".governance").mkdir(parents=True)
    lock = {"schema": "new-project.lock/v1", "standard": {
        "id": planner.STANDARD, "sourceRepository": planner.STANDARD,
        "publicationStatus": "published", "sourceRevision": A}}
    (root / planner.LOCK_PATH).write_text(json.dumps(lock))
    git(root, "init", "-q")
    git(root, "config", "user.name", "Planner Test")
    git(root, "config", "user.email", "planner@example.invalid")
    git(root, "-c", "core.hooksPath=/dev/null", "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
    return root


@pytest.fixture
def catalog(tmp_path):
    def write(supported=(A, B), migrations=None, **overrides):
        data = {"schema": planner.CATALOG_SCHEMA, "standardRepository": planner.STANDARD,
                "supportedRevisions": list(supported),
                "migrations": [edge(A, B)] if migrations is None else migrations}
        data.update(overrides)
        raw = json.dumps(data).encode()
        path = tmp_path / "catalog.json"
        path.write_bytes(raw)
        return path, sha256(raw).hexdigest()
    return write


def test_supported_pin_retained_with_newer_release_and_dirty_product(checkout, catalog):
    (checkout / "product.txt").write_text("work in progress")
    plan = planner.plan_adoption(checkout, *catalog())
    assert (plan["state"], plan["reason"]) == ("retain", "supported_pin")
    assert plan["steps"] == []
    assert plan["dirty"] is True
    assert plan["productReadinessVerified"] is False


def test_explicit_destination_and_deterministic_plan(checkout, catalog):
    inputs = catalog()
    before = git(checkout, "status", "--porcelain")
    plan = planner.plan_adoption(checkout, *inputs, target_revision=B)
    assert plan == planner.plan_adoption(checkout, *inputs, target_revision=B)
    assert plan["state"] == "migration-planned"
    assert plan["authority"] == "advisory-only"
    assert plan["policyProvenanceVerified"] is False
    assert plan["headSha"] == git(checkout, "rev-parse", "HEAD")
    assert plan["catalogSha256"] == inputs[1]
    assert plan["steps"][0]["toRevision"] == B
    assert "--check" in plan["steps"][0]["checkArgv"]
    assert "--latest" not in plan["steps"][0]["checkArgv"]
    assert git(checkout, "status", "--porcelain") == before == ""


def test_shortest_route_stable_ties_and_cycles(checkout, catalog):
    edges = [edge(A, C), edge(C, A), edge(C, D), edge(A, B), edge(B, D)]
    plan = planner.plan_adoption(checkout, *catalog((D,), edges))
    assert [step["toRevision"] for step in plan["steps"]] == [B, D]
    reversed_plan = planner.plan_adoption(checkout, *catalog((D,), list(reversed(edges))))
    assert plan["steps"] == reversed_plan["steps"]
    assert plan["planId"] != reversed_plan["planId"]  # Different catalog byte pin.


@pytest.mark.parametrize("supported,migrations,target,reason", [
    ((B,), [], None, "migration_recipe_missing"),
    ((D,), [edge(A, B), edge(B, A)], None, "migration_recipe_missing"),
    ((A,), [edge(A, B)], B, "unsupported_destination"),
])
def test_missing_routes_fail_closed(checkout, catalog, supported, migrations, target, reason):
    plan = planner.plan_adoption(checkout, *catalog(supported, migrations), target)
    assert plan["state"] == "blocked"
    assert plan["reason"] == reason
    assert plan["steps"] == []


def test_dirty_migration_blocked(checkout, catalog):
    (checkout / "unknown.txt").write_text("preserve")
    plan = planner.plan_adoption(checkout, *catalog((B,)))
    assert plan["reason"] == "dirty_worktree"
    assert plan["steps"] == []
    assert (checkout / "unknown.txt").read_text() == "preserve"


def test_changed_lock_detected_even_assume_unchanged(checkout, catalog):
    git(checkout, "update-index", "--assume-unchanged", planner.LOCK_PATH)
    lock = checkout / planner.LOCK_PATH
    lock.write_text(lock.read_text() + "\n")
    plan = planner.plan_adoption(checkout, *catalog())
    assert plan["reason"] == "observation_changed"
    assert plan["steps"] == []


def test_changed_head_detected(checkout, catalog, monkeypatch):
    original = planner._git
    def observe(root, *args):
        if args == ("rev-parse", "HEAD"):
            return (D + "\n").encode()
        return original(root, *args)
    monkeypatch.setattr(planner, "_git", observe)
    assert planner.plan_adoption(checkout, *catalog())["reason"] == "observation_changed"


@pytest.mark.parametrize("overrides", [
    {"schema": "future/v2"}, {"standardRepository": "attacker/repo"},
    {"commands": ["touch pwned"]}, {"supportedRevisions": ["latest"]},
    {"supportedRevisions": [A, A]}, {"supportedRevisions": []},
    {"supportedRevisions": [None]}, {"supportedRevisions": {}},
    {"migrations": [edge(A, A)]}, {"migrations": [edge(A, B), edge(A, B)]},
    {"migrations": [{**edge(A, B), "recipe": "shell"}]},
    {"migrations": [{**edge(A, B), "command": "rm -rf target"}]},
    {"migrations": [{**edge(A, B), "toRevision": "main"}]},
    {"migrations": [None]}, {"migrations": {}},
    {"migrations": [edge(A, B)] * 257},
])
def test_invalid_catalog_rejected(catalog, overrides):
    with pytest.raises(planner.AdoptionPlanError):
        planner.load_catalog(*catalog(**overrides))


@pytest.mark.parametrize("raw", [b"[]", b"null", b"{", b"\xff",
                                    b'{"schema":1,"schema":2}', b"[" * 3000])
def test_malformed_json_rejected(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    with pytest.raises(planner.AdoptionPlanError):
        planner.load_catalog(path, sha256(raw).hexdigest())


def test_digest_and_size_bounds(catalog, tmp_path):
    path, digest = catalog()
    for bad_digest in ("latest", "f" * 64, digest.upper()):
        with pytest.raises(planner.AdoptionPlanError):
            planner.load_catalog(path, bad_digest)
    path.write_bytes(b" " * (planner.MAX_BYTES + 1))
    with pytest.raises(planner.AdoptionPlanError):
        planner.load_catalog(path, digest)


@pytest.mark.parametrize("field,value", [("publicationStatus", "candidate"),
                                          ("sourceRepository", "other/repo"),
                                          ("sourceRevision", "main")])
def test_unsupported_lock_rejected(checkout, catalog, field, value):
    path = checkout / planner.LOCK_PATH
    data = json.loads(path.read_text())
    data["standard"][field] = value
    path.write_text(json.dumps(data))
    git(checkout, "add", ".")
    git(checkout, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "bad lock")
    with pytest.raises(planner.AdoptionPlanError):
        planner.plan_adoption(checkout, *catalog())


def test_symlink_lock_rejected(checkout, catalog, tmp_path):
    path = checkout / planner.LOCK_PATH
    outside = tmp_path / "outside-lock.json"
    path.rename(outside)
    path.symlink_to(outside)
    with pytest.raises(planner.AdoptionPlanError, match="symlink"):
        planner.plan_adoption(checkout, *catalog())


def test_non_root_and_mutable_target_rejected(checkout, catalog):
    inputs = catalog()
    with pytest.raises(planner.AdoptionPlanError, match="checkout root"):
        planner.plan_adoption(checkout / ".governance", *inputs)
    with pytest.raises(planner.AdoptionPlanError, match="immutable"):
        planner.plan_adoption(checkout, *inputs, "latest")


def test_cli_json_and_no_network_or_llm(checkout, catalog, monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        pytest.fail("planner must not use network")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    path, digest = catalog()
    args = ["plan-adoption", "--target-root", str(checkout), "--catalog", str(path),
            "--catalog-sha256", digest]
    result = CliRunner().invoke(governance, args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["state"] == "retain"
    blocked = CliRunner().invoke(governance, [*args, "--target-revision", D])
    assert blocked.exit_code == 2
    assert json.loads(blocked.output)["state"] == "blocked"
    bad = CliRunner().invoke(governance, [*args, "--catalog-sha256", "0" * 64])
    assert bad.exit_code == 2
    assert json.loads(bad.output)["reason"] == "invalid_input"


def test_main_dispatcher_does_not_enter_mutable_setup(checkout, catalog, monkeypatch):
    import goal.cli as cli
    def forbidden(*args, **kwargs):
        pytest.fail("read-only planner entered mutable setup")
    for name in ("_warn_goal_binary_mismatch", "_warn_wheel_shadows_editable",
                 "_show_goal_version_banner", "_maybe_self_update", "ensure_config",
                 "get_user_config"):
        monkeypatch.setattr(cli, name, forbidden)
    monkeypatch.setattr(cli, "load_config", lambda *args, **kwargs: {})
    path, digest = catalog()
    result = CliRunner().invoke(cli.main, [
        "governance", "plan-adoption", "--target-root", str(checkout),
        "--catalog", str(path), "--catalog-sha256", digest])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["state"] == "retain"
