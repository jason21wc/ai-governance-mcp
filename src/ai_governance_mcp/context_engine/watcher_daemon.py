"""Standalone watcher daemon for Context Engine.

Keeps project indexes fresh independently of any AI client session.
Discovers indexed projects from ~/.context-engine/indexes/ and starts
file watchers for each. Writes heartbeat and PID files for monitoring.

Usage:
    context-engine-watcher              # Watch all realtime projects
    context-engine-watcher --all        # Watch all indexed projects
    context-engine-watcher --projects /path/one /path/two
    context-engine-watcher --log-file /tmp/watcher.log

Phase 0 (plan jiggly-honking-cascade.md):
- Self-restart after AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS (default 12h,
  set to 0 to disable). Clean exit lets launchd KeepAlive respawn, which
  releases the process's memory. The cause of observed growth is unproved.
- ±10% jitter on the target uptime, 1h floor, 1.5× hard cap.
- Phase-aligned: restart fires when elapsed >= target AND
  (idle >= 300s OR elapsed >= 1.5 × target). Idle measured via mtime of
  metadata.json files across watched projects (updated on reindex).
"""

import argparse
import json
import logging
import os
import random
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .. import memory_diagnostics as diagnostics
from ..model_runtime import activity_snapshot

logger = logging.getLogger("ai_governance_mcp.context_engine.watcher_daemon")

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 60

# Default base path for indexes
DEFAULT_BASE_PATH = Path.home() / ".context-engine" / "indexes"

# Phase 0: self-restart configuration
DEFAULT_MAX_UPTIME_HOURS = 12
MIN_MAX_UPTIME_SECONDS = 3600  # 1h floor — prevents typo-driven crashloop
JITTER_RANGE = 0.10  # ±10%
IDLE_THRESHOLD_SECONDS = 300  # 5 min of no reindex activity = "idle"
HARD_CAP_MULTIPLIER = 1.5  # elapsed >= 1.5 × target = force restart

# Phase 2: reranker model for the embedding server
DEFAULT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _get_base_path() -> Path:
    """Resolve base path from env var or default."""
    custom = os.environ.get("AI_CONTEXT_ENGINE_INDEX_PATH")
    if custom:
        return Path(custom).resolve()
    return DEFAULT_BASE_PATH


def _read_max_uptime_from_env() -> float | None:
    """Parse AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS from environment.

    Returns seconds, None if unset/zero/invalid. None means "no self-restart"
    (unbounded uptime — used for tests and explicit opt-out).
    """
    raw = os.environ.get("AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS", "").strip()
    if not raw:
        return None
    try:
        hours = float(raw)
    except ValueError:
        logger.warning(
            "Invalid AI_CONTEXT_ENGINE_WATCHER_MAX_UPTIME_HOURS=%r, ignoring", raw
        )
        return None
    if hours <= 0:
        return None
    return hours * 3600.0


def _apply_jitter_and_floor(max_uptime_seconds: float) -> float:
    """Apply ±10% jitter and enforce 1h floor on uptime target.

    Floor prevents a MAX_UPTIME_HOURS=0.01 typo from turning into a crashloop.
    Jitter spreads restart windows across deployments so they don't flap in sync.
    """
    if max_uptime_seconds < MIN_MAX_UPTIME_SECONDS:
        logger.warning(
            "max_uptime_seconds=%.1f below floor (%ds); clamping to floor",
            max_uptime_seconds,
            MIN_MAX_UPTIME_SECONDS,
        )
        max_uptime_seconds = MIN_MAX_UPTIME_SECONDS
    jitter = random.uniform(1.0 - JITTER_RANGE, 1.0 + JITTER_RANGE)  # nosec B311
    return max(max_uptime_seconds * jitter, float(MIN_MAX_UPTIME_SECONDS))


