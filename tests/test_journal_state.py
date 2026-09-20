"""P5: session-local freshness is not analysis completion or tool-call intent."""

import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / ".claude/hooks/lib/journal-state.py"
spec = importlib.util.spec_from_file_location("journal_state", HELPER)
js = importlib.util.module_from_spec(spec)
spec.loader.exec_module(js)


@pytest.fixture
def session(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "SESSION-STATE.md").write_text("baseline\n")
    tx = tmp_path / "session.jsonl"
    tx.write_text(' {"type":"user"}\n' * 10)
    return root, tx, tmp_path / "state"


def check(session, **kw):
    root, tx, state = session
    return js.check(root, tx, state, min_lines=10, recency=4, **kw)


def grow(session, n=4):
    with session[1].open("a") as f:
        f.write('{"type":"user","message":{"content":"new activity"}}\n' * n)


def complete(session, request, outcome="no_change"):
    return js.complete(*session, request["request_id"], outcome)


def test_same_input_and_small_growth_emit_only_once(session):
    first = check(session)
    assert first["action"] == "fire"
    assert check(session)["action"] == "silent"
    grow(session, 3)
    assert check(session)["action"] == "silent"


@pytest.mark.parametrize("outcome", ["no_change", "proposals", "applied"])
def test_completion_is_explicit_self_attestation_not_a_write(session, outcome):
    request = check(session)
    before = (session[0] / "SESSION-STATE.md").read_bytes()
    assert complete(session, request, outcome)["accepted"]
    assert check(session)["action"] == "silent"
    assert (session[0] / "SESSION-STATE.md").read_bytes() == before
    events = [
        json.loads(x)
        for x in next(session[2].glob("*.events.jsonl")).read_text().splitlines()
    ]
    assert [x["event"] for x in events] == ["requested", "completed"]
    assert events[-1]["evidence"] == "main_agent_self_attestation"
    assert events[-1]["outcome"] == outcome
    assert events[-1]["covered_lines"] == 10
    grow(session)
    assert check(session)["action"] == "fire"


def test_pending_recovery_and_stale_duplicate_receipts(session):
    first = check(session)
    grow(session)
    replacement = check(session)
    assert replacement["action"] == "fire"
    assert replacement["request_id"] != first["request_id"]
    assert not complete(session, first)["accepted"]
    assert not js.complete(*session, "invented", "no_change")["accepted"]
    assert complete(session, replacement)["accepted"]
    assert not complete(session, replacement)["accepted"]


def test_late_completion_does_not_cover_activity_while_analyst_ran(session):
    request = check(session)
    grow(session, 8)
    assert complete(session, request)["accepted"]
    assert check(session)["action"] == "fire"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_tool_vocabulary_does_not_earn_freshness(session, host):
    check(session)
    if host == "claude":
        entry = {
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Edit",
                        "id": "x",
                        "input": {"file_path": str(session[0] / "SESSION-STATE.md")},
                    }
                ]
            }
        }
    else:
        entry = {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "apply_patch",
                "call_id": "x",
                "input": "*** Update File: SESSION-STATE.md",
            },
        }
    with session[1].open("a") as f:
        f.write(json.dumps(entry) + "\n")
        f.write('{"tool_result":"failed", "is_error":true}\n')
        f.write("read SESSION-STATE.md; cat PROJECT-MEMORY.md\n")
        f.write("successful no-op write\n")
    # Even a successful no-op leaves no new byte-level maintenance evidence.
    memory = session[0] / "SESSION-STATE.md"
    memory.write_bytes(memory.read_bytes())
    assert check(session)["action"] == "fire"


@pytest.mark.parametrize("path", ["SESSION-STATE.md", "_ai-context/BACKLOG.md"])
def test_real_content_change_resets_freshness(session, path):
    check(session)
    grow(session)
    memory = session[0] / path
    memory.parent.mkdir(exist_ok=True)
    memory.write_text("new persisted content\n")
    assert check(session)["reason"] == "memory_changed"
    assert check(session)["action"] == "silent"
    grow(session)
    assert check(session)["action"] == "fire"


def test_head_move_plus_memory_change_is_not_freshness(session):
    root = session[0]

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True
        )

    git("init", "-q")
    git("add", ".")
    git(
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "base",
    )
    check(session)
    grow(session)
    (root / "SESSION-STATE.md").write_text("brought in by merge\n")
    git("add", ".")
    git(
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "merge-like HEAD move",
    )
    assert check(session)["action"] == "fire"


def test_head_moves_during_hashing_does_not_credit_the_next_sample(
    session, monkeypatch
):
    monkeypatch.setattr(js, "head_at", lambda _: "old-head")
    check(session)
    # Hook observes a HEAD transition but sampled pre-merge bytes.
    values = iter(["old-head", "new-head"])
    monkeypatch.setattr(js, "head_at", lambda _: next(values))
    assert check(session)["action"] == "silent"
    (session[0] / "SESSION-STATE.md").write_text("merged content\n")
    monkeypatch.setattr(js, "head_at", lambda _: "new-head")
    grow(session)
    assert check(session)["action"] == "fire"


