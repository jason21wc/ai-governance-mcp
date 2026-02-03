"""File system watcher for real-time indexing.

Monitors project files for changes and triggers incremental re-indexing.
Uses watchdog library for cross-platform file system events.
Default debounce of 500ms to batch rapid changes.
"""

import logging
import threading
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("ai_governance_mcp.context_engine.watcher")


class FileWatcher:
    """Watches project files for changes and triggers re-indexing.

    Uses watchdog for filesystem events with debouncing to batch
    rapid changes (e.g., git checkout, IDE auto-save).
    """

    def __init__(
        self,
        project_path: Path,
        on_change: Callable[[list[Path]], None],
        ignore_patterns: Optional[list[str]] = None,
        debounce_seconds: float = 0.5,
    ) -> None:
        """Initialize the file watcher.

        Args:
            project_path: Root directory to watch.
            on_change: Callback invoked with list of changed file paths.
            ignore_patterns: fnmatch patterns for files to ignore.
            debounce_seconds: Minimum delay between change callbacks.
        """
        self.project_path = project_path
        self.on_change = on_change
        self.ignore_patterns = ignore_patterns or []
        self.debounce_seconds = debounce_seconds

        self._observer = None
        self._pending_changes: set[Path] = set()
        self._debounce_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._running = False

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
        self._running = True
        logger.info("File watcher started for: %s", self.project_path)

    def stop(self) -> None:
        """Stop watching for file changes."""
        self._running = False
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
        logger.info("File watcher stopped")

    def _file_changed(self, file_path: Path) -> None:
        """Handle a file change event with debouncing."""
        if not self._running:
            return

        # Check ignore patterns
        try:
            relative = file_path.relative_to(self.project_path)
        except ValueError:
            return

        from fnmatch import fnmatch

        rel_str = str(relative)
        for pattern in self.ignore_patterns:
            if fnmatch(rel_str, pattern) or fnmatch(file_path.name, pattern):
                return

        with self._lock:
            self._pending_changes.add(file_path)

            # Reset debounce timer
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()

            self._debounce_timer = threading.Timer(
                self.debounce_seconds, self._flush_changes
            )
            self._debounce_timer.start()

    def _flush_changes(self) -> None:
        """Flush pending changes to the callback."""
        with self._lock:
            if not self._pending_changes:
                return
            changes = list(self._pending_changes)
            self._pending_changes.clear()

        logger.info("Flushing %d file changes for re-indexing", len(changes))
        try:
            self.on_change(changes)
        except Exception as e:
            logger.error("Error in change callback: %s", e)

    @property
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running
