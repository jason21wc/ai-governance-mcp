"""Logging functions for governance audit, query, and feedback logs.

All log deques (_audit_log, _reasoning_log) live here. Functions read
``_state._settings`` via module-attribute lookup at call time — never
via ``global`` (the variable lives in ``_state``, not this module).
"""

import asyncio
import logging
import os
import tempfile
from collections import deque
from pathlib import Path

from ..config import _find_project_root
from ..models import Feedback, GovernanceAuditLog, GovernanceReasoningLog, QueryLog
from ._constants import AUDIT_LOG_MAX_SIZE

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Path validation & rotation
# ---------------------------------------------------------------------------


def _validate_log_path(log_file: Path) -> None:
    """Validate log file path is within expected boundaries.

    M1 FIX: Prevents arbitrary file writes via manipulated log path env vars.

    Args:
        log_file: The log file path to validate.

    Raises:
        ValueError: If path contains traversal sequences or is outside expected bounds.
    """
    path_str = str(log_file)
    if ".." in path_str:
        raise ValueError("Path traversal sequence detected in log path")

    resolved = log_file.resolve()

    project_root = _find_project_root().resolve()
    cwd = Path.cwd().resolve()
    home_dir = Path.home().resolve()
    temp_dir = Path(tempfile.gettempdir()).resolve()

    is_in_project = resolved.is_relative_to(project_root)
    is_in_cwd = resolved.is_relative_to(cwd)
    is_in_home = resolved.is_relative_to(home_dir)
    is_in_temp = resolved.is_relative_to(temp_dir)

    if not (is_in_project or is_in_cwd or is_in_home or is_in_temp):
        raise ValueError(
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


def _write_log_sync(log_file: Path, content: str) -> None:
    """Synchronous log write helper for use with asyncio.to_thread.

    H2 FIX: Isolated sync function enables non-blocking async wrapper.
    M1 FIX: Validates path before writing.
    """
    from . import _state

    _validate_log_path(log_file)
    if _state._settings:
        _rotate_jsonl_if_needed(
            log_file, _state._settings.log_max_bytes, _state._settings.log_backup_count
        )
    fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a") as f:
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
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_query(query_log: QueryLog) -> None:
    """Log query for analytics (sync fallback for non-async contexts)."""
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "queries.jsonl"
        _write_log_sync(log_file, query_log.model_dump_json() + "\n")


async def log_feedback_async(feedback: Feedback) -> None:
    """Log feedback for future improvement (async, non-blocking).

    H2 FIX: Uses asyncio.to_thread to avoid blocking the event loop.
    """
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "feedback.jsonl"
        content = feedback.model_dump_json() + "\n"
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_feedback_entry(feedback: Feedback) -> None:
    """Log feedback for future improvement (sync fallback)."""
    from . import _state

    if _state._settings:
        log_file = _state._settings.logs_path / "feedback.jsonl"
        _write_log_sync(log_file, feedback.model_dump_json() + "\n")


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
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_governance_audit(audit_entry: GovernanceAuditLog) -> None:
    """Log governance assessment for audit trail (sync fallback)."""
    from . import _state

    _audit_log.append(audit_entry)

    if _state._settings:
        log_file = _state._settings.logs_path / "governance_audit.jsonl"
        _write_log_sync(log_file, audit_entry.model_dump_json() + "\n")


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
        await asyncio.to_thread(_write_log_sync, log_file, content)


def log_reasoning_sync(entry: GovernanceReasoningLog) -> None:
    """Log governance reasoning trace synchronously (fallback)."""
    from . import _state

    _reasoning_log.append(entry)

    if _state._settings:
        log_file = _state._settings.logs_path / "governance_reasoning.jsonl"
        _write_log_sync(log_file, entry.model_dump_json() + "\n")


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