def test_unavailable_hash_keeps_provenance_across_head_move(session, monkeypatch):
    monkeypatch.setattr(js, "head_at", lambda _: "old-head")
    check(session)
    path = session[0] / "SESSION-STATE.md"
    path.unlink()
    monkeypatch.setattr(js, "head_at", lambda _: "new-head")
    assert check(session)["action"] == "silent"
    assert check(session)["action"] == "silent"
    path.write_text("integrated content\n")
    grow(session)
    assert check(session)["action"] == "fire"
    # A later genuine edit at stable HEAD can earn credit again.
    grow(session)
    path.write_text("local maintenance after baseline\n")
    assert check(session)["reason"] == "memory_changed"


@pytest.mark.parametrize(
    "corruption", ["empty_memory", "expanded_receipt", "bad_digest"]
)
def test_schema_inconsistent_state_cannot_credit_freshness_or_coverage(
    session, corruption
):
    request = check(session)
    grow(session, 3)
    check(session)
    path = next(session[2].glob("*.state.json"))
    state = json.loads(path.read_text())
    if corruption == "empty_memory":
        state["memory"] = {}
    elif corruption == "bad_digest":
        state["memory"]["SESSION-STATE.md"] = "invalid digest"
    else:
        state["pending"]["covered_lines"] = 13
    path.write_text(json.dumps(state))
    assert not complete(session, request)["accepted"]
    assert check(session)["action"] == "fire"


@pytest.mark.parametrize("operation", ["delete", "symlink", "directory"])
def test_missing_or_unsafe_file_is_not_maintenance(session, operation):
    check(session)
    grow(session)
    memory = session[0] / "SESSION-STATE.md"
    memory.unlink()
    if operation == "symlink":
        memory.symlink_to(session[1])
    elif operation == "directory":
        memory.mkdir()
    assert check(session)["action"] == "fire"


def test_temporarily_unavailable_then_same_bytes_is_not_freshness(session):
    check(session)
    path = session[0] / "SESSION-STATE.md"
    before = path.read_bytes()
    path.unlink()
    assert check(session)["action"] == "silent"
    grow(session)
    path.write_bytes(before)
    assert check(session)["action"] == "fire"


def test_receipt_after_new_freshness_does_not_move_checkpoint_backwards(session):
    request = check(session)
    grow(session, 3)
    (session[0] / "SESSION-STATE.md").write_text("maintained\n")
    assert check(session)["reason"] == "memory_changed"
    assert complete(session, request)["accepted"]
    grow(session, 1)
    assert check(session)["action"] == "silent"


def test_concurrent_checks_emit_one_request(session):
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: check(session), range(6)))
    assert sum(r["action"] == "fire" for r in results) == 1


def test_sessions_and_worktrees_are_independent(session, tmp_path):
    first = check(session)
    other_tx = tmp_path / "other.jsonl"
    other_tx.write_bytes(session[1].read_bytes())
    other = (session[0], other_tx, session[2])
    assert not complete(other, first)["accepted"]
    assert check(other)["action"] == "fire"
    other_root = tmp_path / "other-root"
    other_root.mkdir()
    another = (other_root, session[1], session[2])
    assert check(another)["action"] == "fire"
    assert not complete(another, first)["accepted"]


@pytest.mark.parametrize("change", ["truncate", "replace", "rewrite_regrow"])
def test_transcript_reset_invalidates_old_receipt_and_recovers(session, change):
    first = check(session)
    tx = session[1]
    if change == "replace":
        tx.unlink()
    tx.write_text("new transcript\n" * (20 if change == "rewrite_regrow" else 10))
    assert not complete(session, first)["accepted"]
    assert check(session)["action"] == "fire"


def test_corrupt_state_is_repaired_not_silent(session):
    check(session)
    next(session[2].glob("*.state.json")).write_text('{"version": 1}')
    assert check(session)["action"] == "fire"
    assert check(session)["action"] == "silent"


def test_unusable_storage_is_explicit_nonblocking_degradation(session):
    session[2].write_text("not a directory")
    result = check(session)
    assert result["action"] == "degraded"
    p = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "check",
            "--root",
            str(session[0]),
            "--transcript",
            str(session[1]),
            "--state-dir",
            str(session[2]),
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert p.returncode == 0
    assert json.loads(p.stdout)["action"] == "degraded"


def test_busy_lock_has_bounded_wait(session):
    import fcntl

    check(session)
    lock = next(session[2].glob("*.lock"))
    with lock.open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        result = check(session)
    assert result == {"action": "silent", "reason": "check_in_progress"}


def test_below_minimum_does_not_claim_a_request(session):
    session[1].write_text("small\n")
    assert check(session)["action"] == "silent"
    assert not list(session[2].glob("*.events.jsonl"))
