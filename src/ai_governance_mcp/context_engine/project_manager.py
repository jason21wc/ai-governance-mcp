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
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi

from .indexer import Indexer
from .models import (
    ContentChunk,
    ProjectIndex,
    ProjectQueryResult,
    ProjectStatus,
    QueryResult,
)
from .storage.base import BaseStorage
from .storage.filesystem import FilesystemStorage
from .watcher import FileWatcher

logger = logging.getLogger("ai_governance_mcp.context_engine.project_manager")


class ProjectManager:
    """Manages multiple project indexes and provides query interface.

    Core responsibilities:
    - Auto-detect and register projects by working directory
    - Manage index lifecycle (create, update, delete)
    - Route queries to the correct project index
    - Provide hybrid search (semantic + BM25)
    """

    def __init__(
        self,
        storage: Optional[BaseStorage] = None,
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

        # RLock protects shared index state from watcher callback mutations.
        # Reentrant because query_project may call get_or_create_index internally.
        self._index_lock = threading.RLock()

    def get_or_create_index(
        self,
        project_path: Path,
        index_mode: str = "realtime",
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
                return self._loaded_indexes[project_id]

            # Check if exists in storage
            if self.storage.project_exists(project_id):
                return self._load_project(project_id)

            # Create new index
            index = self._indexer.index_project(project_path, project_id, index_mode)
            self._loaded_indexes[project_id] = index

            # Load search indexes
            self._load_search_indexes(project_id)

            # Start watcher if realtime mode
            if index_mode == "realtime":
                self._start_watcher(project_path, project_id)

            return index

    def query_project(
        self,
        query: str,
        project_path: Optional[Path] = None,
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

            if index_mode == "realtime":
                self._start_watcher(project_path, project_id)

            return index

    def list_projects(self) -> list[ProjectStatus]:
        """List all indexed projects with their status."""
        statuses = []
        for project_id in self.storage.list_projects():
            metadata = self.storage.load_metadata(project_id)
            if metadata:
                index_path = self.storage.get_index_path(project_id)
                index_size = (
                    sum(f.stat().st_size for f in index_path.iterdir() if f.is_file())
                    if index_path.exists()
                    else 0
                )

                statuses.append(
                    ProjectStatus(
                        project_id=project_id,
                        project_path=metadata.get("project_path", "unknown"),
                        total_files=metadata.get("total_files", 0),
                        total_chunks=metadata.get("total_chunks", 0),
                        index_mode=metadata.get("index_mode", "realtime"),
                        last_updated=metadata.get("updated_at"),
                        index_size_bytes=index_size,
                        embedding_model=metadata.get("embedding_model", "unknown"),
                    )
                )
        return statuses

    def get_project_status(
        self, project_path: Optional[Path] = None
    ) -> Optional[ProjectStatus]:
        """Get status of a specific project."""
        if project_path is None:
            project_path = Path.cwd()

        project_id = FilesystemStorage.project_id_from_path(project_path)
        metadata = self.storage.load_metadata(project_id)
        if metadata is None:
            return None

        index_path = self.storage.get_index_path(project_id)
        index_size = (
            sum(f.stat().st_size for f in index_path.iterdir() if f.is_file())
            if index_path.exists()
            else 0
        )

        return ProjectStatus(
            project_id=project_id,
            project_path=metadata.get("project_path", str(project_path)),
            total_files=metadata.get("total_files", 0),
            total_chunks=metadata.get("total_chunks", 0),
            index_mode=metadata.get("index_mode", "realtime"),
            last_updated=metadata.get("updated_at"),
            index_size_bytes=index_size,
            embedding_model=metadata.get("embedding_model", "unknown"),
        )

    def shutdown(self) -> None:
        """Stop all watchers and clean up resources."""
        for project_id, watcher in self._watchers.items():
            watcher.stop()
        self._watchers.clear()
        logger.info("Project manager shut down")

    # ─── Private methods ───

    def _load_project(self, project_id: str) -> ProjectIndex:
        """Load a project index from storage."""
        metadata = self.storage.load_metadata(project_id)
        if metadata is None:
            raise ValueError(f"Project {project_id} not found in storage")

        index = ProjectIndex(**metadata)
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
            self._loaded_bm25[project_id] = BM25Okapi(bm25_data["tokenized_corpus"])

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
        max_score = scores.max() if len(scores) > 0 and scores.max() > 0 else 1.0
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
            try:
                with self._index_lock:
                    self._indexer.incremental_update(
                        project_path, project_id, changed_files
                    )
                    # Reload search indexes
                    self._load_search_indexes(project_id)
                    # Reload metadata
                    metadata = self.storage.load_metadata(project_id)
                    if metadata:
                        self._loaded_indexes[project_id] = ProjectIndex(**metadata)
            except Exception as e:
                logger.error("Error during incremental update: %s", e)

        watcher = FileWatcher(
            project_path=project_path,
            on_change=on_change,
        )
        watcher.start()
        self._watchers[project_id] = watcher
