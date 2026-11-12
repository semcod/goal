"""Bounded cleanup of the POSIX process group owned by one Linux hub check."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path


def _stop_and_collect(process: subprocess.Popen[str]) -> tuple[str, str]:
    # The child starts a new session: never signal the caller's process group.
    # Kill even if the leader already exited; descendants may still own pipes.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        return process.communicate(timeout=2)
    except subprocess.TimeoutExpired as error:
        # A descendant that deliberately starts another session is outside this
        # process group. Do not let its inherited pipes make teardown unbounded.
        process.stdout.close()
        process.stderr.close()
        process.wait(timeout=2)
        return tuple(
            part.decode(errors="replace") if isinstance(part, bytes) else part or ""
            for part in (error.output, error.stderr)
        )


@contextmanager
def _termination_guard(process):
    # CLI/controller cancellation must reach the new session too. Respect a
    # caller's custom/ignored handler and never change handlers from a worker.
    if (threading.current_thread() is not threading.main_thread()
            or signal.getsignal(signal.SIGTERM) != signal.SIG_DFL):
        yield
        return

    def terminate(signum, _frame):
        try:
            _stop_and_collect(process)
        finally:
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)

    signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_DFL)


def run_check(command: list[str], *, cwd: Path, timeout: float):
    """Run one real check; preserve failure, timeout output and interruption."""
    if os.name != "posix":
        # This contract runs Linux shell suites. Retain the existing portable
        # runner for non-POSIX callers; Windows governance uses its own CI gate.
        return subprocess.run(
            command, cwd=cwd, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )
    with _termination_guard(process):
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            stdout, stderr = _stop_and_collect(process)
            raise subprocess.TimeoutExpired(
                command, timeout, output=stdout, stderr=stderr
            ) from error
        except BaseException as error:
            try:
                _stop_and_collect(process)
            except (OSError, subprocess.TimeoutExpired) as cleanup_error:
                error.add_note(f"Owned process-group cleanup failed: {type(cleanup_error).__name__}")
            raise
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