def _get_last_activity_seconds_ago(base_path: Path) -> float:
    """Seconds since the most recent metadata.json mtime across all projects.

    Used as a proxy for watcher activity: if any project was reindexed in the
    last N seconds, the user is probably active and we should defer restart.
    Returns float('inf') if no metadata files exist.
    """
    if not base_path.exists():
        return float("inf")
    max_mtime = 0.0
    try:
        for project_dir in base_path.iterdir():
            if not project_dir.is_dir():
                continue
            metadata_path = project_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                mtime = metadata_path.stat().st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
            except OSError:
                continue
    except OSError:
        return float("inf")
    if max_mtime == 0.0:
        return float("inf")
    return max(0.0, time.time() - max_mtime)


def _should_restart_now(
    elapsed_seconds: float,
    target_uptime_seconds: float,
    idle_seconds_ago: float,
) -> bool:
    """Phase-aligned restart gate.

    Restart fires when EITHER:
    - elapsed >= target AND idle >= IDLE_THRESHOLD_SECONDS (quiet-window), OR
    - elapsed >= target × HARD_CAP_MULTIPLIER (hard cap, prevents indefinite defer)
    """
    if elapsed_seconds >= target_uptime_seconds * HARD_CAP_MULTIPLIER:
        return True
    if (
        elapsed_seconds >= target_uptime_seconds
        and idle_seconds_ago >= IDLE_THRESHOLD_SECONDS
    ):
        return True
    return False


def _write_pid_file(base_path: Path) -> Path:
    """Write PID file. Returns path to the file."""
    pid_path = base_path.parent / "watcher.pid"
    pid_path.write_text(str(os.getpid()))
    return pid_path


def _remove_pid_file(base_path: Path) -> None:
    """Remove PID file if it exists."""
    pid_path = base_path.parent / "watcher.pid"
    try:
        pid_path.unlink(missing_ok=True)
    except OSError:
        pass


def _write_heartbeat(
    base_path: Path, projects_watched: int, embed_socket: str | None = None
) -> None:
    """Publish a complete heartbeat without exposing a truncated file to readers."""
    from .storage.filesystem import _atomic_write_json

    heartbeat_path = base_path.parent / "watcher-heartbeat.json"
    data = {
        "pid": os.getpid(),
        "alive_at": datetime.now(timezone.utc).isoformat(),
        "projects_watched": projects_watched,
    }
    if embed_socket:
        data["embed_socket"] = embed_socket
    try:
        _atomic_write_json(heartbeat_path, data, indent=2)
    except OSError as e:
        logger.warning("Failed to write heartbeat: %s", e)


def _remove_heartbeat(base_path: Path) -> None:
    """Remove heartbeat file."""
    heartbeat_path = base_path.parent / "watcher-heartbeat.json"
    try:
        heartbeat_path.unlink(missing_ok=True)
    except OSError:
        pass


def _discover_projects(base_path: Path, filter_mode: str | None = None) -> list[dict]:
    """Discover indexed projects from storage.

    Args:
        base_path: Index storage directory.
        filter_mode: If set, only return projects with this index_mode.
                     None returns all projects.

    Returns:
        List of dicts with project_id, project_path, index_mode.
    """
    projects = []
    if not base_path.exists():
        return projects

    for project_dir in base_path.iterdir():
        if not project_dir.is_dir() or project_dir.is_symlink():
            continue
        metadata_path = project_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
            project_path = metadata.get("project_path")
            index_mode = metadata.get("index_mode", "ondemand")
            if project_path and Path(project_path).exists():
                if filter_mode is None or index_mode == filter_mode:
                    projects.append(
                        {
                            "project_id": project_dir.name,
                            "project_path": project_path,
                            "index_mode": index_mode,
                        }
                    )
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", project_dir.name, e)

    return projects


