import tomllib

from goal.bootstrap.pyproject_costs_setup import _try_add_deps


def test_dev_tool_injection_preserves_broad_python_support():
    source = """\
[project]
name = "fixture"
version = "0.1.0"
requires-python = ">=3.8"

[project.optional-dependencies]
dev = [
    "pytest>=7",
]
"""

    updated, changed = _try_add_deps(source)

    assert changed is True
    dev = tomllib.loads(updated)["project"]["optional-dependencies"]["dev"]
    assert "goal>=2.1.0; python_version >= '3.12'" in dev
    assert "costs>=0.1.53; python_version >= '3.9'" in dev
    assert "pfix>=0.1.60; python_version >= '3.10'" in dev

    unchanged, changed_again = _try_add_deps(updated)
    assert changed_again is False
    assert unchanged == updated


def test_legacy_goal_injected_specs_gain_python_markers():
    source = """\
[project]
name = "fixture"
version = "0.1.0"
requires-python = ">=3.8"

[project.optional-dependencies]
dev = [
    "goal>=2.1.0",
    "costs>=0.1.53",
    "pfix>=0.1.60",
]
"""

    updated, changed = _try_add_deps(source)

    assert changed is True
    dev = tomllib.loads(updated)["project"]["optional-dependencies"]["dev"]
    assert "goal>=2.1.0; python_version >= '3.12'" in dev
    assert "costs>=0.1.53; python_version >= '3.9'" in dev
    assert "pfix>=0.1.60; python_version >= '3.10'" in dev

    unchanged, changed_again = _try_add_deps(updated)
    assert changed_again is False
    assert unchanged == updated


def test_marker_migration_does_not_rewrite_runtime_dependencies():
    source = """\
[project]
name = "goal"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "costs>=0.1.53",
]

[project.optional-dependencies]
dev = [
    "pfix>=0.1.60",
]
"""

    updated, changed = _try_add_deps(source)

    assert changed is True
    project = tomllib.loads(updated)["project"]
    assert project["dependencies"] == ["costs>=0.1.53"]
    assert project["optional-dependencies"]["dev"] == [
        "pfix>=0.1.60; python_version >= '3.10'"
    ]

    unchanged, changed_again = _try_add_deps(updated)
    assert changed_again is False
    assert unchanged == updated
