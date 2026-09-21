"""Model-free containment for the watcher, including model bootstrap.

Darwin measures physical footprint (including compressed memory), not RSS.
Polling is a tripwire, not a hard allocation ceiling. Only the owned worker's
process group is signalled; unrelated applications are never selected.
"""

import ctypes
import fcntl
import json
import logging
import math
import os
import signal
import subprocess  # nosec B404 — owned fixed-module worker; never a shell
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)
DEFAULT_LIMIT_MIB = 8192
POLL_SECONDS = 2.0
# The installed launchd job allows five seconds for supervisor exit. Send group
# KILL well before that deadline, even if the worker ignores TERM or holds the GIL.
TERM_SECONDS = 2.0
RESTART_SECONDS = 60.0


class _RUsageInfoV0(ctypes.Structure):
    # Apple's bsd/sys/resource.h, RUSAGE_INFO_V0 (ABI version 0).
    _fields_ = [("uuid", ctypes.c_uint8 * 16)] + [
        (name, ctypes.c_uint64)
        for name in (
            "user_time",
            "system_time",
            "pkg_idle_wkups",
            "interrupt_wkups",
            "pageins",
            "wired_size",
            "resident_size",
            "phys_footprint",
            "proc_start_abstime",
            "proc_exit_abstime",
        )
    ]


class MemoryProbe:
    """Native bounded reads; never imports psutil, NumPy, or torch."""

    def __init__(self):
        if sys.platform == "darwin":
            self._proc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
            self._proc.proc_pid_rusage.argtypes = [
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_void_p,
            ]
            self._proc.proc_pid_rusage.restype = ctypes.c_int
            self._libc = ctypes.CDLL(None, use_errno=True)
            self._libc.sysctlbyname.argtypes = [
                ctypes.c_char_p,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_size_t),
                ctypes.c_void_p,
                ctypes.c_size_t,
            ]
            self._libc.sysctlbyname.restype = ctypes.c_int
        elif not sys.platform.startswith("linux"):
            raise RuntimeError("Watcher memory supervision requires Darwin or Linux")

    def footprint(self, pid: int) -> int:
        if sys.platform == "darwin":
            usage = _RUsageInfoV0()
            if self._proc.proc_pid_rusage(pid, 0, ctypes.byref(usage)) != 0:
                raise OSError(ctypes.get_errno(), "proc_pid_rusage failed")
            value = usage.phys_footprint
        else:
            fields = {}
            for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                key, _, value = line.partition(":")
                if key in ("VmRSS", "VmSwap"):
                    fields[key] = int(value.split()[0]) * 1024
            value = fields["VmRSS"] + fields["VmSwap"]
        if value <= 0:
            raise RuntimeError("Invalid process memory sample")
        return value

    def pressure(self) -> int:
        if sys.platform != "darwin":
            # Linux containment uses RSS+swap; no claim of Darwin-equivalent pressure.
            return 1
        value = ctypes.c_uint32()
        size = ctypes.c_size_t(ctypes.sizeof(value))
        if (
            self._libc.sysctlbyname(
                b"kern.memorystatus_vm_pressure_level",
                ctypes.byref(value),
                ctypes.byref(size),
                None,
                0,
            )
            != 0
        ):
            raise OSError(ctypes.get_errno(), "memory pressure sample failed")
        if value.value not in (1, 2, 4):
            raise RuntimeError(f"Unknown memory pressure level: {value.value}")
        return value.value


def memory_limit_bytes() -> int:
    raw = os.environ.get(
        "AI_CONTEXT_ENGINE_WATCHER_MAX_MEMORY_MIB", str(DEFAULT_LIMIT_MIB)
    )
    value = float(raw)
    if not math.isfinite(value) or value < 256:
        raise ValueError("WATCHER_MAX_MEMORY_MIB must be finite and at least 256")
    return int(value * 1024 * 1024)


def terminate_worker(child, grace: float = TERM_SECONDS) -> None:
    """Bound cleanup even if the worker's graceful shutdown is stuck.

    The child owns a new session/group. Signal the group even if its leader has
    already exited, since model helpers may still be alive.
    """
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait(timeout=5)


