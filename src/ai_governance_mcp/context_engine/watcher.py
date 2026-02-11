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
    ) -> None:
        """Initialize the file watcher.

        Args:
            project_path: Root directory to watch.
            on_change: Callback invoked with list of changed file paths.
            ignore_spec: Compiled gitignore-style spec for files to ignore.
            debounce_seconds: Minimum delay between change events and callback.
            cooldown_seconds: Minimum gap between completed re-indexes.
        """
        self.project_path = project_path
        self.on_change = on_change
        self.ignore_spec = ignore_spec
        self.debounce_seconds = debounce_seconds
        self.cooldown_seconds = cooldown_seconds

        self._observer = None
        self._pending_changes: set[Path] = set()
        self._debounce_timer: threading.Timer | None = None
        self._cooldown_timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._running = threading.Event()

        # Track last completed re-index time for cooldown enforcement
        self._last_index_time: float = 0.0

    def start(self) -> None:
        """Start watching for file changes."""
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
                if event.is_directory:
                    return
                if hasattr(event, "src_path"):
                    self._watcher._file_changed(Path(event.src_path))

        self._observer = Observer()
        self._observer.schedule(_Handler(self), str(self.project_path), recursive=True)
        self._observer.start()
        self._running.set()
        logger.info("File watcher started for: %s", self.project_path)

    def stop(self) -> None:
        """Stop watching for file changes."""
        self._running.clear()
        if self._observer is not None:
            self._observer.stop()
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

        if self.ignore_spec is not None and self.ignore_spec.match_file(str(relative)):
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
        elapsed_since_last = now - self._last_index_time
        if elapsed_since_last < self.cooldown_seconds:
            wait_time = self.cooldown_seconds - elapsed_since_last
            logger.debug(
                "Cooldown active (%.1fs remaining), deferring re-index", wait_time
            )
            # Re-queue with a timer for after cooldown expires
            with self._lock:
                self._pending_changes.update(changes)
                if self._cooldown_timer is not None:
                    self._cooldown_timer.cancel()
                timer = threading.Timer(wait_time, self._flush_changes)
                timer.daemon = True
                timer.start()
                self._cooldown_timer = timer
            return

        logger.info("Flushing %d file changes for re-indexing", len(changes))
        try:
            self.on_change(changes)
            self._last_index_time = time.time()
        except Exception as e:
            logger.error("Error in change callback: %s", e)
            # Re-queue failed changes and schedule a retry timer
            with self._lock:
                self._pending_changes.update(changes)
                if self._debounce_timer is not None:
                    self._debounce_timer.cancel()
                timer = threading.Timer(self.cooldown_seconds, self._flush_changes)
                timer.daemon = True
                timer.start()
                self._debounce_timer = timer

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
        return self._running.is_set()
