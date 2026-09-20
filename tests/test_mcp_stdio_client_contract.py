"""Contract tests for `mcp_stdio_client` — hermetic, no torch, no index, no SDK.

WHY A FAKE SERVER RATHER THAN THE REAL ONE
------------------------------------------
The real failure (BACKLOG #205 / modelcontextprotocol/python-sdk#2678) needs a handler
that yields to the event loop AND an unlucky interleaving, so it reproduces on loaded
CI but not reliably on a fast dev box. A fake reproduces the *shape* deterministically:
respond on a delay, and hard-exit the instant stdin closes.

That also makes these tests independent of the installed SDK version, which matters
here: this repo's pinned mcp (1.28.1) and the version actually installed in a given
environment have drifted before, so a test whose verdict depends on SDK internals
would be untrustworthy exactly when you need it.

THE BASELINE TEST IS LOAD-BEARING. Without it, a fake that quietly stopped reproducing
the bug would let the contract test pass for the wrong reason. It is deliberately two
always-green assertions rather than one `xfail`, because an `xfail` would silently flip
to XPASS on that same drift instead of going red.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - fixed argv, no shell, test-local fixtures
import sys
import time

import pytest
from mcp_stdio_client import call_and_collect

# Comfortably above scheduling noise. At ~50ms this would be flaky in the other
# direction (the response could win the race), which would make the baseline test
# fail intermittently and teach nobody anything.
_FAKE_DELAY_S = 1.0
# The baseline test exits before the timer fires, so a much longer delay costs it
# nothing and makes it immune to a pathological scheduler pause.
_BASELINE_DELAY_S = 10.0

_CALL = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {}}

# A server that drops in-flight responses on stdin EOF — the #2678 shape, made
# deterministic. Reads lines; on a tools/call it arms a timer to answer later; on EOF
# it exits immediately, discarding anything not yet written.
_FAKE = """
import json, os, sys, threading

def respond():
    sys.stdout.write(json.dumps({{"jsonrpc":"2.0","id":2,
        "result":{{"content":[{{"type":"text","text":"PRINCIPLE_CONTENT_OK"}}]}}}}) + "\\n")
    sys.stdout.flush()

NOISE = {noise}
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    if msg.get("method") == "tools/call":
        if NOISE:
            # Fill the stderr pipe buffer well past the ~64KB kernel limit. A client
            # that only drains stdout deadlocks here and never sees the response.
            sys.stderr.write("x" * NOISE + "\\n")
            sys.stderr.flush()
        threading.Timer({delay}, respond).start()
# stdin hit EOF. Hard-exit, dropping any armed-but-unsent response.
os._exit(0)
"""


def _fake_server(tmp_path, noise: int = 0, delay: float = _FAKE_DELAY_S):
    p = tmp_path / "fake_mcp_server.py"
    p.write_text(_FAKE.format(delay=delay, noise=noise))
    return [sys.executable, str(p)]


def _has_response(stdout: str) -> bool:
    for line in stdout.splitlines():
        try:
            msg = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(msg, dict) and msg.get("id") == 2:
            return True
    return False


def test_communicate_baseline_drops_the_response(tmp_path):
    """THE LOAD-BEARING TEST: prove the fake actually reproduces the bug.

    This is what `subprocess.communicate()` does — write, then close stdin at once.
    If this ever goes green, the fake has stopped biting and the contract test below
    is passing for the wrong reason.
    """
    proc = subprocess.Popen(  # nosec B603
        _fake_server(tmp_path, delay=_BASELINE_DELAY_S),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = proc.communicate(json.dumps(_CALL) + "\n", timeout=30)
    assert not _has_response(out), (
        "the fake server no longer drops the response — it has stopped reproducing "
        "#2678, so the contract test below would pass vacuously. Fix the fake."
    )


def test_client_holds_stdin_open_until_the_response_lands(tmp_path):
    """The fix: same fake, same delay, correct client discipline -> response arrives."""
    out, _err, outcome, _rc = call_and_collect(
        _fake_server(tmp_path),
        cwd=str(tmp_path),
        env=None,
        messages=[_CALL],
        want_id=2,
        timeout_s=30,
    )
    assert outcome == "answered", f"expected 'answered', got {outcome!r}"
    assert _has_response(out)


def test_client_does_not_deadlock_on_large_stderr(tmp_path):
    """A client that drains only stdout deadlocks once stderr fills its pipe buffer.

    The real server is chatty on stderr (startup logging), so this is not theoretical.
    The per-stream drain threads are what prevent it; this test keeps that a covered
    regression rather than a comment.
    """
    out, err, outcome, _rc = call_and_collect(
        _fake_server(tmp_path, noise=1_000_000),
        cwd=str(tmp_path),
        env=None,
        messages=[_CALL],
        want_id=2,
        timeout_s=60,
    )
    assert outcome == "answered", f"deadlocked or lost the response: {outcome!r}"
    assert _has_response(out)
    assert len(err) > 500_000, "stderr was not actually drained"


def test_exited_outcome_when_child_dies_without_answering(tmp_path):
    """Classification matters: 'exited' (dropped) must not be reported as 'timeout'.

    Conflating the two is precisely what made this bug survive two wrong root causes.
    """
    p = tmp_path / "dies.py"
    p.write_text("import os,sys\nsys.stdin.readline()\nos._exit(3)\n")
    out, _err, outcome, rc = call_and_collect(
        [sys.executable, str(p)],
        cwd=str(tmp_path),
        env=None,
        messages=[_CALL],
        want_id=2,
        timeout_s=30,
    )
    assert outcome == "exited", f"expected 'exited', got {outcome!r}"
    assert rc == 3
    assert not _has_response(out)


@pytest.mark.parametrize("noise", [0, 200_000])
def test_answered_returns_promptly_not_at_process_exit(tmp_path, noise):
    """`communicate()` blocked until the child EXITED. This returns on the response.

    MEASURES the promptness rather than merely implying it — the earlier version only
    asserted `outcome == "answered"`, which discriminated only because the child's sleep
    exceeded the deadline. Guards the launch test's docstring claim that the happy path
    returns as soon as the response lands (false while it used communicate()).
    """
    p = tmp_path / "lingers.py"
    p.write_text(
        "import json,sys,time\n"
        "sys.stdin.readline()\n"
        'sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":2,"result":{}})+"\\n")\n'
        "sys.stdout.flush()\n"
        f"sys.stderr.write('y'*{noise})\n"
        # Long enough that waiting for exit would be obvious, short enough that the
        # shutdown grace does not dominate the suite's wall clock.
        "time.sleep(12)\n"
    )
    t0 = time.monotonic()
    _out, _err, outcome, _rc = call_and_collect(
        [sys.executable, str(p)],
        cwd=str(tmp_path),
        env=None,
        messages=[_CALL],
        want_id=2,
        timeout_s=25,
    )
    elapsed = time.monotonic() - t0
    assert outcome == "answered"
    assert elapsed < 11, (
        f"took {elapsed:.1f}s — the response landed almost immediately, so this "
        f"returned at process exit rather than on the response (the communicate() bug)"
    )