def _watcher_ownership_loop(
    manager,
    stop_event: threading.Event,
    target_project_ids: frozenset[str],
    retry_interval: float = 30.0,
) -> None:
    """Recover released leases for admitted projects without registry loading.

    A client can own a configured project when the daemon starts, then exit
    without another file event or client request. Reconciliation may do I/O, so
    keep ownership maintenance separate from heartbeat publication.
    """
    while not stop_event.wait(timeout=retry_interval):
        with manager._index_lock:
            project_ids = target_project_ids.intersection(manager._loaded_indexes)
        for project_id in project_ids:
            with manager._index_lock:
                # Check after acquiring the lock: shutdown may have started
                # while a query or another project's reconciliation held it.
                if stop_event.is_set():
                    return
                index = manager._loaded_indexes.get(project_id)
                # Explicit --projects/--all can select an index whose stored
                # mode is ondemand. The daemon's selection controls ownership.
                if index is not None:
                    manager._ensure_watcher(Path(index.project_path), project_id)


def _heartbeat_loop(
    base_path: Path,
    manager,
    stop_event: threading.Event,
    heartbeat_interval: float,
    start_time: float,
    target_uptime_seconds: float | None,
    embed_socket: str | None = None,
    embed_server=None,
) -> None:
    """Background thread that writes heartbeat and enforces self-restart.

    Phase 0: checks uptime on each tick. When target_uptime_seconds is set
    and the phase-alignment gate opens, sets stop_event to trigger clean exit.
    launchd KeepAlive + ThrottleInterval respawns a fresh process.
    """
    while not stop_event.wait(timeout=heartbeat_interval):
        count = len(getattr(manager, "_watchers", {}))
        _write_heartbeat(base_path, count, embed_socket=embed_socket)
        _record_memory_tick(manager, embed_server)

        if target_uptime_seconds is None:
            continue  # self-restart disabled

        elapsed = time.time() - start_time
        idle = _get_last_activity_seconds_ago(base_path)
        if _should_restart_now(elapsed, target_uptime_seconds, idle):
            reason = (
                "hard-cap"
                if elapsed >= target_uptime_seconds * HARD_CAP_MULTIPLIER
                else "quiet-window"
            )
            logger.info(
                "scheduled restart: elapsed=%.1fh target=%.1fh idle=%.0fs reason=%s "
                "(see plan jiggly-honking-cascade.md)",
                elapsed / 3600.0,
                target_uptime_seconds / 3600.0,
                idle,
                reason,
            )
            stop_event.set()
            return


def _record_memory_tick(manager, embed_server=None):
    """Sample idle baselines without waiting on inference or copying a corpus."""
    if not diagnostics.is_enabled():
        return
    fields = activity_snapshot()
    try:
        if embed_server is not None:
            fields.update(embed_server.diagnostic_snapshot())
        # Do not block heartbeat publication behind a long index mutation.
        if manager._index_lock.acquire(blocking=False):
            try:
                fields.update(
                    loaded_projects=len(manager._loaded_indexes),
                    cached_chunks=sum(
                        len(i.chunks) for i in manager._loaded_indexes.values()
                    ),
                    cached_embedding_bytes=sum(
                        e.nbytes for e in manager._loaded_embeddings.values()
                    ),
                )
            finally:
                manager._index_lock.release()
        else:
            fields["index_snapshot_busy"] = True
    except Exception:
        fields["snapshot_error"] = True
    diagnostics.record("heartbeat", **fields)


