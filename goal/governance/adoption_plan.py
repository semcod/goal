"""Offline new-project adoption planning; catalog data never grants authority.

Catalog v1 has exactly these keys::

    {"schema": "goal.adoption-catalog/v1",
     "standardRepository": "wellmanifest/new-project",
     "supportedRevisions": ["<40 lowercase hex characters>"],
     "migrations": [{"fromRevision": "<sha>", "toRevision": "<sha>",
                     "recipe": "goal-governance-adopt/v1"}]}

The caller supplies an independently acquired SHA-256 of the catalog bytes.
This binds input, not its issuer or freshness. A protected controller must
establish policy provenance, allocate a ticket/worktree, reobserve every step,
and enforce tests and independent review before any effect. No catalog is
implicitly fetched, trusted, or installed. V1 covers new-project only.
"""

from collections import deque
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


CATALOG_SCHEMA = "goal.adoption-catalog/v1"
PLAN_SCHEMA = "goal.adoption-plan/v1"
STANDARD = "wellmanifest/new-project"
RECIPE = "goal-governance-adopt/v1"
MAX_BYTES = 1024 * 1024
MAX_EDGES = 256
LOCK_PATH = ".governance/manifest.lock.json"
REVISION = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class AdoptionPlanError(ValueError):
    """Invalid or unobservable planning input; no migration may be inferred."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AdoptionPlanError("duplicate JSON key")
        result[key] = value
    return result


def _json(raw):
    if len(raw) > MAX_BYTES:
        raise AdoptionPlanError("JSON input exceeds 1 MiB")
    try:
        return json.loads(raw, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise AdoptionPlanError("invalid JSON input") from error


def _revision(value):
    return isinstance(value, str) and REVISION.fullmatch(value) is not None


def load_catalog(path, expected_digest):
    """Validate bounded closed-schema catalog bytes against an explicit pin."""
    if not isinstance(expected_digest, str) or not DIGEST.fullmatch(expected_digest):
        raise AdoptionPlanError("catalog SHA-256 must be 64 lowercase hex characters")
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise AdoptionPlanError("catalog exceeds 1 MiB")
    if sha256(raw).hexdigest() != expected_digest:
        raise AdoptionPlanError("catalog SHA-256 mismatch")
    catalog = _json(raw)
    keys = {"schema", "standardRepository", "supportedRevisions", "migrations"}
    if not isinstance(catalog, dict) or set(catalog) != keys:
        raise AdoptionPlanError("invalid catalog fields")
    if catalog["schema"] != CATALOG_SCHEMA or catalog["standardRepository"] != STANDARD:
        raise AdoptionPlanError("unsupported catalog schema or standard repository")
    supported = catalog["supportedRevisions"]
    if (not isinstance(supported, list) or not 1 <= len(supported) <= MAX_EDGES
            or not all(_revision(pin) for pin in supported)
            or len(set(supported)) != len(supported)):
        raise AdoptionPlanError("invalid supported revisions")
    edges = catalog["migrations"]
    if not isinstance(edges, list) or len(edges) > MAX_EDGES:
        raise AdoptionPlanError("invalid or excessive migrations")
    seen = set()
    for edge in edges:
        if (not isinstance(edge, dict)
                or set(edge) != {"fromRevision", "toRevision", "recipe"}
                or not _revision(edge["fromRevision"])
                or not _revision(edge["toRevision"])
                or edge["recipe"] != RECIPE):
            raise AdoptionPlanError("invalid migration or unsupported recipe")
        pair = (edge["fromRevision"], edge["toRevision"])
        if pair[0] == pair[1] or pair in seen:
            raise AdoptionPlanError("self migration or duplicate migration")
        seen.add(pair)
    return catalog


def _git(root, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise AdoptionPlanError("Git observation unavailable") from error
    if result.returncode:
        raise AdoptionPlanError("Git observation unavailable")
    return result.stdout


def _route(current, destinations, edges):
    adjacency = {}
    for edge in edges:
        adjacency.setdefault(edge["fromRevision"], []).append(edge["toRevision"])
    pending = deque([(current, [])])
    seen = {current}
    while pending:
        revision, route = pending.popleft()
        if revision in destinations:
            return route
        for target in sorted(adjacency.get(revision, [])):
            if target not in seen:
                seen.add(target)
                pending.append((target, [*route, target]))
    return None


def plan_adoption(target_root, catalog_path, catalog_sha256, target_revision=None):
    """Observe a Git checkout and return a deterministic advisory plan.

    Retain a supported pin unless a specific destination was requested. A
    migration requires a clean worktree and an explicit route to a supported
    destination. Shortest routes win, with lexical SHA ordering for ties.
    The plan is not a product readiness check or an execution authorization.
    """
    catalog = load_catalog(catalog_path, catalog_sha256)
    if target_revision is not None and not _revision(target_revision):
        raise AdoptionPlanError("target revision must be an immutable lowercase commit SHA")
    root = Path(target_root).resolve()
    observed_root = Path(_git(root, "rev-parse", "--show-toplevel").decode().strip())
    if observed_root.resolve() != root:
        raise AdoptionPlanError("target root must be the Git checkout root")
    head = _git(root, "rev-parse", "--verify", "HEAD").decode().strip()
    if not _revision(head):
        raise AdoptionPlanError("unsupported Git HEAD format")
    raw_lock = _git(root, "show", f"{head}:{LOCK_PATH}")
    lock = _json(raw_lock)
    standard = lock.get("standard") if isinstance(lock, dict) else None
    if (not isinstance(lock, dict) or lock.get("schema") != "new-project.lock/v1"
            or not isinstance(standard, dict) or standard.get("id") != STANDARD
            or standard.get("sourceRepository") != STANDARD
            or standard.get("publicationStatus") != "published"
            or not _revision(standard.get("sourceRevision"))):
        raise AdoptionPlanError("unsupported or unpublished committed adoption lock")
    current = standard["sourceRevision"]
    # Compare the file even if Git assume-unchanged/skip-worktree masks it.
    lock_path = root / LOCK_PATH
    if lock_path.is_symlink() or lock_path.parent.is_symlink():
        raise AdoptionPlanError("symlinked adoption lock is not supported")
    with lock_path.open("rb") as stream:
        working_lock = stream.read(MAX_BYTES + 1)
    dirty = bool(_git(root, "status", "--porcelain=v1", "--untracked-files=all"))
    changed = working_lock != raw_lock
    stale = _git(root, "rev-parse", "HEAD").decode().strip() != head
    supported = set(catalog["supportedRevisions"])
    result = {
        "schema": PLAN_SCHEMA, "catalogSha256": catalog_sha256,
        "standardRepository": STANDARD, "targetRoot": str(root),
        "headSha": head, "lockSha256": sha256(raw_lock).hexdigest(),
        "currentRevision": current, "requestedRevision": target_revision,
        "supportedCurrentPin": current in supported,
        "dirty": dirty, "lockChanged": changed, "headChanged": stale,
        "authority": "advisory-only", "policyProvenanceVerified": False,
        "productReadinessVerified": False, "steps": [],
    }
    if changed or stale:
        state, reason = "blocked", "observation_changed"
    elif target_revision is not None and target_revision not in supported:
        state, reason = "blocked", "unsupported_destination"
    elif current in supported and target_revision in (None, current):
        state, reason = "retain", "supported_pin"
    elif dirty:
        state, reason = "blocked", "dirty_worktree"
    else:
        route = _route(current, {target_revision} if target_revision else supported,
                       catalog["migrations"])
        if route is None:
            state, reason = "blocked", "migration_recipe_missing"
        else:
            state, reason = "migration-planned", "explicit_recipe_route"
            previous = current
            for revision in route:
                result["steps"].append({
                    "fromRevision": previous, "toRevision": revision,
                    "recipe": RECIPE,
                    "checkArgv": ["goal", "governance", "adopt",
                                  "--source-revision", revision,
                                  "--standard-repository",
                                  "https://github.com/wellmanifest/new-project.git",
                                  "--check"],
                    "requires": ["protected-catalog-provenance", "authorized-ticket",
                                 "isolated-worktree", "reobserve-head-and-lock",
                                 "adoption-preview", "stack-and-governance-tests",
                                 "independent-exact-head-review"],
                })
                previous = revision
    result.update(state=state, reason=reason)
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["planId"] = sha256(encoded).hexdigest()
    return result
