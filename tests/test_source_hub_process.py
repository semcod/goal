"""Actual Linux descendants must not outlive bounded source-hub checks."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from goal.governance import delivery

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="Observe Linux process identity and zombie state"
)


def _hub(tmp_path):
    root = tmp_path / "hub"
    for name in ("governance", "scripts", "tests", ".github/workflows"):
        (root / name).mkdir(parents=True)
    (root / "governance/manifest.default.json").write_text("{}\n")
    (root / "scripts/check_required_checks.py").write_text("print('required: PASS')\n")
    (root / ".github/workflows/ci.yml").write_text(
        "steps:\n  - run: bash tests/slow.test.sh\n"
    )
    marker = root / "child.json"
    child = (
        "import json,os,signal,time; from pathlib import Path; "
        "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
        f"note=Path({str(marker)!r}); staged=note.with_suffix('.tmp'); "
        "staged.write_text(json.dumps({'pid':os.getpid(),'group':os.getpgrp(),"
        "'identity':Path('/proc/self/stat').read_text().split()[21]})); "
        "staged.replace(note); "
        "print('owned child ready',flush=True); time.sleep(60)"
    )
    (root / "tests/spawn.py").write_text(
        "import subprocess,sys,time\n"
        f"subprocess.Popen([sys.executable,'-c',{child!r}])\n"
        "time.sleep(60)\n"
    )
    (root / "tests/slow.test.sh").write_text(
        'exec python3 -u tests/spawn.py\n'
    )
    return root, marker


def _running(marker):
    if not marker.exists():
        return False
    identity = json.loads(marker.read_text())
    try:
        state = Path(f"/proc/{identity['pid']}/stat").read_text().split()
    except (FileNotFoundError, ProcessLookupError):
        return False
    return state[21] == identity["identity"] and state[2] != "Z"


def _wait_for_exit(marker):
    # SIGKILL and pipe closure can precede the kernel's final exit state.
    deadline = time.monotonic() + 2
    while _running(marker) and time.monotonic() < deadline:
        time.sleep(0.01)
    return not _running(marker)


def _cleanup(marker):
    # Only this test's recorded child, with the same kernel start identity.
    if _running(marker):
        identity = json.loads(marker.read_text())
        group = os.getpgid(identity["pid"])
        if group == identity["group"] and group != os.getpgrp():
            os.killpg(group, signal.SIGKILL)
        else:
            os.kill(identity["pid"], signal.SIGKILL)


def test_real_source_hub_timeout_stops_term_ignoring_descendant(tmp_path):
    root, marker = _hub(tmp_path)
    try:
        result = delivery.run_source_hub_health(root, timeout=3, use_cache=True)
        assert marker.exists(), result.stderr
        assert result.returncode == 124
        assert result.completed_checks == 1
        assert "owned child ready" in result.stdout
        assert json.loads(marker.read_text())["group"] != os.getpgrp()
        assert _wait_for_exit(marker), "timeout left the owned child running"
        assert not (root / delivery.SOURCE_HUB_CACHE_FILE).exists()
    finally:
        _cleanup(marker)


@pytest.mark.parametrize("interrupt", [signal.SIGINT, signal.SIGTERM])
def test_real_source_hub_interrupt_stops_descendant_and_stays_failure(tmp_path, interrupt):
    root, marker = _hub(tmp_path)
    harness = subprocess.Popen(
        [sys.executable, "-c", ("from pathlib import Path; "
         "from goal.governance.delivery import run_source_hub_health; "
         f"run_source_hub_health(Path({str(root)!r}),timeout=30,use_cache=True)")],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 15
        while not marker.exists() and harness.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert marker.exists(), "source-hub child did not start"
        harness.send_signal(interrupt)
        harness.communicate(timeout=5)
        assert harness.returncode != 0
        if interrupt == signal.SIGTERM:
            assert harness.returncode == -signal.SIGTERM
        assert json.loads(marker.read_text())["group"] != harness.pid
        assert _wait_for_exit(marker), "interruption left the owned child running"
        assert not (root / delivery.SOURCE_HUB_CACHE_FILE).exists()
    finally:
        _cleanup(marker)
        if harness.poll() is None:
            os.killpg(harness.pid, signal.SIGKILL)
            harness.communicate(timeout=5)


def test_real_source_hub_failure_is_not_cached(tmp_path):
    root, _ = _hub(tmp_path)
    (root / "tests/slow.test.sh").write_text("echo intentional-failure >&2\nexit 7\n")
    result = delivery.run_source_hub_health(root, timeout=3, use_cache=True)
    assert result.returncode == 7
    assert result.completed_checks == 1
    assert "intentional-failure" in result.stderr
    assert not (root / delivery.SOURCE_HUB_CACHE_FILE).exists()


def test_real_slow_success_reuses_only_matching_head(tmp_path):
    root, _ = _hub(tmp_path)
    (root / "tests/slow.test.sh").write_text(
        "python3 -c 'import time; time.sleep(0.05); print(\"slow: PASS\")'\n"
    )
    (root / ".gitignore").write_text("/.subactor/\n")

    def git(*args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", "Fixture")
    first = delivery.run_source_hub_health(root, timeout=3, use_cache=True)
    assert first.returncode == 0 and not first.cached
    assert "slow: PASS" in first.stdout
    assert first.completed_checks == 2
    same = delivery.run_source_hub_health(root, timeout=3, use_cache=True)
    assert same.returncode == 0 and same.cached
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--allow-empty", "-qm", "Another head")
    changed = delivery.run_source_hub_health(root, timeout=3, use_cache=True)
    assert changed.returncode == 0 and not changed.cached
