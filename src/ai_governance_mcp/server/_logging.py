"""Logging functions for governance audit, query, and feedback logs.

All log deques (_audit_log, _reasoning_log) live here. Functions read
``_state._settings`` via module-attribute lookup at call time — never
via ``global`` (the variable lives in ``_state``, not this module).
"""

import asyncio
import json
import logging
import os
import tempfile
from collections import deque
from pathlib import Path

from ..config import _find_project_root
from ..models import Feedback, GovernanceAuditLog, GovernanceReasoningLog, QueryLog
from ..path_resolution import safe_cwd
from ._constants import AUDIT_LOG_MAX_SIZE

logger = logging.getLogger(__name__)


class LogPathTraversal(ValueError):
    """A log path contains a traversal sequence — an active manipulation signal.

    STAYS FATAL. This is the M1 arbitrary-file-write control. Declining the write
    would be safe in itself, but a traversal attempt means something is trying to
    steer writes, and that must be loud rather than counted.
    """


class LogPathOutOfScope(ValueError):
    """A log path resolves outside every permitted root.

    ABSORBED by ``_guarded_write`` as an environment failure, unlike its sibling.
    The two used to be one ``ValueError``, and that overloading is what let the
    original incident survive its first fix: on a dead working directory the
    permitted set loses TWO entries — the cwd, and the real project root, because
    ``_find_project_root()`` stops finding its marker and returns the fallback. A
    checkout outside ``$HOME`` (Docker ``/app``, ``/workspace/...``) therefore
    raised from here, sailed past a guard that caught only ``OSError``, and turned
    a computed verdict into ``TOOL_ERROR`` exactly as before.

    Absorbing it is safe because the failure mode is *declining to write*: nothing
    reaches the filesystem on this path. The M1 control is preserved — an
    out-of-scope path still never gets written, it is now counted instead of
    crashing the call it was recording.
    """


# ---------------------------------------------------------------------------
# Durable-write failure accounting
# ---------------------------------------------------------------------------

# Counts of durable telemetry writes that failed, keyed by log kind. Read via
# get_telemetry_failures(), which _verification_response() in handlers/governance.py
# folds into every verify_governance_compliance reply — so a degraded audit trail is
# VISIBLE rather than merely survivable. (An earlier revision of this comment claimed
# that wiring existed before it did; the counter was read only by tests. Review
# caught it. If you remove the consumer, correct this line in the same commit.)
_telemetry_failures: dict[str, int] = {}


def get_telemetry_failures() -> dict[str, int]:
    """Durable telemetry writes that failed this process, by log kind.

    Empty dict is the healthy state. A non-empty dict means the in-memory audit
    trail is intact but the on-disk one has gaps — which matters when reading
    ``logs/*.jsonl`` to compute governance metrics, because the absence of a
    record would otherwise read as "this never happened".
    """
    return dict(_telemetry_failures)


def _record_write_failure(kind: str, exc: BaseException) -> None:
    """Account for a failed durable write, and say so once per kind."""
    first = kind not in _telemetry_failures
    _telemetry_failures[kind] = _telemetry_failures.get(kind, 0) + 1
    if first:
        # Once per kind per process: a dead cwd or a read-only volume would
        # otherwise log on every governance call for the process lifetime.
        logger.warning(
            "Durable %s log write failed (%s: %s). The in-memory trail is intact; "
            "on-disk telemetry for this process is incomplete. Governance verdicts "
            "are unaffected.",
            kind,
            type(exc).__name__,
            exc,
        )


def _guarded_write(log_file: Path, content: str, kind: str) -> None:
    """Write telemetry, absorbing OS-level failures.

    WHY THE GUARD IS HERE AND NOT INSIDE ``_write_log_sync``
    -------------------------------------------------------
    This is the boundary between a governance call and its own bookkeeping, and
    that is where the decision "a failed side effect must not destroy a computed
    result" belongs. ``_write_log_sync`` is a writer: its job is to write or say
    why it couldn't.

    THE FAILURE THIS EXISTS FOR. A session deleted the git worktree its own
    governance MCP server was running in. ``_find_project_root()`` then raised
    ``FileNotFoundError`` from the log-path validator on every call, the
    exception propagated out of ``log_governance_audit_async``, and the tool
    dispatcher turned a fully-computed assessment into ``TOOL_ERROR``. The
    verdict existed. It was discarded because a log line could not be appended.

    ``_rotate_jsonl_if_needed`` already stated this exact rule for its own step
    ("rotation errors fall back to unbounded append rather than crashing the
    write path") and it was applied per-line instead of per-path — the rotation
    call was protected while the validate and the write on either side of it were
    not. This makes it a property of the path.

    WHAT IS ABSORBED, AND WHY IT IS NOT "everything". ``OSError`` (the filesystem
    said no) and ``LogPathOutOfScope`` (we declined to write) are environment
    failures: in both cases nothing reached the disk, so counting them is safe.
    ``LogPathTraversal`` stays fatal — see its docstring. So does every
    programming error; a ``TypeError`` here is a bug, not weather.

    The first version of this caught ``OSError`` alone, which read as correct and
    was not: on a dead working directory a checkout outside ``$HOME`` fails with
    ``LogPathOutOfScope``, sails past an OSError-only guard, and reproduces the
    original incident. Found by review, not by the test suite, because this
    machine's checkout happens to live under ``$HOME``.
    """
    try:
        _write_log_sync(log_file, content)
    except (OSError, LogPathOutOfScope) as exc:
        _record_write_failure(kind, exc)


