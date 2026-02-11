"""Multi-project index management for the Context Engine.

Manages project discovery, index lifecycle, and provides the query
interface used by the MCP server. Auto-detects working directory
to route queries to the correct project index.
"""

import logging
import re
import threading
import time
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi

from .indexer import Indexer
from .models import (
    ContentChunk,
    IndexMode,
    ProjectIndex,
    ProjectQueryResult,
    ProjectStatus,
    QueryResult,
)
from .storage.base import BaseStorage
from .storage.filesystem import FilesystemStorage
from .watcher import FileWatcher

logger = logging.getLogger("ai_governance_mcp.context_engine.project_manager")


# Maximum number of projects kept in memory simultaneously.
# Older projects are evicted (watchers stopped, data unloaded) when limit is hit.
MAX_LOADED_PROJECTS = 10


def _build_bm25(corpus: list[list[str]]) -> BM25Okapi | None:
    """Build a BM25 index from a tokenized corpus, with empty-corpus guard.

    BM25Okapi raises ZeroDivisionError on empty or all-empty-document corpus.
    Returns None if the corpus is unusable.
    """
    if corpus and any(len(doc) > 0 for doc in corpus):
        return BM25Okapi(corpus)
    return None


class ProjectManager:
    """Manages multiple project indexes and provides query interface.

    Core responsibilities:
    - Auto-detect and register projects by working directory
    - Manage index lifecycle (create, update, delete)
    - Route queries to the correct project index
    - Provide hybrid search (semantic + BM25)
    - LRU eviction of loaded projects when MAX_LOADED_PROJECTS exceeded
    """

    def __init__(
        self,
        storage: BaseStorage | None = None,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        embedding_dimensions: int = 384,
        semantic_weight: float = 0.6,
    ) -> None:
        self.storage = storage or FilesystemStorage()
        self.embedding_model_name = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.semantic_weight = semantic_weight

        self._indexer = Indexer(
            storage=self.storage,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
        )
        self._watchers: dict[str, FileWatcher] = {}
        self._loaded_indexes: dict[str, ProjectIndex] = {}
        self._loaded_embeddings: dict[str, np.ndarray] = {}
        self._loaded_bm25: dict[str, BM25Okapi] = {}

        # LRU tracking: list of project_ids ordered by last access (most recent last)
        self._access_order: list[str] = []

        # RLock protects shared index state from watcher callback mutations.
        # Reentrant because query_project may call get_or_create_index internally.
        self._index_lock = threading.RLock()

        # Track consecutive watcher failures per project for circuit breaker
        self._watcher_failures: dict[str, int] = {}
        # Track projects with circuit-broken watchers (for status reporting)
        self._circuit_broken: set[str] = set()

    def get_or_create_index(
        self,
        project_path: Path,
        index_mode: IndexMode = "realtime",
    ) -> ProjectIndex:
        """Get existing index or create a new one for a project.

        Args:
            project_path: Root directory of the project.
            index_mode: 'realtime' or 'ondemand'.

        Returns:
            ProjectIndex for the project.
        """
        with self._index_lock:
            project_id = FilesystemStorage.project_id_from_path(project_path)

            # Check if already loaded in memory
            if project_id in self._loaded_indexes:
                self._touch_project(project_id)
                return self._loaded_indexes[project_id]

            # Evict old projects before loading new one
            self._evict_if_needed()

            # Check if exists in storage
            if self.storage.project_exists(project_id):
                index = self._load_project(project_id)
                self._touch_project(project_id)
                return index

            # Create new index
            index = self._indexer.index_project(project_path, project_id, index_mode)
            self._loaded_indexes[project_id] = index

            # Load search indexes
            self._load_search_indexes(project_id)
            self._touch_project(project_id)

            # Start watcher if realtime mode
            if index_mode == "realtime":
                self._start_watcher(project_path, project_id)

            return index

    def query_project(
        self,
        query: str,
        project_path: Path | None = None,
        max_results: int = 10,
    ) -> ProjectQueryResult:
        """Query a project's content using hybrid search.

        Args:
            query: Natural language query or keyword search.
            project_path: Project to query. Defaults to current working directory.
            max_results: Maximum number of results to return.

        Returns:
            Ranked query results with content chunks and scores.
        """
        start_time = time.time()

        if project_path is None:
            project_path = Path.cwd()

        project_id = FilesystemStorage.project_id_from_path(project_path)

        # Acquire lock to prevent watcher mutations during read phase.
        # RLock allows re-entry if get_or_create_index calls _load_search_indexes.
        with self._index_lock:
            # Ensure project is indexed
            if project_id not in self._loaded_indexes:
                if self.storage.project_exists(project_id):
                    self._load_project(project_id)
                else:
                    self.get_or_create_index(project_path)

            self._touch_project(project_id)
            index = self._loaded_indexes.get(project_id)
            if index is None or not index.chunks:
                return ProjectQueryResult(
                    query=query,
                    project_id=project_id,
                    project_path=str(project_path),
                    results=[],
                    total_results=0,
                )

            # Semantic search
            semantic_scores = self._semantic_search(query, project_id)

            # BM25 keyword search
            keyword_scores = self._bm25_search(query, project_id)

            # Fuse scores
            results = self._fuse_scores(
                index.chunks, semantic_scores, keyword_scores, max_results
            )

        elapsed_ms = (time.time() - start_time) * 1000

        return ProjectQueryResult(
            query=query,
            project_id=project_id,
            project_path=str(project_path),
            results=results,
            total_results=len(results),
            query_time_ms=round(elapsed_ms, 2),
        )

    def reindex_project(self, project_path: Path) -> ProjectIndex:
        """Force a full re-index of a project."""
        with self._index_lock:
            project_id = FilesystemStorage.project_id_from_path(project_path)

            # Stop existing watcher if any
            if project_id in self._watchers:
                self._watchers[project_id].stop()
                del self._watchers[project_id]

            # Clear loaded data
            self._loaded_indexes.pop(project_id, None)
            self._loaded_embeddings.pop(project_id, None)
            self._loaded_bm25.pop(project_id, None)

            # Re-index
            existing = self.storage.load_metadata(project_id)
            index_mode = (
                existing.get("index_mode", "realtime") if existing else "realtime"
            )

            index = self._indexer.index_project(project_path, project_id, index_mode)
            self._loaded_indexes[project_id] = index
            self._load_search_indexes(project_id)
            self._touch_project(project_id)

            # Clear circuit breaker and failure history on successful re-index
            self._circuit_broken.discard(project_id)
            self._watcher_failures.pop(project_id, None)

            if index_mode == "realtime":
                self._start_watcher(project_path, project_id)

            return index

    def _get_watcher_status(self, project_id: str, index_mode: IndexMode) -> str:
        """Get watcher status for a project.

        Returns: running, stopped, circuit_broken, or disabled
        """
        if index_mode == "ondemand":
            return "disabled"
        if project_id in self._circuit_broken:
            return "circuit_broken"
        if project_id in self._watchers and self._watchers[project_id].is_running:
            return "running"
        return "stopped"

    def list_projects(self) -> list[ProjectStatus]:
        """List all indexed projects with their status."""
        statuses = []
        for project_id in self.storage.list_projects():
            try:
                metadata = self.storage.load_metadata(project_id)
                if metadata:
                    statuses.append(self._build_project_status(project_id, metadata))
            except Exception as e:
                logger.warning("Error loading project %s: %s", project_id, e)
                continue
        return statuses

    def get_project_status(
        self, project_path: Path | None = None
    ) -> ProjectStatus | None:
        """Get status of a specific project."""
        if project_path is None:
            project_path = Path.cwd()

        project_id = FilesystemStorage.project_id_from_path(project_path)
        metadata = self.storage.load_metadata(project_id)
        if metadata is None:
            return None

        return self._build_project_status(project_id, metadata, project_path)

    def shutdown(self) -> None:
        """Stop all watchers and clean up resources."""
        with self._index_lock:
            watchers = list(self._watchers.values())
            self._watchers.clear()
        for watcher in watchers:
            watcher.stop()
        logger.info("Project manager shut down")

    # ─── Private methods ───

    def _build_project_status(
        self,
        project_id: str,
        metadata: dict,
        project_path: Path | None = None,
    ) -> ProjectStatus:
        """Build a ProjectStatus from metadata with error-safe index size."""
        index_path = self.storage.get_index_path(project_id)
        index_size = 0
        if index_path.exists():
            try:
                index_size = sum(
                    f.stat().st_size
                    for f in index_path.iterdir()
                    if f.is_file() and not f.is_symlink()
                )
            except OSError as e:
                logger.warning("Error computing index size for %s: %s", project_id, e)

        index_mode = metadata.get("index_mode", "realtime")
        with self._index_lock:
            watcher_status = self._get_watcher_status(project_id, index_mode)

        return ProjectStatus(
            project_id=project_id,
            project_path=metadata.get("project_path", str(project_path or "unknown")),
            total_files=metadata.get("total_files", 0),
            total_chunks=metadata.get("total_chunks", 0),
            index_mode=index_mode,
            last_updated=metadata.get("updated_at"),
            index_size_bytes=index_size,
            embedding_model=metadata.get("embedding_model", "unknown"),
            watcher_status=watcher_status,
        )

    def _touch_project(self, project_id: str) -> None:
        """Mark a project as recently accessed for LRU eviction.

        Must be called with _index_lock held.
        """
        if project_id in self._access_order:
            self._access_order.remove(project_id)
        self._access_order.append(project_id)

    def _evict_if_needed(self) -> None:
        """Evict least-recently-used projects if at/over MAX_LOADED_PROJECTS.

        Called before loading a new project, so >= ensures the new project
        plus existing ones never exceed MAX_LOADED_PROJECTS.
        Must be called with _index_lock held.
        """
        while len(self._loaded_indexes) >= MAX_LOADED_PROJECTS and self._access_order:
            evict_id = self._access_order.pop(0)
            if evict_id not in self._loaded_indexes:
                continue
            # Stop watcher for evicted project
            watcher = self._watchers.pop(evict_id, None)
            if watcher is not None:
                watcher.stop()
            # Unload from memory
            self._loaded_indexes.pop(evict_id, None)
            self._loaded_embeddings.pop(evict_id, None)
            self._loaded_bm25.pop(evict_id, None)
            logger.info("Evicted project %s from memory (LRU)", evict_id)

    def _load_project(self, project_id: str) -> ProjectIndex:
        """Load a project index from storage.

        If metadata is corrupt (fails Pydantic validation), logs a warning
        and returns a minimal empty index so the caller can trigger re-indexing.
        """
        metadata = self.storage.load_metadata(project_id)
        if metadata is None:
            raise ValueError(f"Project {project_id} not found in storage")

        try:
            index = ProjectIndex(**metadata)
        except Exception as e:
            logger.warning(
                "Corrupt metadata for project %s, creating empty index: %s",
                project_id,
                e,
            )
            index = ProjectIndex(
                project_id=project_id,
                project_path=metadata.get("project_path", "unknown"),
                created_at=metadata.get("created_at", "unknown"),
                updated_at=metadata.get("updated_at", "unknown"),
                embedding_model=metadata.get("embedding_model", "unknown"),
            )
        # Warn if stored embedding model differs from configured model.
        # Mismatched embeddings produce garbage similarity scores — disable
        # semantic search and fall back to BM25-only until re-indexed.
        stored_model = index.embedding_model
        if stored_model and stored_model != self.embedding_model_name:
            logger.warning(
                "Project %s was indexed with model '%s' but server is configured "
                "for '%s'. Semantic search disabled — using BM25-only. Re-index to fix.",
                project_id,
                stored_model,
                self.embedding_model_name,
            )
            # Discard incompatible embeddings so _semantic_search returns empty
            self._loaded_embeddings.pop(project_id, None)

        self._loaded_indexes[project_id] = index
        self._load_search_indexes(project_id)
        return index

    def _load_search_indexes(self, project_id: str) -> None:
        """Load embeddings and BM25 index for a project."""
        embeddings = self.storage.load_embeddings(project_id)
        if embeddings is not None:
            self._loaded_embeddings[project_id] = embeddings

        bm25_data = self.storage.load_bm25_index(project_id)
        if bm25_data and bm25_data.get("tokenized_corpus"):
            bm25 = _build_bm25(bm25_data["tokenized_corpus"])
            if bm25 is not None:
                self._loaded_bm25[project_id] = bm25

    def _semantic_search(self, query: str, project_id: str) -> np.ndarray:
        """Perform semantic search, returning per-chunk scores."""
        embeddings = self._loaded_embeddings.get(project_id)
        if embeddings is None or len(embeddings) == 0:
            return np.array([])

        query_embedding = self._indexer.embedding_model.encode(
            [query], normalize_embeddings=True
        )
        scores = np.dot(embeddings, query_embedding.T).flatten()
        # Clip to [0, 1]
        scores = np.clip(scores, 0.0, 1.0)
        return scores

    def _bm25_search(self, query: str, project_id: str) -> np.ndarray:
        """Perform BM25 keyword search, returning per-chunk scores."""
        bm25 = self._loaded_bm25.get(project_id)
        if bm25 is None:
            return np.array([])

        tokenized_query = re.findall(r"\w+", query.lower())
        scores = bm25.get_scores(tokenized_query)

        # Normalize to [0, 1]
        max_score = scores.max() if len(scores) > 0 else 0.0
        if max_score > 0:
            scores = scores / max_score
        return scores

    def _fuse_scores(
        self,
        chunks: list[ContentChunk],
        semantic_scores: np.ndarray,
        keyword_scores: np.ndarray,
        max_results: int,
    ) -> list[QueryResult]:
        """Fuse semantic and keyword scores and return top results."""
        if len(chunks) == 0:
            return []

        n = len(chunks)
        sem = semantic_scores if len(semantic_scores) == n else np.zeros(n)
        kw = keyword_scores if len(keyword_scores) == n else np.zeros(n)

        combined = self.semantic_weight * sem + (1 - self.semantic_weight) * kw

        # Get top results
        top_indices = np.argsort(combined)[::-1][:max_results]

        results = []
        for idx in top_indices:
            if combined[idx] <= 0:
                break
            results.append(
                QueryResult(
                    chunk=chunks[idx],
                    semantic_score=float(min(sem[idx], 1.0)),
                    keyword_score=float(min(kw[idx], 1.0)),
                    combined_score=float(min(combined[idx], 1.0)),
                )
            )

        return results

    def _start_watcher(self, project_path: Path, project_id: str) -> None:
        """Start a file watcher for a project."""
        if project_id in self._watchers:
            return

        def on_change(changed_files: list[Path]) -> None:
            # Perform expensive I/O work OUTSIDE the lock so queries aren't blocked.
            # Only acquire the lock briefly to swap in-memory data structures.
            try:
                new_index = self._indexer.incremental_update(
                    project_path, project_id, changed_files
                )
                # Load search data from storage (disk I/O, still outside lock)
                new_embeddings = self.storage.load_embeddings(project_id)
                new_bm25_data = self.storage.load_bm25_index(project_id)
                new_bm25 = _build_bm25(
                    new_bm25_data["tokenized_corpus"]
                    if new_bm25_data and new_bm25_data.get("tokenized_corpus")
                    else []
                )

                # Brief lock: swap in-memory structures atomically
                with self._index_lock:
                    self._loaded_indexes[project_id] = new_index
                    if new_embeddings is not None:
                        self._loaded_embeddings[project_id] = new_embeddings
                    else:
                        # Discard stale embeddings — array length won't match new chunks
                        self._loaded_embeddings.pop(project_id, None)
                    if new_bm25 is not None:
                        self._loaded_bm25[project_id] = new_bm25
                    else:
                        self._loaded_bm25.pop(project_id, None)
                    self._watcher_failures.pop(project_id, None)

            except Exception as e:
                watcher_to_stop = None
                with self._index_lock:
                    failures = self._watcher_failures.get(project_id, 0) + 1
                    self._watcher_failures[project_id] = failures
                    if failures >= 3:
                        watcher_to_stop = self._watchers.pop(project_id, None)
                        self._circuit_broken.add(project_id)
                logger.error(
                    "Incremental update failed (%d consecutive): %s", failures, e
                )
                if watcher_to_stop is not None:
                    logger.error(
                        "Stopping watcher for %s after %d consecutive failures",
                        project_id,
                        failures,
                    )
                    watcher_to_stop.stop()

        ignore_spec = self._indexer.load_ignore_patterns(project_path)
        watcher = FileWatcher(
            project_path=project_path,
            on_change=on_change,
            ignore_spec=ignore_spec,
        )
        watcher.start()
        self._watchers[project_id] = watcher
