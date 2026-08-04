from pathlib import Path
from unittest import mock
import importlib.util


_TODO_STAGE_PATH = (
    Path(__file__).resolve().parents[1] / "goal" / "push" / "stages" / "todo.py"
)
_SPEC = importlib.util.spec_from_file_location("goal_push_todo_stage", _TODO_STAGE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
handle_todo_stage = _MODULE.handle_todo_stage


def test_todo_stage_returns_false_when_prefact_missing() -> None:
    ctx = {"todo": True}

    with mock.patch.object(_MODULE.subprocess, "run", side_effect=FileNotFoundError):
        assert handle_todo_stage(ctx, yes=True, dry_run=False) is False


def test_todo_stage_returns_false_on_prefact_nonzero_exit() -> None:
    ctx = {"todo": True}
    proc = mock.MagicMock(returncode=1, stderr="boom", stdout="")

    with mock.patch.object(_MODULE.subprocess, "run", return_value=proc):
        assert handle_todo_stage(ctx, yes=True, dry_run=False) is False


def test_todo_stage_stages_existing_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "TODO.md").write_text("# TODO\n", encoding="utf-8")
    (tmp_path / ".planfile" / "sprints").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".planfile" / "sprints" / "current.yaml").write_text(
        "tickets: []\n", encoding="utf-8"
    )
    proc = mock.MagicMock(returncode=0, stderr="", stdout="")
    staged_calls = []

    def _fake_run_git(*args):
        staged_calls.append(args)

    with (
        mock.patch.object(_MODULE.subprocess, "run", return_value=proc),
        mock.patch.object(_MODULE, "run_git", side_effect=_fake_run_git),
    ):
        assert handle_todo_stage({"todo": True}, yes=True, dry_run=False) is True

    assert ("add", "TODO.md") in staged_calls
    assert ("add", ".planfile/sprints/current.yaml") in staged_calls