def clear_worker_markers(base_path: Path, pid: int) -> None:
    """A forced kill must not leave a fresh-looking heartbeat for a dead worker."""
    for name in ("watcher.pid", "watcher-heartbeat.json"):
        path = base_path.parent / name
        try:
            raw = path.read_text()
            owner = int(raw) if name.endswith(".pid") else json.loads(raw)["pid"]
            if owner == pid:
                path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass
        except (OSError, ValueError, KeyError, TypeError):
            logger.warning("Could not validate/clear worker marker %s", path)


def monitor_worker(
    child, probe, limit: int, stop, publish, interval=POLL_SECONDS
) -> str:
    """Return the containment reason; metric failures propagate to outer cleanup."""
    while child.poll() is None and not stop.is_set():
        footprint = probe.footprint(child.pid)
        pressure = probe.pressure()
        reason = "running"
        if footprint >= limit:
            reason = "memory_limit"
        elif pressure == 4:
            reason = "critical_pressure"
        publish(reason, child.pid, footprint, pressure)
        if reason != "running":
            return reason
        stop.wait(interval)
    return "stopping" if stop.is_set() else "worker_exit"


def watch_parent(fd: int) -> None:
    """Exit if the supervisor dies, including an uncatchable parent SIGKILL."""

    def wait_for_eof():
        try:
            while os.read(fd, 1):
                pass
        finally:
            try:
                # Only a worker started in its own session may signal this group.
                if os.getpgrp() == os.getpid():
                    os.killpg(os.getpid(), signal.SIGKILL)
            finally:
                os._exit(70)

    threading.Thread(
        target=wait_for_eof, name="supervisor-liveness", daemon=True
    ).start()


def supervise(base_path: Path, worker_args: list[str]) -> None:
    """Hold singleton ownership while cycling one bounded worker at a time."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    limit = memory_limit_bytes()
    probe = MemoryProbe()
    base_path.parent.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    previous = {}
    for sig in (signal.SIGTERM, signal.SIGINT):
        previous[sig] = signal.signal(sig, lambda *_: stop.set())

    status_path = base_path.parent / "watcher-supervisor.json"

    def publish(reason, pid=None, footprint=None, pressure=None):
        data = dict(
            supervisor_pid=os.getpid(),
            child_pid=pid,
            state=reason,
            footprint_bytes=footprint,
            pressure=pressure,
            limit_bytes=limit,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
        temporary = status_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data) + "\n")
        temporary.replace(status_path)

    try:
        with (base_path.parent / "watcher-supervisor.lock").open("a") as ownership:
            try:
                fcntl.flock(ownership, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError(
                    "A watcher supervisor already owns this index namespace"
                ) from None
            while not stop.is_set():
                child = None
                read_fd = write_fd = None
                try:
                    pressure = probe.pressure()
                    if pressure != 1:
                        publish("waiting_for_normal_pressure", pressure=pressure)
                        stop.wait(RESTART_SECONDS)
                        continue
                    read_fd, write_fd = os.pipe()
                    command = [
                        sys.executable,
                        "-m",
                        "ai_governance_mcp.context_engine.watcher_daemon",
                        "--supervised-worker-fd",
                        str(read_fd),
                        *worker_args,
                    ]
                    child = subprocess.Popen(  # nosec B603 — fixed module + CLI argv, no shell
                        command,
                        start_new_session=True,
                        pass_fds=(read_fd,),
                    )
                    os.close(read_fd)
                    read_fd = None
                    logger.info(
                        "Supervising watcher PID %d; limit=%d MiB",
                        child.pid,
                        limit // 1048576,
                    )
                    reason = monitor_worker(child, probe, limit, stop, publish)
                    logger.warning("Watcher PID %d containment: %s", child.pid, reason)
                except Exception:
                    logger.exception(
                        "Watcher supervision failed; stopping owned worker"
                    )
                    reason = "supervision_error"
                finally:
                    if child is not None:
                        terminate_worker(child)
                        clear_worker_markers(base_path, child.pid)
                    for fd in (read_fd, write_fd):
                        if fd is not None:
                            os.close(fd)
                publish(reason)
                # Always back off, including failed bootstrap/metrics. launchd does not
                # get a fresh unmonitored model process while pressure remains high.
                stop.wait(RESTART_SECONDS)
            publish("stopped")
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
