#!/usr/bin/env python3
"""Classify LibreOffice by a bounded conversion, not PATH presence."""

from __future__ import annotations

import argparse
from contextlib import suppress
import json
import os
import signal
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30.0
TERMINATION_GRACE_SECONDS = 1.0
RUNNABLE = 0
ABSENT = 1
INSTALLED_BUT_BLOCKED = 2


def _positive_seconds(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if seconds <= 0:
        raise argparse.ArgumentTypeError("timeout must be greater than zero")
    return seconds


def _first_line(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return (value or "").splitlines()[0] if value else ""


def _emit(**diagnostic: Any) -> None:
    print(json.dumps(diagnostic, sort_keys=True))


def _terminate_timed_out(process: subprocess.Popen[str]) -> str:
    """Terminate the isolated probe tree, reap its launcher, and drain stderr."""
    if os.name == "posix":
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
    else:
        with suppress(ProcessLookupError):
            process.terminate()

    stderr = ""
    try:
        _, stderr = process.communicate(timeout=TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired as exc:
        stderr = _first_line(exc.stderr)

    if os.name == "posix":
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    elif process.poll() is None:
        process.kill()

    try:
        _, drained_stderr = process.communicate(timeout=TERMINATION_GRACE_SECONDS)
        if drained_stderr:
            stderr = drained_stderr
    except subprocess.TimeoutExpired:
        process.kill()
        _, drained_stderr = process.communicate()
        if drained_stderr:
            stderr = drained_stderr
    return _first_line(stderr)


def probe(timeout_seconds: float) -> int:
    executable = shutil.which("soffice")
    common: dict[str, Any] = {
        "executable": executable,
        "timeout_seconds": timeout_seconds,
    }
    if executable is None:
        _emit(
            state="ABSENT",
            exit_status=None,
            signal=None,
            timeout_hit=False,
            output_present=False,
            stderr_first_line="",
            **common,
        )
        return ABSENT

    with tempfile.TemporaryDirectory(prefix="content-enhancer-libreoffice-") as root:
        probe_root = Path(root)
        profile = probe_root / "profile"
        output = probe_root / "output"
        source = probe_root / "probe.csv"
        profile.mkdir()
        output.mkdir()
        source.write_text("label,value\nprobe,1\n", encoding="utf-8")
        command = [
            executable,
            f"-env:UserInstallation={profile.resolve().as_uri()}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output),
            str(source),
        ]

        try:
            process = subprocess.Popen(  # nosec B603 - capability probe target
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                start_new_session=os.name == "posix",
            )
            _, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            _emit(
                state="INSTALLED_BUT_BLOCKED",
                exit_status=None,
                signal=None,
                timeout_hit=True,
                output_present=False,
                stderr_first_line=_terminate_timed_out(process),
                **common,
            )
            return INSTALLED_BUT_BLOCKED
        except OSError as exc:
            _emit(
                state="INSTALLED_BUT_BLOCKED",
                exit_status=None,
                signal=None,
                timeout_hit=False,
                output_present=False,
                stderr_first_line=_first_line(str(exc)),
                **common,
            )
            return INSTALLED_BUT_BLOCKED

        expected_pdf = output / "probe.pdf"
        output_present = expected_pdf.is_file() and expected_pdf.stat().st_size > 0
        returncode = process.returncode
        runnable = returncode == 0 and output_present
        _emit(
            state="RUNNABLE" if runnable else "INSTALLED_BUT_BLOCKED",
            exit_status=returncode if returncode >= 0 else None,
            signal=-returncode if returncode < 0 else None,
            timeout_hit=False,
            output_present=output_present,
            stderr_first_line=_first_line(stderr),
            **common,
        )
        return RUNNABLE if runnable else INSTALLED_BUT_BLOCKED


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe LibreOffice with an isolated, bounded PDF conversion."
    )
    parser.add_argument(
        "--timeout",
        type=_positive_seconds,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"conversion timeout (default: {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    args = parser.parse_args()
    return probe(args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
