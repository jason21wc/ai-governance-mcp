"""End-to-end launch + content test for generated MCP configs.

The anti-false-confidence gate (contrarian ab92073f5912): "tools appear" is NOT
"it works" — a server with a missing/empty index still lists its tools and
returns nothing. This test spawns the resolved argv from the generated config,
from a cwd OUTSIDE the repo, under the EXACT generated env block, and asserts a
`get_principle` call returns real principle content. That proves both the
launch path (no spawn ENOENT — absolute interpreter) and the data path (the
generated AI_GOVERNANCE_* env vars actually point the server at its corpus).

Marked `integration`: it starts a real server subprocess. NOTE it is NOT marked
`slow`, so it DOES run in CI's default `-m "not slow"` suite on every PR and push
(`.github/workflows/ci.yml`) — an earlier version of this docstring claimed it ran
only under `pytest -m integration`, which was wrong.

CLIENT DISCIPLINE (BACKLOG #205): this test drives the server through
`mcp_stdio_client.call_and_collect`, NOT `subprocess.communicate`. `communicate()`
closes stdin the instant it finishes writing, and the MCP SDK treats stdin EOF as
immediate transport teardown — closing the write stream out from under a handler that
is still running, so the response is generated and then discarded
(modelcontextprotocol/python-sdk#2678). No real host closes stdin with a request in
flight; `src/ai_governance_mcp/enforcement.py` holds it open for the whole session.
"""

import json
import os

import pytest
from mcp_stdio_client import call_and_collect

from ai_governance_mcp.config_generator import generate_claude_config

pytestmark = pytest.mark.integration

PRINCIPLE_ID = "meta-core-systemic-thinking"

_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "launch-test", "version": "0"},
    },
}
_INITIALIZED = {"jsonrpc": "2.0", "method": "notifications/initialized"}
_CALL = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "get_principle", "arguments": {"principle_id": PRINCIPLE_ID}},
}


# Cold-start ceiling for the spawned server (numpy import, index JSON, embeddings
# .npy, BM25 build). NOTE: the model is NOT loaded on this path — `RetrievalEngine
# .embedder` is a lazy @property and `get_principle` never touches it, so the old
# "imports torch, loads the embedding model" note here was stale. Sized for loaded CI
# runners, notably 3.11 which reruns the whole suite under coverage. The happy path
# now genuinely returns as soon as the response lands (it did not under communicate(),
# which blocked until process exit), so this bounds only the pathological path.
_LAUNCH_TIMEOUT_S = 300


def _run(server_entry, cwd):
    """Drive the server as a correct MCP client; return the (out, err) contract.

    Thin wrapper over `call_and_collect` — it owns only the self-labeling, so
    `_tool_result_text` and the assertions below are unchanged.
    """
    argv = [server_entry["command"], *server_entry["args"]]
    # Real generated env block layered over the base environment. cwd is OUTSIDE
    # the repo, so the server cannot fall back to a cwd-based corpus discovery —
    # it must use AI_GOVERNANCE_* from the generated env.
    env = {**os.environ, **server_entry["env"]}

    out, err, outcome, rc = call_and_collect(
        argv,
        cwd=str(cwd),
        env=env,
        messages=[_INIT, _INITIALIZED, _CALL],
        want_id=2,
        timeout_s=_LAUNCH_TIMEOUT_S,
    )

    if outcome == "timeout":
        # Self-labeling: empty stdout here means the server did not finish startup in
        # time, NOT a launch/handshake error — the startup WARNING that otherwise
        # dominates the STDERR tail is a red herring. KEEP THIS STRING BYTE-IDENTICAL:
        # BACKLOG #205 and the LEARNING-LOG both cite its ABSENCE as the evidence that
        # ruled out the timeout hypothesis. Changing it invalidates that trail.
        err = f"[server did not respond within {_LAUNCH_TIMEOUT_S}s — killed]\n{err}"
    elif outcome == "exited":
        # Report the OBSERVATION as fact and the CAUSE as a hypothesis. Other things
        # land in this branch — a crash during index load, an SDK "request before
        # initialization" error, a truncated drain — and stating #2678 as established
        # here would be the same move that produced two wrong root causes for this very
        # bug. What is certain is only that it closed stdout rather than timing out.
        err = (
            f"[server exited rc={rc} without answering id=2 — it did NOT time out, it "
            f"closed stdout. Leading hypothesis: BACKLOG #205 / python-sdk#2678 (the "
            f"SDK closes the write stream on stdin EOF, dropping a still-running "
            f"handler's response). Rule out a startup crash using the tail below.]\n{err}"
        )
    return out, err


def _tool_result_text(stdout):
    """Extract the id=2 result text, or None. Re-parses raw stdout deliberately.

    This duplicates a few lines of the client's matcher rather than reusing its verdict,
    so the assertion stays independent of the detector that decided we had an answer.
    Do not "simplify" it away.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:  # JSONDecodeError subclasses ValueError
            continue
        if msg.get("id") == 2 and isinstance(msg.get("result"), dict):
            parts = msg["result"].get("content", [])
            return "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return None


def _tool_error(stdout):
    """A JSON-RPC error for id=2, if any.

    Without this, an error response reads as NO response — the server answered, it just
    answered badly, and collapsing those two is the failure-mode confusion this whole
    change exists to remove.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("id") == 2 and msg.get("error") is not None:
            return msg["error"]
    return None


@pytest.mark.parametrize("enforce", [False, True])
def test_generated_config_launches_and_returns_content(tmp_path, enforce):
    server = generate_claude_config(enforce=enforce)["mcpServers"]["ai-governance"]

    # The launch path must be PATH-independent (the original bug).
    assert os.path.isabs(server["command"]), server["command"]

    docs = server["env"].get("AI_GOVERNANCE_DOCUMENTS_PATH")
    if not docs or not os.path.isdir(docs):
        pytest.skip(
            "no governance corpus resolved here (bare wheel) — data path not testable"
        )

    out, err = _run(server, tmp_path)

    # Distinguish "answered badly" from "did not answer" before asserting on content.
    rpc_error = _tool_error(out)
    assert rpc_error is None, (
        f"server RESPONDED with a JSON-RPC error (it launched and answered — this is "
        f"NOT a dropped response): {rpc_error}\nSTDERR tail:\n{err[-2000:]}"
    )

    text = _tool_result_text(out)
    assert text is not None, (
        f"no tools/call response on stdout (server failed to launch/respond).\n"
        f"STDERR tail:\n{err[-2000:]}"
    )
    # Real content, not an empty-index degradation.
    assert PRINCIPLE_ID in text or "systemic" in text.lower(), (
        f"governance returned no real content (empty index?).\nGOT: {text[:500]}"
    )