async def _guarded_write_async(log_file: Path, content: str, kind: str) -> None:
    """Async twin of ``_guarded_write`` — see it for the rationale."""
    try:
        await asyncio.to_thread(_write_log_sync, log_file, content)
    except (OSError, LogPathOutOfScope) as exc:
        _record_write_failure(kind, exc)


# ---------------------------------------------------------------------------
# Path validation & rotation
# ---------------------------------------------------------------------------


def _validate_log_path(log_file: Path) -> None:
    """Validate log file path is within expected boundaries.

    M1 FIX: Prevents arbitrary file writes via manipulated log path env vars.

    Args:
        log_file: The log file path to validate.

    An unavailable working directory drops CWD from the permitted roots rather
    than raising, so this check can only get STRICTER — see ``safe_cwd``.

    THE TWO FAILURES ARE DISTINCT TYPES, and conflating them cost a fix. A
    traversal sequence is an attack signal and stays fatal; an out-of-scope path
    is an environment fact and is absorbed by ``_guarded_write``. Both decline the
    write, so neither is a security relaxation — but only one deserves to take
    down the governance call that was being recorded.

    Raises:
        LogPathTraversal: the path contains a traversal sequence (fatal).
        LogPathOutOfScope: the path resolves outside every permitted root.
    """
    path_str = str(log_file)
    if ".." in path_str:
        raise LogPathTraversal("Path traversal sequence detected in log path")

    resolved = log_file.resolve()

    permitted = [
        _find_project_root().resolve(),
        Path.home().resolve(),
        Path(tempfile.gettempdir()).resolve(),
    ]
    cwd = safe_cwd()
    if cwd is not None:
        permitted.append(cwd.resolve())

    if not any(resolved.is_relative_to(base) for base in permitted):
        raise LogPathOutOfScope(
            f"Log path must be within project root, CWD, home, or temp directory: {resolved}"
        )


def _rotate_jsonl_if_needed(log_file: Path, max_bytes: int, backup_count: int) -> None:
    """Rotate JSONL log file if it exceeds max_bytes. Fail-safe: rotation
    errors fall back to unbounded append rather than crashing the write path."""
    if max_bytes <= 0:
        return
    try:
        if not log_file.exists() or log_file.stat().st_size < max_bytes:
            return
        for i in range(backup_count - 1, 0, -1):
            src = log_file.with_suffix(f".jsonl.{i}")
            dst = log_file.with_suffix(f".jsonl.{i + 1}")
            if src.exists():
                src.rename(dst)
        log_file.rename(log_file.with_suffix(".jsonl.1"))
    except OSError:
        pass


def _origin_project() -> str:
    """Which project this record came from.

    WHY THIS FIELD EXISTS (BACKLOG #261, Compliance Review #17). Until now the telemetry
    was attributed *by file location*: each checkout wrote to its own ``logs/``, so
    "which project produced this record" was answered by which directory you were
    reading. That was one mechanism doing two jobs — storage AND attribution — and the
    storage half was broken (every worktree became a separate root, so C-155 computed
    its metrics on a fraction).

    Consolidating to one user-level tree fixes storage and would have silently destroyed
    attribution. So attribution moves into the record, where it belongs and where it
    survives any future relocation. Falls back to ``"unknown"`` rather than raising —
    a telemetry write must never break the call it is recording.

    Worktrees attribute to the PROJECT, not the worktree: a session running in
    ``<repo>/.claude/worktrees/session-270`` is still doing ai-governance-mcp work, and
    a per-worktree label would re-fragment the data by a different name — the same
    mistake one layer up.
    """
    try:
        root = _find_project_root().resolve()
        # <repo>/.claude/worktrees/<name>  ->  <repo>
        if root.parent.name == "worktrees" and root.parent.parent.name == ".claude":
            root = root.parent.parent.parent
        return root.name
    except Exception:  # pragma: no cover — defensive; telemetry must not raise
        return "unknown"


def _stamp_origin(content: str) -> str:
    """Add ``project`` to a JSONL record that lacks it.

    Applied at the single write choke-point rather than in each of the four log models:
    one place to change, no schema ripple, and a record that skips this path (there is
    none today) is still valid JSON without the field.
    """
    line = content.rstrip("\n")
    if not line:
        return content
    try:
        record = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return content  # not JSON — write it through untouched
    if not isinstance(record, dict) or "project" in record:
        return content
    record["project"] = _origin_project()
    return json.dumps(record) + "\n"


