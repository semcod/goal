from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from goal.bootstrap.costs_badge import _calculate_ai_costs


def test_calculate_ai_costs_uses_commit_diff_tuple_and_message_filter() -> None:
    ai_commit = SimpleNamespace(message="AI: improve bootstrap", hexsha="abc123")
    normal_commit = SimpleNamespace(message="docs: readme", hexsha="def456")
    commits = [
        (ai_commit, "diff --git a/goal.py b/goal.py\n@@ -1 +1 @@\n-print('a')\n+print('b')"),
        (normal_commit, "diff --git a/README.md b/README.md"),
    ]

    with patch("costs.git_parser.parse_commits", return_value=commits), patch(
        "costs.calculator.ai_cost", return_value={"cost": 0.42}
    ) as ai_cost_mock:
        total_cost, total_commits, all_commits_data = _calculate_ai_costs(Path("."))

    assert total_cost == 0.42
    assert total_commits == 1
    assert all_commits_data == commits
    ai_cost_mock.assert_called_once()
