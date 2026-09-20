"""Hermetic tests for the content-enhancer LibreOffice capability probe."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "global-skills"
    / "content-enhancer"
    / "probe_libreoffice.py"
)

FAKE_SOFFICE = """#!/bin/sh
: > "$FAKE_CAPTURE"
for arg in "$@"; do
    printf '%s\\n' "$arg" >> "$FAKE_CAPTURE"
done

case "$FAKE_MODE" in
    success)
        want_out=0
        outdir=""
        for arg in "$@"; do
            if [ "$want_out" = 1 ]; then
                outdir="$arg"
                want_out=0
            elif [ "$arg" = "--outdir" ]; then
                want_out=1
            fi
        done
        printf '%%PDF-1.4\\nprobe\\n' > "$outdir/probe.pdf"
        printf 'benign warning\\n' >&2
        exit 0
        ;;
    abort)
        printf 'abort trap\\n' >&2
        exit 134
        ;;
    missing_output)
        exit 0
        ;;
    timeout)
        trap '' TERM
        /bin/sleep 10 &
        printf '%s\\n' "$!" > "$FAKE_CHILD_PID"
        wait
        ;;
esac
exit 99
"""


def _fake_soffice(tmp_path: Path) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "soffice"
    executable.write_text(FAKE_SOFFICE, encoding="utf-8")
    executable.chmod(0o755)
    return bin_dir, tmp_path / "argv.txt"


def _run(
    tmp_path: Path, mode: str | None, timeout: float | None = None
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], Path | None]:
    env = os.environ.copy()
    capture: Path | None = None
    if mode is None:
        env["PATH"] = ""
    else:
        bin_dir, capture = _fake_soffice(tmp_path)
        env.update(
            PATH=str(bin_dir),
            FAKE_MODE=mode,
            FAKE_CAPTURE=str(capture),
            FAKE_CHILD_PID=str(tmp_path / "child.pid"),
        )
    command = [sys.executable, str(SCRIPT)]
    if timeout is not None:
        command += ["--timeout", str(timeout)]
    completed = subprocess.run(  # nosec B603 - fixed test target
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=5,
    )
    return completed, json.loads(completed.stdout), capture


def test_absent_when_soffice_is_not_on_path(tmp_path: Path):
    completed, diagnostic, _ = _run(tmp_path, None)

    assert completed.returncode == 1
    assert diagnostic == {
        "executable": None,
        "exit_status": None,
        "output_present": False,
        "signal": None,
        "state": "ABSENT",
        "stderr_first_line": "",
        "timeout_hit": False,
        "timeout_seconds": 30.0,
    }


def test_runnable_requires_nonempty_pdf_and_ignores_benign_stderr(tmp_path: Path):
    completed, diagnostic, _ = _run(tmp_path, "success")

    assert completed.returncode == 0
    assert diagnostic["state"] == "RUNNABLE"
    assert diagnostic["exit_status"] == 0
    assert diagnostic["output_present"] is True
    assert diagnostic["stderr_first_line"] == "benign warning"


def test_nonzero_exit_is_installed_but_blocked(tmp_path: Path):
    completed, diagnostic, _ = _run(tmp_path, "abort")

    assert completed.returncode == 2
    assert diagnostic["state"] == "INSTALLED_BUT_BLOCKED"
    assert diagnostic["exit_status"] == 134
    assert diagnostic["output_present"] is False
    assert diagnostic["stderr_first_line"] == "abort trap"


def test_zero_exit_without_output_is_installed_but_blocked(tmp_path: Path):
    completed, diagnostic, _ = _run(tmp_path, "missing_output")

    assert completed.returncode == 2
    assert diagnostic["state"] == "INSTALLED_BUT_BLOCKED"
    assert diagnostic["exit_status"] == 0
    assert diagnostic["output_present"] is False


def test_timeout_is_bounded_and_reported(tmp_path: Path):
    started = time.monotonic()
    completed, diagnostic, _ = _run(tmp_path, "timeout", timeout=1)

    assert time.monotonic() - started < 4
    assert completed.returncode == 2
    assert diagnostic["state"] == "INSTALLED_BUT_BLOCKED"
    assert diagnostic["timeout_hit"] is True
    assert diagnostic["timeout_seconds"] == 1.0
    assert diagnostic["output_present"] is False


def test_timeout_kills_a_non_exec_wrapper_child(tmp_path: Path):
    completed, _, _ = _run(tmp_path, "timeout", timeout=1)
    child_pid = int((tmp_path / "child.pid").read_text(encoding="utf-8"))

    if os.name == "posix":
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)
        else:
            raise AssertionError(f"timed-out child process {child_pid} survived")

    assert completed.returncode == 2


def test_conversion_uses_a_disposable_profile_and_expected_arguments(tmp_path: Path):
    completed, _, capture = _run(tmp_path, "success")
    assert completed.returncode == 0 and capture is not None
    arguments = capture.read_text(encoding="utf-8").splitlines()
    profile_argument = next(
        arg for arg in arguments if arg.startswith("-env:UserInstallation=file://")
    )

    assert "content-enhancer-libreoffice-" in profile_argument
    assert "--headless" in arguments
    assert arguments[arguments.index("--convert-to") + 1] == "pdf"
    assert arguments[arguments.index("--outdir") + 1]
