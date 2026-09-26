"""File system watcher for real-time indexing.

Monitors project files for changes and triggers incremental re-indexing.
Uses watchdog library for cross-platform file system events.

Smart re-indexing strategy:
- Default debounce of 2 seconds to batch rapid changes (e.g., IDE auto-save).
- Post-index cooldown prevents cascading re-indexes during burst edits.
- Only triggers when actual file changes are detected (ignores duplicates).
- Safety limit: MAX_PENDING_CHANGES (10,000) triggers force-flush.
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable

import pathspec

logger = logging.getLogger("ai_governance_mcp.context_engine.watcher")

# Maximum pending changes before force-flush to prevent unbounded memory
MAX_PENDING_CHANGES = 10_000

# Default debounce: 2 seconds batches most IDE auto-save and AI-driven edits
DEFAULT_DEBOUNCE_SECONDS = 2.0

# Minimum gap between completed re-indexes (prevents cascading re-index loop)
DEFAULT_COOLDOWN_SECONDS = 5.0


def _lock_ownership_file(stream, windows: bool = os.name == "nt") -> None:
    """Nonblocking OS ownership; descriptor close releases either backend."""
    if windows:
        import msvcrt

        stream.seek(0)
        # Windows permits locking a region beyond EOF, including an empty file.
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)


class FileWatcher:
    """Watches project files for changes and triggers re-indexing.

    Uses watchdog for filesystem events with smart debouncing:
    - Debounce timer batches rapid changes (e.g., git checkout, AI edits)
    - Post-index cooldown prevents re-index storms during active development
    - Duplicate file events within a batch are deduplicated via set
    """

    def __init__(
        self,
        project_path: Path,
        on_change: Callable[[list[Path]], None],
        ignore_spec: pathspec.GitIgnoreSpec | None = None,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        ownership_path: Path | None = None,
        ignore_loader: Callable[[], pathspec.GitIgnoreSpec] | None = None,
    ) -> None:
        """Initialize the file watcher.

        Args:
            project_path: Root directory to watch.
            on_change: Callback invoked with list of changed file paths.
            ignore_spec: Compiled gitignore-style spec for files to ignore.
            debounce_seconds: Minimum delay between change events and callback.
            cooldown_seconds: Minimum gap between completed re-indexes.
            ignore_loader: Reload root ignore policy when either control file changes.
        """
        self.project_path = project_path
        self.on_change = on_change
        self.ignore_spec = ignore_spec
        self.ignore_loader = ignore_loader
        self.debounce_seconds = debounce_seconds
        self.cooldown_seconds = cooldown_seconds
        self.ownership_path = ownership_path
        self._ownership_file = None

        self._observer = None
        self._pending_changes: set[Path] = set()
        self._debounce_timer: threading.Timer | None = None
        self._cooldown_timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._flush_lock = threading.Lock()  # Serializes _do_flush invocations
        self._running = threading.Event()

        # Track last completed re-index time for cooldown enforcement
        self._last_index_time: float = 0.0

    def start(self) -> None:
        """Start watching for file changes."""
        if self._running.is_set() or self._ownership_file is not None:
            return
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            logger.warning(
                "watchdog not installed. File watching disabled. "
                "Install with: pip install watchdog"
            )
            return

        class _Handler(FileSystemEventHandler):
            def __init__(self, watcher: "FileWatcher"):
                self._watcher = watcher

            def on_any_event(self, event):
                # Reading policy must not recursively schedule more reads on
                # platforms that report opened/closed-without-write events.
                if event.is_directory or event.event_type not in {
                    "created",
                    "modified",
                    "deleted",
                    "moved",
                }:
                    return
                for name in ("src_path", "dest_path"):
                    path = getattr(event, name, None)
                    if path:
                        self._watcher._file_changed(Path(path))

        if not self._acquire_ownership():
            return
        try:
            self._observer = Observer()
            self._observer.schedule(
                _Handler(self), str(self.project_path), recursive=True
            )
            self._observer.start()
            self._running.set()
        except BaseException:
            self.stop()
            raise
        logger.info("File watcher started for: %s", self.project_path)

    def _acquire_ownership(self) -> bool:
        """A stable local-filesystem lock coordinates daemon and stdio clients.

        Never unlink/replace the lock file: competing owners must lock the same
        inode. Closing the descriptor (including process exit) releases ownership.
        Unsupported locking or I/O errors disable this watcher, not exclusion.
        """
        if self.ownership_path is None:
            return True
        stream = None
        try:
            self.ownership_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(
                self.ownership_path,
                os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            stream = os.fdopen(fd, "a+")
            _lock_ownership_file(stream)
            self._ownership_file = stream
            return True
        except (ImportError, OSError) as exc:
            if stream is not None:
                stream.close()
            logger.info(
                "Watcher ownership unavailable for %s: %s", self.project_path, exc
            )
            return False

    def _release_ownership_if_stopped(self) -> None:
        # Must hold _flush_lock: a callback may still be writing after stop().
        if not self._running.is_set() and self._ownership_file is not None:
            self._ownership_file.close()
            self._ownership_file = None

    def reconcile(self) -> None:
        """Catch changes made while no watcher owned this project."""
        # The indexer treats paths as hints and reconciles the full manifest.
        # A nonempty root hint survives the normal retry/coalescing path even
        # when no new filesystem event arrives after a failed first attempt.
        self._do_flush([self.project_path])

    def stop(self) -> None:
        """Stop watching for file changes."""
        self._running.clear()
        if self._observer is not None:
            self._observer.stop()
            if (
                self._observer.ident is not None
                and self._observer is not threading.current_thread()
            ):
                self._observer.join(timeout=5)
            if self._observer.is_alive():
                logger.warning("Observer thread did not stop within timeout")
            self._observer = None
        with self._lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
                self._debounce_timer = None
            if self._cooldown_timer is not None:
                self._cooldown_timer.cancel()
                self._cooldown_timer = None
        # Never join an active indexing callback here: its publication may need
        # the manager lock held by the caller doing eviction. The callback's
        # finally block releases this instance's lease when it finishes.
        if self._flush_lock.acquire(blocking=False):
            try:
                self._release_ownership_if_stopped()
            finally:
                self._flush_lock.release()
        logger.info("File watcher stopped")

    def _file_changed(self, file_path: Path) -> None:
        """Handle a file change event with debouncing."""
        if not self._running.is_set():
            return

        # Check ignore patterns
        try:
            relative = file_path.relative_to(self.project_path)
        except ValueError:
            return

        policy_changed = relative.as_posix() in {".gitignore", ".contextignore"}
        if policy_changed and self.ignore_loader is not None:
            try:
                self.ignore_spec = self.ignore_loader()
            except Exception:
                # The indexer validates policy again before indexing. Until it
                # succeeds, retain all event hints so newly included files cannot
                # lose edits behind a stale event filter. No content is read here.
                self.ignore_spec = None
                logger.exception(
                    "Cannot reload ignore policy; scheduling reconciliation"
                )

        if (
            not policy_changed
            and self.ignore_spec is not None
            and self.ignore_spec.match_file(str(relative))
        ):
            return

        changes_to_flush = None

        with self._lock:
            self._pending_changes.add(file_path)

            # Force-flush if pending changes exceed limit (prevents unbounded memory)
            if len(self._pending_changes) >= MAX_PENDING_CHANGES:
                logger.warning(
                    "Pending changes reached %d, force-flushing", MAX_PENDING_CHANGES
                )
                if self._debounce_timer is not None:
                    self._debounce_timer.cancel()
                    self._debounce_timer = None
                # Extract changes inside lock, flush OUTSIDE lock (M2 fix)
                changes_to_flush = list(self._pending_changes)
                self._pending_changes.clear()
            else:
                # Reset debounce timer
                if self._debounce_timer is not None:
                    self._debounce_timer.cancel()

                self._debounce_timer = threading.Timer(
                    self.debounce_seconds, self._flush_changes
                )
                self._debounce_timer.daemon = True
                self._debounce_timer.start()

        # Force-flush happens outside lock to avoid blocking other events
        if changes_to_flush is not None:
            self._do_flush(changes_to_flush)

    def _do_flush(self, changes: list[Path]) -> None:
        """Execute the flush callback with cooldown enforcement."""
        if not self._running.is_set():
            return

        # Enforce cooldown: if a re-index just completed, defer
        now = time.time()
        with self._lock:
            last_index = self._last_index_time
        elapsed_since_last = now - last_index
        if elapsed_since_last < self.cooldown_seconds:
            wait_time = self.cooldown_seconds - elapsed_since_last
            logger.debug(
                "Cooldown active (%.1fs remaining), deferring re-index", wait_time
            )
            # Re-queue with a timer for after cooldown expires
            with self._lock:
                if not self._running.is_set():
                    return
                self._pending_changes.update(changes)
                if self._cooldown_timer is not None:
                    self._cooldown_timer.cancel()
                timer = threading.Timer(wait_time, self._flush_changes)
                timer.daemon = True
                timer.start()
                self._cooldown_timer = timer
            return

        # Prevent concurrent flushes — overlapping incremental updates race on
        # atomic file renames (.tmp → .json), causing ENOENT errors that trip
        # the circuit breaker after 3 consecutive failures.
        if not self._flush_lock.acquire(blocking=False):
            logger.debug(
                "Flush already in progress, re-queuing %d changes", len(changes)
            )
            with self._lock:
                if not self._running.is_set():
                    return
                self._pending_changes.update(changes)
                if self._cooldown_timer is not None:
                    self._cooldown_timer.cancel()
                timer = threading.Timer(self.cooldown_seconds, self._flush_changes)
                timer.daemon = True
                timer.start()
                self._cooldown_timer = timer
            return

        try:
            # stop() can race the initial running check while we acquire the
            # flush lock. A stopped instance must not begin another write.
            if not self._running.is_set():
                return
            logger.info("Flushing %d file changes for re-indexing", len(changes))
            try:
                self.on_change(changes)
                with self._lock:
                    self._last_index_time = time.time()
            except Exception as e:
                logger.error("Error in change callback: %s", e)
                # Re-queue failed changes and schedule a retry timer
                with self._lock:
                    if not self._running.is_set():
                        return
                    self._pending_changes.update(changes)
                    if self._cooldown_timer is not None:
                        self._cooldown_timer.cancel()
                    timer = threading.Timer(self.cooldown_seconds, self._flush_changes)
                    timer.daemon = True
                    timer.start()
                    self._cooldown_timer = timer
        finally:
            self._release_ownership_if_stopped()
            self._flush_lock.release()

    def _flush_changes(self) -> None:
        """Flush pending changes to the callback."""
        if not self._running.is_set():
            return
        with self._lock:
            if not self._pending_changes:
                return
            changes = list(self._pending_changes)
            self._pending_changes.clear()

        self._do_flush(changes)

    @property
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        obs = self._observer
        return self._running.is_set() and obs is not None and obs.is_alive()
