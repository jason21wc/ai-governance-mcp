"""A minimally-correct MCP stdio client for tests that spawn the real server.

WHY THIS EXISTS
---------------
`subprocess.communicate(payload)` is NOT a valid MCP client. It writes the request
and CLOSES STDIN in the same breath, which asks the server to answer a peer that has
already hung up. No real host does that -- `src/ai_governance_mcp/enforcement.py`
(a real stdio client in this repo) holds the wrapped server's stdin open for the whole
session and closes it only in its `finally`.

That distinction is not academic. In the MCP Python SDK, `BaseSession._receive_loop`
holds BOTH streams in one `async with` (`mcp/shared/session.py`):

    async with (self._read_stream, self._write_stream):
        async for message in self._read_stream:

so stdin EOF drains the read stream, the `async with` exits, and **the write stream is
closed** -- while a handler dispatched via `tg.start_soon` in `Server.run()`'s SEPARATE
task group is still running. That handler completes normally and then finds nowhere to
send. Upstream: modelcontextprotocol/python-sdk#2678 (open); fix PR #2680 open/unmerged.

MEASURED (this repo, real server): a handler with >=1 event-loop suspension point loses
its response reproducibly; a handler with none does not. It is yields, not wall time.

So the fix is to speak the protocol properly: write, keep stdin OPEN, read until the
response arrives, and only then hang up.

NAMING HAZARD: `pyproject.toml` sets `pythonpath = ["tests"]`, so this module is
importable as `mcp_stdio_client`. Never name a test-support module `mcp.py` here -- it
would shadow the SDK package on sys.path.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - fixed argv, no shell, test-controlled input
import threading

# Grace given to a child to exit on its own after we close stdin, before we kill it.
_SHUTDOWN_GRACE_S = 10
# Bound on joining the drain threads after the child is gone.
_JOIN_GRACE_S = 5


def _drain(stream, sink: list[str], on_line=None) -> None:
    """Read a pipe to EOF, appending each line to `sink`.

    Runs on a daemon thread. Threads (rather than a bare readline loop in the caller)
    are load-bearing for TWO reasons:

    1. `readline()` blocks with NO timeout, so a caller looping on it can only check a
       deadline BETWEEN lines. During a cold start stdout emits nothing for a long
       while, so an in-line deadline would never fire -- turning a bounded failure into
       an unbounded hang. With a thread the caller waits on an Event instead.
    2. stdout and stderr are both pipes and this server is chatty on stderr. Draining
       only stdout deadlocks the moment stderr fills its ~64KB pipe buffer.

    `selectors` was considered and rejected: it does not work on Windows pipe handles,
    and this codebase still guards for win32 (`server/_app.py`).
    """
    try:
        for line in iter(stream.readline, ""):
            sink.append(line)
            if on_line is not None:
                on_line(line)
    except (ValueError, OSError) as exc:
        # Do NOT swallow this. A failed read truncates the sink, the joiner sets
        # `done`, and the outcome then reads as "exited" -- indistinguishable from the
        # #2678 drop, so the caller would print a confident and possibly wrong
        # diagnosis. Leave a marker in the tail so it tells the truth instead.
        sink.append(f"\n[drain aborted: {exc!r}]\n")


def call_and_collect(
    argv: list[str],
    *,
    cwd: str,
    env: dict | None,
    messages: list[dict],
    want_id: int,
    timeout_s: float,
) -> tuple[str, str, str, int | None]:
    """Speak newline-delimited JSON-RPC to a subprocess the way a real host does.

    Writes every message WITHOUT closing stdin, then reads stdout until a message with
    `id == want_id` is seen, the child closes stdout, or `timeout_s` expires. Only then
    is stdin closed and the child reaped.

    Returns `(stdout_text, stderr_text, outcome, returncode)` where outcome is:
      "answered" -- the wanted id arrived (happy path; returns as soon as it lands)
      "exited"   -- child closed stdout without answering  <- the #2678 signature
      "timeout"  -- deadline expired without stdout EOF and without the wanted id

    CONSTRAINT: the stdin write happens before the deadline starts and is NOT covered
    by `timeout_s`. Total payload must fit the OS pipe buffer (~64KB), or a child that
    never reads could block it forever. Today's callers send well under 1KB.
    """
    out_lines: list[str] = []
    err_lines: list[str] = []
    done = threading.Event()
    matched = threading.Event()

    def _watch(line: str) -> None:
        # ORDER IS LOAD-BEARING: the line is already appended to out_lines by _drain
        # before this runs, so a caller woken by `done` always sees it.
        try:
            msg = json.loads(line)
        except ValueError:  # JSONDecodeError subclasses ValueError
            return
        if isinstance(msg, dict) and msg.get("id") == want_id:
            matched.set()
            done.set()

    proc = subprocess.Popen(  # nosec B603 - fixed argv from generated config, no shell
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    t_out = threading.Thread(
        target=_drain, args=(proc.stdout, out_lines, _watch), daemon=True
    )
    t_err = threading.Thread(target=_drain, args=(proc.stderr, err_lines), daemon=True)
    t_out.start()
    t_err.start()
    # stdout hitting EOF without a match is a real outcome ("exited"), so wake the
    # caller then too rather than making it wait out the full deadline.
    threading.Thread(target=lambda: (t_out.join(), done.set()), daemon=True).start()

    try:
        payload = "".join(json.dumps(m) + "\n" for m in messages)
        try:
            proc.stdin.write(payload)
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            # Child died before it read us. Not an error here -- let the outcome
            # classification below report it with the stderr tail attached.
            pass

        # Classify off the events themselves rather than elapsed time. The clock
        # version was correct but only via an argument nobody would reconstruct (it
        # depended on `started` being taken before the write), so one innocent edit
        # would have turned every timeout into "exited".
        signalled = done.wait(timeout_s)
        if matched.is_set():
            outcome = "answered"
        elif signalled:
            outcome = "exited"  # stdout hit EOF without the wanted id
        else:
            outcome = "timeout"
    finally:
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        try:
            proc.wait(timeout=_SHUTDOWN_GRACE_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        # Killing the child closes its fds, which is what unblocks a thread parked in
        # readline(). Without that the join below would return on timeout and leak the
        # thread. Join so the returned text is complete.
        t_out.join(timeout=_JOIN_GRACE_S)
        t_err.join(timeout=_JOIN_GRACE_S)

    return "".join(out_lines), "".join(err_lines), outcome, proc.returncode