def run_daemon(
    project_paths: list[Path] | None = None,
    watch_all: bool = False,
    log_file: str | None = None,
    max_uptime_seconds: float | None = None,
    heartbeat_interval: float = HEARTBEAT_INTERVAL,
) -> None:
    """Run the watcher daemon.

    Args:
        project_paths: Specific projects to watch. None = auto-discover.
        watch_all: If True, watch all indexed projects regardless of mode.
        log_file: Optional log file path. None = stderr.
        max_uptime_seconds: Phase 0 self-restart. None = read env var. 0 or
            negative = disabled. Otherwise jitter + floor applied.
        heartbeat_interval: Seconds between heartbeat writes / uptime checks.
            Production default is HEARTBEAT_INTERVAL (60s). Tests override.
    """
    # Setup logging
    log_level = os.environ.get("AI_CONTEXT_ENGINE_LOG_LEVEL", "INFO").upper()
    handlers: list[logging.Handler] = []
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    else:
        handlers.append(logging.StreamHandler(sys.stderr))

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    base_path = _get_base_path()

    if not base_path.exists():
        logger.error("Index directory does not exist: %s", base_path)
        logger.error("No projects to watch. Index a project first.")
        sys.exit(1)

    diagnostics.configure(base_path.parent / "watcher-memory.jsonl")
    diagnostics.record("startup")

    # Phase 0: resolve max_uptime_seconds from arg OR env var
    if max_uptime_seconds is None:
        max_uptime_seconds = _read_max_uptime_from_env()
    if max_uptime_seconds is not None and max_uptime_seconds > 0:
        target_uptime_seconds: float | None = _apply_jitter_and_floor(
            max_uptime_seconds
        )
    else:
        target_uptime_seconds = None

    # Prevent the daemon's own Indexer from using the socket (infinite loop)
    os.environ["AI_CONTEXT_ENGINE_EMBED_SOCKET"] = "none"

    # Import here to avoid loading ML models at import time
    from .project_manager import ProjectManager
    from .storage.filesystem import FilesystemStorage

    storage = FilesystemStorage(base_path=base_path)
    manager = ProjectManager(
        storage=storage,
        default_index_mode="realtime",
    )

    # Determine which projects to watch
    if project_paths:
        # Explicit project list — ensure each is indexed, set to realtime
        for pp in project_paths:
            pp = pp.resolve()
            if not pp.exists():
                logger.warning("Project path does not exist, skipping: %s", pp)
                continue
            logger.info("Loading project: %s", pp)
            manager.get_or_create_index(pp, index_mode="realtime")
    else:
        # Auto-discover from storage
        filter_mode = None if watch_all else "realtime"
        projects = _discover_projects(base_path, filter_mode=filter_mode)
        if not projects:
            if watch_all:
                logger.error("No indexed projects found in %s", base_path)
            else:
                logger.error(
                    "No realtime projects found. Use --all to watch all projects, "
                    "or --projects to specify paths."
                )
            manager.shutdown()
            diagnostics.close()
            sys.exit(1)

        for p in projects:
            pp = Path(p["project_path"])
            logger.info("Loading project: %s (mode: %s)", pp, p["index_mode"])
            manager.get_or_create_index(pp, index_mode="realtime")

    # Write PID and initial heartbeat
    _write_pid_file(base_path)
    watcher_count = len(manager._watchers)

    # Phase 2: start the embedding IPC server so MCP clients can call us
    embed_server = None
    embed_socket_str = None
    try:
        from ..embedding_ipc import EmbeddingServer

        _reranker = None
        from ..model_runtime import INFERENCE_LOCK, SerializedModel

        _reranker_lock = INFERENCE_LOCK

        def _get_reranker():
            nonlocal _reranker
            if _reranker is not None:
                return _reranker
            with _reranker_lock:
                if _reranker is not None:
                    return _reranker
                from sentence_transformers import CrossEncoder

                model_name = os.environ.get(
                    "AI_GOVERNANCE_RERANK_MODEL", DEFAULT_RERANK_MODEL
                )
                from ..retrieval import ALLOWED_RERANKER_MODELS

                if model_name not in ALLOWED_RERANKER_MODELS:
                    logger.warning(
                        "Reranker model %r not in allowlist, using default", model_name
                    )
                    model_name = DEFAULT_RERANK_MODEL
                logger.info("Loading reranker model: %s", model_name)
                _reranker = SerializedModel(
                    CrossEncoder(model_name, trust_remote_code=False)
                )
                return _reranker

        def encode_fn(texts, normalize_embeddings=False):
            return manager._indexer.embedding_model.encode(
                texts,
                normalize_embeddings=normalize_embeddings,
                show_progress_bar=False,
            )

        def predict_fn(pairs):
            return _get_reranker().predict(pairs)

        embed_server = EmbeddingServer(
            encode_fn=encode_fn,
            predict_fn=predict_fn,
            socket_path=base_path.parent / "embed.sock",
        )
        embed_server.start()
        embed_socket_str = str(embed_server.socket_path)
        logger.info("Embedding IPC server started: %s", embed_socket_str)
    except Exception as e:
        logger.warning(
            "Embedding IPC server failed to start: %s (semantic clients unavailable)",
            e,
        )
        embed_server = None

    _write_heartbeat(base_path, watcher_count, embed_socket=embed_socket_str)

    # Phase 0 startup log: explicit project count + self-restart config
    if target_uptime_seconds is not None:
        logger.info(
            "Phase 0: watcher daemon started (PID %d, watching %d project%s, "
            "target_uptime=%.1fh with ±%d%% jitter, 5min idle / 1.5× hard-cap)",
            os.getpid(),
            watcher_count,
            "s" if watcher_count != 1 else "",
            target_uptime_seconds / 3600.0,
            int(JITTER_RANGE * 100),
        )
    else:
        logger.info(
            "Watcher daemon started (PID %d, watching %d project%s, self-restart DISABLED)",
            os.getpid(),
            watcher_count,
            "s" if watcher_count != 1 else "",
        )

    # Graceful shutdown
    stop_event = threading.Event()

    def _shutdown(signum, frame):
        logger.info("Received signal %d, shutting down...", signum)
        stop_event.set()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

    # Start heartbeat thread (also enforces Phase 0 self-restart)
    start_time = time.time()
    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(
            base_path,
            manager,
            stop_event,
            heartbeat_interval,
            start_time,
            target_uptime_seconds,
            embed_socket_str,
            embed_server,
        ),
        name="heartbeat",
        daemon=True,
    )
    heartbeat_thread.start()

    ownership_thread = threading.Thread(
        target=_watcher_ownership_loop,
        args=(manager, stop_event, frozenset(manager._loaded_indexes)),
        name="watcher-ownership",
        daemon=True,
    )
    ownership_thread.start()

    # Block until stop signal (or self-restart triggers stop_event)
    try:
        stop_event.wait()
    finally:
        stop_event.set()
        logger.info("Stopping watchers...")
        if embed_server is not None:
            embed_server.shutdown()
            logger.info("Embedding IPC server stopped")
        manager.shutdown()
        _remove_pid_file(base_path)
        _remove_heartbeat(base_path)
        diagnostics.record("shutdown")
        diagnostics.close()
        logger.info("Watcher daemon stopped")


def main() -> None:
    """CLI entry point for context-engine-watcher."""
    parser = argparse.ArgumentParser(
        prog="context-engine-watcher",
        description="Standalone file watcher daemon for Context Engine indexes.",
    )
    parser.add_argument(
        "--projects",
        nargs="+",
        type=Path,
        help="Specific project directories to watch.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="watch_all",
        help="Watch all indexed projects regardless of stored index mode.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log to file instead of stderr.",
    )

    parser.add_argument("--supervised-worker-fd", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.platform == "win32":
        logger.warning(
            "Watcher memory supervision is unavailable on Windows; "
            "only the legacy uptime restart is active"
        )
        run_daemon(args.projects, args.watch_all, args.log_file)
        return
    from .watcher_supervisor import supervise, watch_parent

    if args.supervised_worker_fd is None:
        supervise(_get_base_path(), sys.argv[1:])
        return
    watch_parent(args.supervised_worker_fd)
    run_daemon(
        project_paths=args.projects,
        watch_all=args.watch_all,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    main()