def _write_log_sync(log_file: Path, content: str) -> None:
    """Synchronous log write helper for use with asyncio.to_thread.

    H2 FIX: Isolated sync function enables non-blocking async wrapper.
    M1 FIX: Validates path before writing.
    #261: Stamps the originating project, now that all projects share one log tree.
    """
    from . import _state

    _validate_log_path(log_file)
    content = _stamp_origin(content)
    if _state._settings:
        _rotate_jsonl_if_needed(
            log_file, _state._settings.log_max_bytes, _state._settings.log_backup_count
        )
    fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    # encoding PINNED. Without it this used the locale default, so a governance
    # record containing non-ASCII (action text, principle prose, an em-dash) could
    # raise UnicodeEncodeError on a non-UTF-8 locale. That is NOT an OSError, so it
    # would bypass the _guarded_write boundary and destroy the verdict it was
    # recording — the original bug through a different door. Found by review.
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())


# ---------------------------------------------------------------------------
# Query & feedback logging
# ---------------------------------------------------------------------------


async def log_query_async(query_log: QueryLog) -> None:
    """Log query for analytics (async, non-blocking).

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "queries.jsonl"
        content = query_log.model_dump_json() + "\n"
        await _guarded_write_async(log_file, content, "query")


def log_query(query_log: QueryLog) -> None:
    """Log query for analytics (sync fallback for non-async contexts)."""
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "queries.jsonl"
        _guarded_write(log_file, query_log.model_dump_json() + "\n", "query")


async def log_feedback_async(feedback: Feedback) -> None:
    """Log feedback for future improvement (async, non-blocking).

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "feedback.jsonl"
        content = feedback.model_dump_json() + "\n"
        await _guarded_write_async(log_file, content, "feedback")


def log_feedback_entry(feedback: Feedback) -> None:
    """Log feedback for future improvement (sync fallback)."""
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "feedback.jsonl"
        _guarded_write(log_file, feedback.model_dump_json() + "\n", "feedback")


# ---------------------------------------------------------------------------
# Governance audit log
# ---------------------------------------------------------------------------

_audit_log: deque[GovernanceAuditLog] = deque(maxlen=AUDIT_LOG_MAX_SIZE)


async def log_governance_audit_async(audit_entry: GovernanceAuditLog) -> None:
    """Log governance assessment for audit trail (async, non-blocking).

    Per §4.6 Audit Trail Requirements: Every evaluate_governance() call
    generates an audit record for pattern analysis and bypass detection.

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    from . import _state

    _audit_log.append(audit_entry)

    if _state._settings:
        log_file = _state._settings.logs_path / "governance_audit.jsonl"
        content = audit_entry.model_dump_json() + "\n"
        await _guarded_write_async(log_file, content, "governance_audit")


def log_governance_audit(audit_entry: GovernanceAuditLog) -> None:
    """Log governance assessment for audit trail (sync fallback)."""
    from . import _state

    _audit_log.append(audit_entry)

    if _state._settings:
        log_file = _state._settings.logs_path / "governance_audit.jsonl"
        _guarded_write(
            log_file, audit_entry.model_dump_json() + "\n", "governance_audit"
        )


def get_audit_log() -> list[GovernanceAuditLog]:
    """Get the in-memory audit log for verification."""
    return list(_audit_log)


# ---------------------------------------------------------------------------
# Governance reasoning log
# ---------------------------------------------------------------------------

_reasoning_log: deque[GovernanceReasoningLog] = deque(maxlen=AUDIT_LOG_MAX_SIZE)


async def log_reasoning_async(entry: GovernanceReasoningLog) -> None:
    """Log governance reasoning trace asynchronously.

    Links to existing audit entry via audit_id.
    Part of Governance Reasoning Externalization feature.
    """
    from . import _state

    _reasoning_log.append(entry)
    logger.debug("Logged reasoning for audit %s", entry.audit_id)

    if _state._settings:
        log_file = _state._settings.logs_path / "governance_reasoning.jsonl"
        content = entry.model_dump_json() + "\n"
        await _guarded_write_async(log_file, content, "governance_reasoning")


def log_reasoning_sync(entry: GovernanceReasoningLog) -> None:
    """Log governance reasoning trace synchronously (fallback)."""
    from . import _state

    _reasoning_log.append(entry)

    if _state._settings:
        log_file = _state._settings.logs_path / "governance_reasoning.jsonl"
        _guarded_write(log_file, entry.model_dump_json() + "\n", "governance_reasoning")


def get_reasoning_log() -> list[GovernanceReasoningLog]:
    """Get the in-memory reasoning log for inspection."""
    return list(_reasoning_log)


# ---------------------------------------------------------------------------
# Shutdown helper
# ---------------------------------------------------------------------------


def _flush_all_logs() -> None:
    """Flush all log files to ensure data is persisted before exit.

    H3 FIX: Called before os._exit() to reduce data loss on shutdown.
    """
    from . import _state

    if _state._settings:
        log_files = [
            "queries.jsonl",
            "feedback.jsonl",
            "governance_audit.jsonl",
            "governance_reasoning.jsonl",
        ]
        for log_name in log_files:
            log_file = _state._settings.logs_path / log_name
            try:
                if log_file.exists():
                    with open(log_file, "a") as f:
                        f.flush()
                        os.fsync(f.fileno())
            except Exception as e:
                logger.warning(f"Failed to flush {log_name}: {e}")
