"""Standalone watcher daemon for Context Engine.

Keeps project indexes fresh independently of any AI client session.
Discovers indexed projects from ~/.context-engine/indexes/ and starts
file watchers for each. Writes heartbeat and PID files for monitoring.

Usage:
    context-engine-watcher              # Watch all realtime projects
    context-engine-watcher --all        # Watch all indexed projects
    context-engine-watcher --projects /path/one /path/two
    context-engine-watcher --log-file /tmp/watcher.log
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("ai_governance_mcp.context_engine.watcher_daemon")

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 60

# Default base path for indexes
DEFAULT_BASE_PATH = Path.home() / ".context-engine" / "indexes"


def _get_base_path() -> Path:
    """Resolve base path from env var or default."""
    custom = os.environ.get("AI_CONTEXT_ENGINE_INDEX_PATH")
    if custom:
        return Path(custom).resolve()
    return DEFAULT_BASE_PATH


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


def _write_heartbeat(base_path: Path, projects_watched: int) -> None:
    """Write heartbeat file with daemon status."""
    heartbeat_path = base_path.parent / "watcher-heartbeat.json"
    data = {
        "pid": os.getpid(),
        "alive_at": datetime.now(timezone.utc).isoformat(),
        "projects_watched": projects_watched,
    }
    try:
        heartbeat_path.write_text(json.dumps(data, indent=2))
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


def _heartbeat_loop(
    base_path: Path,
    manager,
    stop_event: threading.Event,
) -> None:
    """Background thread that writes heartbeat periodically."""
    while not stop_event.wait(timeout=HEARTBEAT_INTERVAL):
        count = len(getattr(manager, "_watchers", {}))
        _write_heartbeat(base_path, count)


def run_daemon(
    project_paths: list[Path] | None = None,
    watch_all: bool = False,
    log_file: str | None = None,
) -> None:
    """Run the watcher daemon.

    Args:
        project_paths: Specific projects to watch. None = auto-discover.
        watch_all: If True, watch all indexed projects regardless of mode.
        log_file: Optional log file path. None = stderr.
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
            sys.exit(1)

        for p in projects:
            pp = Path(p["project_path"])
            logger.info("Loading project: %s (mode: %s)", pp, p["index_mode"])
            manager.get_or_create_index(pp, index_mode="realtime")

    # Write PID and initial heartbeat
    _write_pid_file(base_path)
    watcher_count = len(manager._watchers)
    _write_heartbeat(base_path, watcher_count)

    logger.info(
        "Watcher daemon started (PID %d, watching %d project%s)",
        os.getpid(),
        watcher_count,
        "s" if watcher_count != 1 else "",
    )

    # Graceful shutdown
    stop_event = threading.Event()

    def _shutdown(signum, frame):
        logger.info("Received signal %d, shutting down...", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Start heartbeat thread
    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(base_path, manager, stop_event),
        name="heartbeat",
        daemon=True,
    )
    heartbeat_thread.start()

    # Block until stop signal
    try:
        stop_event.wait()
    finally:
        logger.info("Stopping watchers...")
        manager.shutdown()
        _remove_pid_file(base_path)
        _remove_heartbeat(base_path)
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

    args = parser.parse_args()
    run_daemon(
        project_paths=args.projects,
        watch_all=args.watch_all,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    main()
