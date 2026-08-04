"""Tests for non-fast-forward push detection (rebase-retry in sweep mode)."""

import pytest

from goal.push.stages.push_remote import _is_rejected_push


@pytest.mark.parametrize(
    "stderr",
    [
        "! [rejected]        main -> main (non-fast-forward)",
        "! [rejected]        main -> main (fetch first)",
        "hint: Updates were rejected because the remote contains work",
        "error: failed to push some refs; tip of your current branch is behind",
    ],
)
def test_detects_rejected_push(stderr):
    assert _is_rejected_push(stderr) is True


@pytest.mark.parametrize(
    "stderr",
    [
        "",
        "fatal: Authentication failed for 'https://github.com/o/r.git/'",
        "error: src refspec main does not match any",
        "remote: Permission to o/r.git denied",
    ],
)
def test_ignores_non_rejection_errors(stderr):
    assert _is_rejected_push(stderr) is False
