#!/usr/bin/env python3
"""Advisory journal accounting, not proof that memory is complete (BACKLOG #248).

Two separate signals: observed content freshness and MAIN-agent self-attested
analysis completion. No tool-name/command parsing; no-change is a valid outcome,
NOT independently observed execution. A HEAD move earns no freshness credit.
External edits without a HEAD move remain indistinguishable from local edits.

One locked, atomically replaced state file per checkout + transcript path. A
request covers the transcript checkpoint captured at dispatch, never later EOF.
After RECENCY new lines a pending request may be replaced: bounded retry, not
proof a slow analyst stopped. A first observation cannot reconstruct old writes.
Missing/corrupt state rebaselines; failed storage returns explicit degradation
(the shell emits an advisory without a receipt). A busy lock stays silent for
this prompt, with a diagnostic, so the lock holder cannot be double-dispatched.
Never block prompts.

State and bounded event logs contain identifiers/hashes, not transcript/memory
content. Events distinguish requested from completed; all completion outcomes
carry evidence=main_agent_self_attestation. Legacy fired-to-ran proxies must not
silently treat these receipts as independently verified execution.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import uuid

MEMORY_FILES = (
    "SESSION-STATE.md",
    "PROJECT-MEMORY.md",
    "LEARNING-LOG.md",
    "BACKLOG.md",
    "OPERATIONS.md",
    "ARCHITECTURE.md",
)
OUTCOMES = ("no_change", "proposals", "applied")
MEMORY_PATHS = {
    prefix + name for prefix in ("", "_ai-context/") for name in MEMORY_FILES
}
MAX_STATE = 131072
MAX_MEMORY = 8 * 1024 * 1024


def is_digest(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value) <= set("0123456789abcdef")
    )


def default_state_dir():
    return Path(
        os.environ.get(
            "JOURNAL_STATE_DIR", str(Path.home() / ".cache/ai-governance/journal")
        )
    )


@contextmanager
def regular_file(path, flags=os.O_RDONLY):
    """Do not follow final symlinks or block on FIFOs in advisory inputs."""
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("not a regular file")
        with os.fdopen(
            fd, "r+b" if flags & os.O_RDWR else "rb", closefd=False
        ) as stream:
            yield stream
    finally:
        os.close(fd)


def key_for(root, transcript):
    return hashlib.sha256(
        json.dumps([str(root.resolve()), str(transcript.resolve())]).encode()
    ).hexdigest()


@contextmanager
def locked(state_dir, key):
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if state_dir.is_symlink():
        raise ValueError("state directory must not be a symlink")
    with regular_file(state_dir / (key + ".lock"), os.O_RDWR | os.O_CREAT) as lock:
        deadline = time.monotonic() + 0.75
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("journal state lock busy")
                time.sleep(0.01)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def atomic_write(path, text):
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def read_state(path):
    try:
        with regular_file(path) as f:
            state = json.loads(f.read(MAX_STATE))
        valid = (
            type(state["version"]) is int
            and state["version"] == 1
            and all(type(state[k]) is int and state[k] >= 0 for k in ("lines", "size"))
            and all(
                type(state[k]) is int and 0 <= state[k] <= state["lines"]
                for k in ("fresh_at", "analyzed_at", "requested_at")
            )
            and is_digest(state["digest"])
            and isinstance(state["identity"], list)
            and len(state["identity"]) == 2
            and all(type(value) is int and value >= 0 for value in state["identity"])
            and (state["head"] is None or isinstance(state["head"], str))
            and isinstance(state["memory"], dict)
            and set(state["memory"]) == MEMORY_PATHS
            and isinstance(state["uncertain_memory"], list)
            and all(
                isinstance(name, str) and name in MEMORY_PATHS
                for name in state["uncertain_memory"]
            )
            and all(
                isinstance(k, str) and (v is None or is_digest(v))
                for k, v in state["memory"].items()
            )
        )
        pending = state["pending"]
        if pending is not None:
            valid = (
                valid
                and isinstance(pending["request_id"], str)
                and type(pending["covered_lines"]) is int
                and 0 <= pending["covered_lines"] <= state["lines"]
                and pending["covered_lines"] == state["requested_at"]
            )
        return state if valid else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def transcript_snapshot(path, old):
    """Hash the prior prefix as well as current bytes: detect truncate+regrow.

    Read only the size present at open, not a growing writer's moving EOF.
    Newlines are the existing hook's activity unit, independent of host schema.
    """
    digest, prefix = hashlib.sha256(), hashlib.sha256()
    offset = lines = 0
    old_size = old["size"] if old else 0
    with regular_file(path) as f:
        info = os.fstat(f.fileno())
        while offset < info.st_size:
            chunk = f.read(min(65536, info.st_size - offset))
            if not chunk:
                raise ValueError("transcript changed while reading")
            digest.update(chunk)
            if offset < old_size:
                prefix.update(chunk[: old_size - offset])
            offset += len(chunk)
            lines += chunk.count(b"\n")
    identity = [info.st_dev, info.st_ino]
    continuous = bool(
        old
        and old["identity"] == identity
        and offset >= old_size
        and old["digest"] == prefix.hexdigest()
    )
    return {
        "lines": lines,
        "size": offset,
        "digest": digest.hexdigest(),
        "identity": identity,
    }, continuous


def head_at(root):
    # A real non-git directory is stable too. Git failures inside a checkout
    # remain UNKNOWN and never earn freshness credit.
    try:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        p = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            env=env,
            timeout=0.5,
        )
        if p.returncode == 0:
            return p.stdout.strip()
        if not any((parent / ".git").exists() for parent in (root, *root.parents)):
            return "non-git"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def fingerprints(root):
    result = {}
    for directory in (root, root / "_ai-context"):
        for name in MEMORY_FILES:
            path = directory / name
            value = None
            try:
                # Never follow an _ai-context directory link into host memory.
                if directory.is_symlink():
                    raise ValueError("linked memory directory")
                with regular_file(path) as f:
                    if os.fstat(f.fileno()).st_size > MAX_MEMORY:
                        raise ValueError("memory file exceeds bounded read")
                    data = f.read(MAX_MEMORY + 1)
                    if len(data) > MAX_MEMORY:
                        raise ValueError("memory file grew beyond bounded read")
                    value = hashlib.sha256(data).hexdigest()
            except (OSError, ValueError):
                pass  # Unreadable/deleted is not evidence of maintenance.
            result[str(path.relative_to(root))] = value
    return result


def event(state_dir, key, kind, request, **fields):
    path = state_dir / (key + ".events.jsonl")
    row = {
        "version": 1,
        "event": kind,
        "session_key": key,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **request,
        **fields,
    }
    try:
        try:
            with regular_file(path) as f:
                f.seek(max(0, os.fstat(f.fileno()).st_size - 100000))
                previous = f.read(100000).decode("utf-8", errors="replace").splitlines()
                # Drop a possibly truncated first line; logs are explicitly bounded.
                previous = previous[1:] if f.tell() >= 100000 else previous
        except FileNotFoundError:
            previous = []
        atomic_write(path, "\n".join(previous[-199:] + [json.dumps(row)]) + "\n")
    except (OSError, ValueError):
        print(
            "[journal-state] event log unavailable; accounting is incomplete",
            file=sys.stderr,
        )


def check(root, transcript, state_dir, min_lines=250, recency=400):
    root, transcript, state_dir = (
        Path(root).resolve(),
        Path(transcript),
        Path(state_dir),
    )
    try:
        if min_lines < 1 or recency < 1:
            raise ValueError("positive activity thresholds required")
        key = key_for(root, transcript)
        path = state_dir / (key + ".state.json")
        with locked(state_dir, key):
            old = read_state(path)
            snap, continuous = transcript_snapshot(transcript, old)
            if not continuous:
                old = None
            before_head = head_at(root)
            memory = fingerprints(root)
            head = head_at(root)
            fresh = bool(
                old
                and head is not None
                and old["head"] == before_head == head
                and any(
                    value is not None
                    and value != old["memory"].get(name)
                    and name not in old["uncertain_memory"]
                    for name, value in memory.items()
                )
            )
            state = old or {
                "version": 1,
                "fresh_at": 0,
                "analyzed_at": 0,
                "requested_at": 0,
                "pending": None,
                "uncertain_memory": [],
            }
            uncertain = set(old["uncertain_memory"]) if old else set()
            for name, value in memory.items():
                if value is not None:
                    # A readable sample rebaselines this path, but any prior
                    # uncertainty excluded it from freshness above.
                    uncertain.discard(name)
                elif old and (
                    head is None or old["head"] != before_head or before_head != head
                ):
                    # Carry provenance with last-good hashes over a HEAD change,
                    # including repeated unavailable samples. Other readable
                    # memory paths remain independently eligible for credit.
                    uncertain.add(name)
            # A transient read failure/deletion must not erase the last good
            # baseline and credit restoration of identical bytes as maintenance.
            if old:
                memory = {
                    name: value if value is not None else old["memory"].get(name)
                    for name, value in memory.items()
                }
            # Do not associate pre-merge hashes with post-merge HEAD: the next
            # sample would otherwise misclassify the merge as a local edit.
            if before_head != head:
                head = None
            state.update(
                snap, head=head, memory=memory, uncertain_memory=sorted(uncertain)
            )
            if fresh:
                state["fresh_at"] = snap["lines"]
            checkpoint = max(
                state["fresh_at"], state["analyzed_at"], state["requested_at"]
            )
            eligible = snap["lines"] >= min_lines and (
                checkpoint == 0 or snap["lines"] - checkpoint >= recency
            )
            result = {
                "action": "silent",
                "reason": "memory_changed" if fresh else "activity_budget",
                "session_key": key,
            }
            if eligible:
                request = {
                    "request_id": uuid.uuid4().hex,
                    "covered_lines": snap["lines"],
                }
                state["pending"] = request
                state["requested_at"] = snap["lines"]
                result.update(action="fire", reason="new_activity", **request)
            atomic_write(path, json.dumps(state))
            if eligible:
                event(
                    state_dir,
                    key,
                    "requested",
                    request,
                    evidence="directive_issued_not_execution",
                )
            return result
    except TimeoutError:
        # An existing checker owns the bounded critical section. An untracked
        # fallback directive here would defeat duplicate suppression itself.
        print(
            "[journal-state] another check is in progress; retry next prompt",
            file=sys.stderr,
        )
        return {"action": "silent", "reason": "check_in_progress"}
    except (OSError, ValueError, TypeError) as e:
        print("[journal-state] unavailable: " + type(e).__name__, file=sys.stderr)
        return {"action": "degraded", "reason": "state_unavailable"}


def complete(root, transcript, state_dir, request_id, outcome):
    root, transcript, state_dir = (
        Path(root).resolve(),
        Path(transcript),
        Path(state_dir),
    )
    try:
        if outcome not in OUTCOMES:
            raise ValueError("unsupported completion outcome")
        key = key_for(root, transcript)
        path = state_dir / (key + ".state.json")
        with locked(state_dir, key):
            state = read_state(path)
            if state is None:
                return {"accepted": False, "reason": "no_current_request"}
            _, continuous = transcript_snapshot(transcript, state)
            pending = state["pending"]
            if not continuous or not pending or pending["request_id"] != request_id:
                return {"accepted": False, "reason": "stale_or_foreign_request"}
            state["analyzed_at"] = max(state["analyzed_at"], pending["covered_lines"])
            state["pending"] = None
            atomic_write(path, json.dumps(state))
            event(
                state_dir,
                key,
                "completed",
                pending,
                outcome=outcome,
                evidence="main_agent_self_attestation",
            )
            return {
                "accepted": True,
                "covered_lines": pending["covered_lines"],
                "evidence": "main_agent_self_attestation",
            }
    except (OSError, ValueError, TypeError):
        return {"accepted": False, "reason": "state_unavailable"}


class AdvisoryParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main():
    parser = AdvisoryParser(description=__doc__)
    parser.add_argument("command", choices=("check", "complete"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--state-dir", type=Path, default=default_state_dir())
    parser.add_argument("--min-lines", type=int, default=250)
    parser.add_argument("--recency", type=int, default=400)
    parser.add_argument("--request-id")
    parser.add_argument("--outcome", choices=OUTCOMES)
    try:
        args = parser.parse_args()
        if args.command == "check":
            result = check(
                args.root, args.transcript, args.state_dir, args.min_lines, args.recency
            )
        else:
            result = complete(
                args.root,
                args.transcript,
                args.state_dir,
                args.request_id,
                args.outcome,
            )
    except (ValueError, OSError):
        result = {
            "action": "degraded",
            "accepted": False,
            "reason": "invalid_arguments",
        }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
