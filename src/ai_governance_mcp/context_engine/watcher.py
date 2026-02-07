"""File system watcher for real-time indexing.

Monitors project files for changes and triggers incremental re-indexing.
Uses watchdog library for cross-platform file system events.
Default debounce of 500ms to batch rapid changes.
"""

import logging
import threading
from pathlib import Path
from typing import Callable

import pathspec

logger = logging.getLogger("ai_governance_mcp.context_engine.watcher")

# L5: Maximum pending changes before force-flush to prevent unbounded memory
MAX_PENDING_CHANGES = 10_000


class FileWatcher:
    """Watches project files for changes and triggers re-indexing.

    Uses watchdog for filesystem events with debouncing to batch
    rapid changes (e.g., git checkout, IDE auto-save).
    """

    def __init__(
        self,
        project_path: Path,
        on_change: Callable[[list[Path]], None],
        ignore_spec: pathspec.GitIgnoreSpec | None = None,
        debounce_seconds: float = 0.5,
    ) -> None:
        """Initialize the file watcher.

        Args:
            project_path: Root directory to watch.
            on_change: Callback invoked with list of changed file paths.
            ignore_spec: Compiled gitignore-style spec for files to ignore.
            debounce_seconds: Minimum delay between change callbacks.
        """
        self.project_path = project_path
        self.on_change = on_change
        self.ignore_spec = ignore_spec
        self.debounce_seconds = debounce_seconds

        self._observer = None
        self._pending_changes: set[Path] = set()
        self._debounce_timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._running = threading.Event()

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
        # H2 fix: Lock protects timer access from race with _file_changed
        with self._lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
                self._debounce_timer = None
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

        with self._lock:
            self._pending_changes.add(file_path)

            # L5: Force-flush if pending changes exceed limit (prevents unbounded memory)
            if len(self._pending_changes) >= MAX_PENDING_CHANGES:
                logger.warning(
                    "Pending changes reached %d, force-flushing", MAX_PENDING_CHANGES
                )
                if self._debounce_timer is not None:
                    self._debounce_timer.cancel()
                    self._debounce_timer = None
                # Release lock before flush to avoid holding it during callback
                changes = list(self._pending_changes)
                self._pending_changes.clear()
                # Flush outside lock
                self._do_flush(changes)
                return

            # Reset debounce timer
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()

            self._debounce_timer = threading.Timer(
                self.debounce_seconds, self._flush_changes
            )
            self._debounce_timer.start()

    def _do_flush(self, changes: list[Path]) -> None:
        """Execute the flush callback with error handling."""
        logger.info("Flushing %d file changes for re-indexing", len(changes))
        try:
            self.on_change(changes)
        except Exception as e:
            logger.error("Error in change callback: %s", e)

    def _flush_changes(self) -> None:
        """Flush pending changes to the callback."""
        # H4 fix: Guard against post-stop execution from timer callback
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
