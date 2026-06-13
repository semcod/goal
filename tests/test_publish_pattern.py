"""Tests for publish pattern resolution after doctor auto-fixes."""

from pathlib import Path

from goal.cli.publish import (
    _ensure_python_artifacts_for_version,
    _resolve_python_publish_cmd,
)
from goal.config.manager import GoalConfig


def test_resolve_python_publish_cmd_uses_pyproject_name(
    tmp_path: Path, monkeypatch
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "cllm-1.2.3-py3-none-any.whl").write_text("wheel")
    (dist / "cllm-1.2.3.tar.gz").write_text("sdist")

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "cllm"\n')
    monkeypatch.chdir(tmp_path)

    publish_cmd = "twine upload dist/clilm-{version}*"
    resolved = _resolve_python_publish_cmd(publish_cmd, "1.2.3")

    assert resolved == (
        "twine upload dist/cllm-1.2.3-py3-none-any.whl dist/cllm-1.2.3.tar.gz"
    )


def test_resolve_python_publish_cmd_uses_setup_py_name(
    tmp_path: Path, monkeypatch
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "tellm-4.0.1-py3-none-any.whl").write_text("wheel")
    (dist / "tellm-4.0.1.tar.gz").write_text("sdist")
    (dist / "tellm-4.0.0.tar.gz").write_text("old sdist")

    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\nsetup(name="tellm", version="4.0.1")\n'
    )
    monkeypatch.chdir(tmp_path)

    publish_cmd = "twine upload dist/telm-{version}*"
    resolved = _resolve_python_publish_cmd(publish_cmd, "4.0.1")

    assert resolved == (
        "twine upload dist/tellm-4.0.1-py3-none-any.whl dist/tellm-4.0.1.tar.gz"
    )


def test_resolve_python_publish_cmd_filters_broad_dist_glob(
    tmp_path: Path, monkeypatch
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "tellm-4.0.1-py3-none-any.whl").write_text("wheel")
    (dist / "tellm-4.0.1.tar.gz").write_text("sdist")
    (dist / "tellm-4.0.0.tar.gz").write_text("old sdist")

    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\nsetup(name="tellm", version="4.0.1")\n'
    )
    monkeypatch.chdir(tmp_path)

    resolved = _resolve_python_publish_cmd("twine upload dist/*", "4.0.1")

    assert resolved == (
        "twine upload dist/tellm-4.0.1-py3-none-any.whl dist/tellm-4.0.1.tar.gz"
    )


def test_ensure_python_artifacts_resyncs_setup_py_and_rebuilds(
    tmp_path: Path, monkeypatch
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "tellm-4.0.0.tar.gz").write_text("old sdist")
    (tmp_path / "VERSION").write_text("4.0.0\n")
    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\nsetup(name="tellm", version="4.0.0")\n'
    )
    monkeypatch.chdir(tmp_path)

    calls = []

    def fake_build(command):
        calls.append(command)
        (dist / "tellm-4.0.1.tar.gz").write_text("new sdist")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr("goal.cli.publish.run_command_tee", fake_build)

    assert _ensure_python_artifacts_for_version("4.0.1", "python -m build", "python")
    assert calls == ["python -m build"]
    assert 'version="4.0.1"' in (tmp_path / "setup.py").read_text()


def test_goal_config_reload_reads_updated_goal_yaml(tmp_path: Path, monkeypatch) -> None:
    goal_yaml = tmp_path / "goal.yaml"
    goal_yaml.write_text(
        "project:\n  name: old\nstrategies:\n  python:\n    publish: twine upload dist/old-{version}*\n"
    )

    monkeypatch.chdir(tmp_path)
    config = GoalConfig(str(goal_yaml))
    config.load()
    assert config.get_strategy("python")["publish"] == "twine upload dist/old-{version}*"

    goal_yaml.write_text(
        "project:\n  name: new\nstrategies:\n  python:\n    publish: twine upload dist/new-{version}*\n"
    )
    config.reload()
    assert config.get_strategy("python")["publish"] == "twine upload dist/new-{version}*"
