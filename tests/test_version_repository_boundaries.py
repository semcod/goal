"""Automatic version scans must not own files in another checkout."""

import subprocess
from pathlib import Path

import pytest

from goal.cli.version_state import discover_version_specs
from goal.cli.version_sync import sync_all_versions


def git(root, *args):
    subprocess.run(
        ["git", "-C", str(root), *args], check=True,
        capture_output=True, text=True,
    )


def declarations(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "pkg").mkdir(exist_ok=True)
    (root / "VERSION").write_text("1.2.3\n")
    (root / "package.json").write_text('{"version": "1.2.3"}\n')
    (root / "pkg/__init__.py").write_text('__version__ = "1.2.3"\n')
    return {
        path: path.read_bytes()
        for path in (root / "VERSION", root / "package.json", root / "pkg/__init__.py")
    }


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    (root / "VERSION").write_text("1.2.3\n")
    git(root, "init", "-q")
    git(root, "add", "VERSION")
    git(root, "-c", "user.name=Version test", "-c", "user.email=test@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", "base")
    declarations(root / "packages/owned")
    monkeypatch.chdir(root)
    return root


def sync():
    function = sync_all_versions
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__
    return function("1.2.4")


@pytest.mark.parametrize("kind", ["clone", "worktree", "gitfile", "dangling-marker", "worktree-cache"])
@pytest.mark.parametrize("operation", ["discover", "sync"])
def test_nested_checkout_boundary(project, kind, operation):
    relative = ".worktrees/recovery" if kind == "worktree-cache" else "packages/foreign"
    foreign = project / relative
    if kind == "clone":
        git(project, "clone", "-q", "--no-hardlinks", str(project), str(foreign))
    elif kind == "worktree":
        git(project, "worktree", "add", "--detach", str(foreign), "HEAD")
    else:
        foreign.mkdir(parents=True)
        if kind == "gitfile":
            (foreign / ".git").write_text("gitdir: /unavailable/submodule/metadata\n")
        elif kind == "dangling-marker":
            (foreign / ".git").symlink_to(project / "missing-metadata")
    before = declarations(foreign)

    if operation == "discover":
        specs = discover_version_specs()
        assert "VERSION" in specs
        assert "packages/owned/VERSION" in specs
        assert not any(spec.startswith(relative + "/") for spec in specs)
    else:
        updated = sync()
        assert (project / "VERSION").read_text() == "1.2.4\n"
        assert (project / "packages/owned/VERSION").read_text() == "1.2.4\n"
        assert '"1.2.4"' in (project / "packages/owned/pkg/__init__.py").read_text()
        assert not any(Path(path).as_posix().startswith(relative + "/") for path in updated)
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("operation", ["discover", "sync"])
def test_symlinked_declarations_do_not_read_or_write_external_files(project, operation):
    outside = project.parent / "outside"
    before = declarations(outside)
    shared = project / "packages/shared"
    shared.mkdir()
    (shared / "VERSION").symlink_to(outside / "VERSION")
    (shared / "__init__.py").symlink_to(outside / "pkg/__init__.py")
    (project / "linked").symlink_to(outside, target_is_directory=True)
    links = {
        path: path.readlink()
        for path in (shared / "VERSION", shared / "__init__.py", project / "linked")
    }

    if operation == "discover":
        specs = discover_version_specs()
        assert not any(spec.startswith(("linked/", "packages/shared/")) for spec in specs)
        assert "packages/owned/VERSION" in specs
    else:
        updated = sync()
        assert not any(Path(path).as_posix().startswith(("linked/", "packages/shared/")) for path in updated)
        assert (project / "packages/owned/VERSION").read_text() == "1.2.4\n"
    assert {path: path.read_bytes() for path in before} == before
    assert {path: path.readlink() for path in links} == links


@pytest.mark.parametrize("boundary", ["examples", "samples", "fixtures", "templates", "vendor", "testdata", "packages/foreign"])
def test_project_type_discovery_preserves_owned_packages_only(tmp_path, monkeypatch, boundary):
    from goal.cli.version_utils import detect_project_types

    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "owned"\n')
    owned = root / "packages/owned"
    owned.mkdir(parents=True)
    (owned / "package.json").write_text('{"name": "owned-adapter"}')
    foreign = root / boundary
    foreign.mkdir(parents=True)
    (foreign / "Cargo.toml").write_text('[package]\nname = "illustration"\n')
    if boundary == "packages/foreign":
        (foreign / ".git").write_text("gitdir: /unavailable/recovery\n")
    monkeypatch.chdir(root)
    assert detect_project_types() == ["python", "nodejs"]


def test_project_type_discovery_prunes_depth_and_links(tmp_path, monkeypatch):
    from goal.cli.version_utils import detect_project_types

    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text('[project]\nname = "owned"\n')
    at_limit = root / "packages/owned/adapter"
    at_limit.mkdir(parents=True)
    (at_limit / "package.json").write_text('{"name": "owned-adapter"}')
    too_deep = at_limit / "nested"
    too_deep.mkdir()
    (too_deep / "Cargo.toml").write_text('[package]\nname = "too-deep"\n')
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "go.mod").write_text('module foreign\n')
    (root / "linked").symlink_to(outside, target_is_directory=True)
    (root / "Gemfile").symlink_to(outside / "Gemfile")
    (outside / "Gemfile").write_text('source "https://rubygems.org"\n')
    monkeypatch.chdir(root)
    assert detect_project_types() == ["python", "nodejs"]
