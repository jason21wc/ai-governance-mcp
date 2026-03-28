"""Multi-project index management for the Context Engine.

Manages project discovery, index lifecycle, and provides the query
interface used by the MCP server. Auto-detects working directory
to route queries to the correct project index.
"""

import logging
import re
import threading
import time
from datetime import datetime, timezone
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

# ─── Ranking signal constants ───

# File-type bonuses (additive, applied before clamping)
FILE_TYPE_BONUSES: dict[str, float] = {
    "source": 0.02,
    "test": -0.02,
    "other": 0.0,
}

# Recency thresholds (seconds) and bonuses
RECENCY_RECENT_DAYS = 7
RECENCY_STALE_DAYS = 90
RECENCY_RECENT_BONUS = 0.01
RECENCY_STALE_PENALTY = -0.01


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
        semantic_weight: float = 0.7,
        default_index_mode: IndexMode = "ondemand",
        readonly: bool = False,
    ) -> None:
        self.storage = storage or FilesystemStorage()
        self.embedding_model_name = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.semantic_weight = semantic_weight
        self.default_index_mode: IndexMode = default_index_mode
        self.readonly = readonly

        self._indexer = Indexer(
            storage=self.storage,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            readonly=readonly,
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
        # Generation counter per project — prevents stale watcher results from
        # overwriting fresh manual reindex results (race condition mitigation)
        self._index_generations: dict[str, int] = {}

    def get_or_create_index(
        self,
        project_path: Path,
        index_mode: IndexMode = "ondemand",
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
                if index_mode == "realtime":
                    self._ensure_watcher(project_path, project_id)
                return self._loaded_indexes[project_id]

            # Evict old projects before loading new one
            self._evict_if_needed()

            # Check if exists in storage
            if self.storage.project_exists(project_id):
                index = self._load_project(project_id)
                self._touch_project(project_id)
                if index_mode == "realtime":
                    self._ensure_watcher(project_path, project_id)
                return index

            # Create new index
            index = self._indexer.index_project(project_path, project_id, index_mode)
            self._loaded_indexes[project_id] = index

            # Load search indexes
            self._load_search_indexes(project_id)
            self._touch_project(project_id)

            # Start watcher if realtime mode
            if index_mode == "realtime":
                self._ensure_watcher(project_path, project_id)

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
                    # Start watcher if project was indexed as realtime (skip in readonly)
                    if not self.readonly:
                        metadata = self.storage.load_metadata(project_id)
                        stored_mode = (metadata or {}).get("index_mode", "ondemand")
                        if stored_mode == "realtime":
                            try:
                                self._ensure_watcher(project_path, project_id)
                            except Exception as e:
                                logger.warning(
                                    "Failed to start watcher for %s: %s",
                                    project_id,
                                    e,
                                )
                elif self.readonly:
                    # Read-only mode: can't auto-index missing projects
                    return ProjectQueryResult(
                        query=query,
                        project_id=project_id,
                        project_path=str(project_path),
                        results=[],
                        total_results=0,
                        readonly_message=(
                            "Project not indexed. Index from a writable environment "
                            "(e.g., Claude Code CLI) first, then queries will work here."
                        ),
                    )
                else:
                    self.get_or_create_index(
                        project_path, index_mode=self.default_index_mode
                    )

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

            # Build file recency map for ranking signals
            file_recency_map = self._build_file_recency_map(project_id)

            # Fuse scores with ranking signals
            results = self._fuse_scores(
                index.chunks,
                semantic_scores,
                keyword_scores,
                max_results,
                file_recency_map=file_recency_map,
                query_lower=query.lower(),
            )

        elapsed_ms = (time.time() - start_time) * 1000

        # Compute freshness metadata from loaded index
        last_indexed_at = None
        index_age_seconds = None
        if index is not None and index.updated_at:
            last_indexed_at = index.updated_at
            try:
                updated_dt = datetime.fromisoformat(index.updated_at)
                age = (datetime.now(timezone.utc) - updated_dt).total_seconds()
                index_age_seconds = round(max(age, 0.0), 2)
            except (ValueError, TypeError):
                pass

        return ProjectQueryResult(
            query=query,
            project_id=project_id,
            project_path=str(project_path),
            results=results,
            total_results=len(results),
            query_time_ms=round(elapsed_ms, 2),
            last_indexed_at=last_indexed_at,
            index_age_seconds=index_age_seconds,
        )

    def reindex_project(self, project_path: Path) -> ProjectIndex:
        """Force a full re-index of a project."""
        if self.readonly:
            raise RuntimeError(
                "Cannot reindex in read-only mode. "
                "Index from a writable environment first."
            )
        with self._index_lock:
            project_id = FilesystemStorage.project_id_from_path(project_path)

            # Stop existing watcher if any
            if project_id in self._watchers:
                self._watchers[project_id].stop()
                del self._watchers[project_id]

            # Increment generation — any in-flight watcher callbacks will
            # detect the mismatch and discard their stale results
            gen = self._index_generations.get(project_id, 0) + 1
            self._index_generations[project_id] = gen

            # Clear loaded data
            self._loaded_indexes.pop(project_id, None)
            self._loaded_embeddings.pop(project_id, None)
            self._loaded_bm25.pop(project_id, None)

            # Re-index — use default_index_mode (from env var) rather than only
            # stored metadata, so env var changes take effect on reindex
            index_mode = self.default_index_mode

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

        Returns: running, stopped, circuit_broken, disabled, or not_loaded
        """
        if index_mode == "ondemand":
            return "disabled"
        if project_id in self._circuit_broken:
            return "circuit_broken"
        if project_id in self._watchers and self._watchers[project_id].is_running:
            return "running"
        # Distinguish: project not loaded into memory yet vs watcher stopped
        if project_id not in self._loaded_indexes:
            return "not_loaded"
        return "stopped"

    def list_projects(self) -> list[ProjectStatus]:
        """List all indexed projects with their status."""
        statuses = []
        for project_id in self.storage.list_projects():
            try:
                metadata = self.storage.load_metadata(project_id)
                if metadata:
                    statuses.append(self._build_project_status(project_id, metadata))
            except (OSError, ValueError, KeyError) as e:
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

    def startup_watchers(self) -> int:
        """Start watchers for stored projects with index_mode='realtime'.

        Called at server boot to eagerly load realtime projects and start
        file watchers. Pre-warms the embedding model outside _index_lock
        to avoid blocking concurrent MCP queries during the expensive
        first model load.

        Returns number of watchers started. Returns 0 immediately in
        read-only mode (no watchers needed).
        """
        if self.readonly:
            return 0
        # Pre-warm embedding model outside _index_lock.
        # Lock ordering: _index_lock must always be acquired before _model_lock.
        # By warming the model here, get_or_create_index() won't trigger the
        # expensive lazy load while holding _index_lock.
        try:
            _ = self._indexer.embedding_model
        except Exception as e:
            logger.warning("Failed to pre-warm embedding model: %s", e)
            # Continue — projects with stored embeddings can still load

        started = 0
        for project_id in self.storage.list_projects():
            # Soft LRU check — get_or_create_index enforces the hard limit
            # under _index_lock via _evict_if_needed. Racing here is benign.
            if len(self._loaded_indexes) >= MAX_LOADED_PROJECTS:
                logger.info(
                    "LRU limit reached (%d), skipping remaining projects",
                    MAX_LOADED_PROJECTS,
                )
                break
            try:
                metadata = self.storage.load_metadata(project_id)
                if not metadata or metadata.get("index_mode") != "realtime":
                    continue
                raw_path = metadata.get("project_path", "")
                if not raw_path:
                    logger.warning(
                        "Skipping project %s: no project_path in metadata",
                        project_id,
                    )
                    continue
                project_path = Path(raw_path)
                if not project_path.is_dir():
                    logger.warning(
                        "Skipping project %s: path does not exist: %s",
                        project_id,
                        project_path,
                    )
                    continue
                # Clear circuit breaker on fresh boot — safe without lock here
                # because no watchers are running for this project yet (they
                # start inside get_or_create_index below).
                with self._index_lock:
                    self._circuit_broken.discard(project_id)
                    self._watcher_failures.pop(project_id, None)
                # Load index and start watcher
                self.get_or_create_index(project_path, index_mode="realtime")
                started += 1
            except Exception as e:
                logger.warning("Failed to start watcher for %s: %s", project_id, e)
        logger.info("Eager startup: %d watcher(s) started", started)
        return started

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

        index_mode = metadata.get("index_mode", "ondemand")
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
            chunking_version=metadata.get("chunking_version", "unknown"),
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

        Loads metadata (lightweight) and chunks (separate file) independently.
        Handles backward compat: if metadata still contains chunks (old format),
        uses them as fallback when chunks.json doesn't exist.

        If metadata is corrupt (fails Pydantic validation), logs a warning
        and returns a minimal empty index so the caller can trigger re-indexing.
        """
        metadata = self.storage.load_metadata(project_id)
        if metadata is None:
            raise ValueError(f"Project {project_id} not found in storage")

        # Load chunks from dedicated file (new format)
        chunks_data = self.storage.load_chunks(project_id)
        if chunks_data is not None:
            metadata["chunks"] = chunks_data
        # else: metadata may still contain chunks from old format — use as-is

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
        """Load embeddings and BM25 index for a project.

        Respects embedding model mismatch: if _load_project discarded
        embeddings due to model mismatch, this method will not reload them.
        Also validates embeddings/chunks length consistency.
        """
        # Skip embedding reload if they were discarded due to model mismatch
        if project_id not in self._loaded_embeddings:
            embeddings = self.storage.load_embeddings(project_id)
            if embeddings is not None:
                # A1 FIX: Validate embeddings/chunks length consistency
                index = self._loaded_indexes.get(project_id)
                if index and len(embeddings) != len(index.chunks):
                    logger.warning(
                        "Embeddings/chunks length mismatch for %s "
                        "(%d embeddings vs %d chunks). Discarding embeddings.",
                        project_id,
                        len(embeddings),
                        len(index.chunks),
                    )
                else:
                    self._loaded_embeddings[project_id] = embeddings

        bm25_data = self.storage.load_bm25_index(project_id)
        if bm25_data and bm25_data.get("tokenized_corpus"):
            bm25 = _build_bm25(bm25_data["tokenized_corpus"])
            if bm25 is not None:
                self._loaded_bm25[project_id] = bm25

    def _semantic_search(self, query: str, project_id: str) -> np.ndarray:
        """Perform semantic search, returning per-chunk scores.

        Falls back to empty results (BM25-only) if the embedding model
        fails to load, preventing a single model failure from breaking
        all queries.
        """
        embeddings = self._loaded_embeddings.get(project_id)
        if embeddings is None or len(embeddings) == 0:
            return np.array([])

        try:
            query_embedding = self._indexer.embedding_model.encode(
                [query], normalize_embeddings=True
            )
        except Exception as e:
            logger.warning(
                "Embedding model failed for query, falling back to BM25-only: %s", e
            )
            return np.array([])

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

        # Normalize to [0, 1]. BM25 IDF can produce negative scores for
        # very common terms in small corpora — clip after normalization.
        max_score = scores.max() if len(scores) > 0 else 0.0
        if max_score > 0:
            scores = scores / max_score
        scores = np.clip(scores, 0.0, 1.0)
        return scores

    @staticmethod
    def _classify_file_type(source_path: str) -> str:
        """Classify a chunk's source file as 'source', 'test', or 'other'."""
        parts = source_path.replace("\\", "/").split("/")
        basename = parts[-1] if parts else ""

        # Test file detection
        if basename.startswith("test_") or basename.endswith("_test.py"):
            return "test"
        # Go/Rust test convention
        if basename.endswith("_test.go") or basename.endswith("_test.rs"):
            return "test"
        # JS/TS test conventions
        for suffix in (
            ".test.js",
            ".test.ts",
            ".test.jsx",
            ".test.tsx",
            ".spec.js",
            ".spec.ts",
            ".spec.jsx",
            ".spec.tsx",
        ):
            if basename.endswith(suffix):
                return "test"
        if any(p == "tests" or p == "test" or p == "__tests__" for p in parts):
            return "test"

        # Source code detection by extension
        code_exts = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".rb",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".swift",
            ".kt",
            ".scala",
        }
        for ext in code_exts:
            if basename.endswith(ext):
                return "source"

        return "other"

    @staticmethod
    def _compute_recency_bonus(
        source_path: str, file_recency_map: dict[str, float] | None
    ) -> float:
        """Compute recency bonus for a chunk based on file modification time.

        Args:
            source_path: Relative path from the chunk.
            file_recency_map: {relative_path: last_modified_timestamp} or None.

        Returns:
            Bonus: +0.01 for recent, -0.01 for stale, 0.0 otherwise.
        """
        if file_recency_map is None:
            return 0.0

        last_mod = file_recency_map.get(source_path)
        if last_mod is None:
            return 0.0

        age_seconds = time.time() - last_mod
        age_days = age_seconds / 86400

        if age_days <= RECENCY_RECENT_DAYS:
            return RECENCY_RECENT_BONUS
        elif age_days > RECENCY_STALE_DAYS:
            return RECENCY_STALE_PENALTY
        return 0.0

    def _build_file_recency_map(self, project_id: str) -> dict[str, float] | None:
        """Build {relative_path: last_modified} map from loaded index.

        FileMetadata.path is absolute; ContentChunk.source_path is relative.
        Strips project root to create the mapping.
        """
        index = self._loaded_indexes.get(project_id)
        if index is None or not index.files:
            return None

        project_root = index.project_path
        recency_map: dict[str, float] = {}
        for fm in index.files:
            # Convert absolute path to relative
            abs_path = fm.path
            if abs_path.startswith(project_root):
                rel = abs_path[len(project_root) :].lstrip("/").lstrip("\\")
            else:
                rel = abs_path
            recency_map[rel] = fm.last_modified

        return recency_map

    @staticmethod
    def _deduplicate_per_file(results: list[QueryResult]) -> list[QueryResult]:
        """Keep only the highest-scoring chunk per source file."""
        seen_files: set[str] = set()
        deduped: list[QueryResult] = []
        for r in results:
            path = r.chunk.source_path
            if path not in seen_files:
                seen_files.add(path)
                deduped.append(r)
        return deduped

    @staticmethod
    def _compute_metadata_bonus(chunk: ContentChunk, query_lower: str) -> float:
        """Compute score bonus based on YAML frontmatter metadata.

        Boosts chunks whose metadata tags match query terms.
        Penalizes deprecated/archived entries. Boosts evergreen entries.
        Per QAM research (Amazon/SIGIR 2025): metadata-enhanced retrieval
        improves mAP@5 by +29% over BM25.
        """
        if not chunk.frontmatter:
            return 0.0

        bonus = 0.0
        fm = chunk.frontmatter

        # Tag matching: boost if query terms appear in tags
        tags = fm.get("tags", [])
        if isinstance(tags, list):
            tag_str = " ".join(str(t).lower() for t in tags)
            query_words = query_lower.split()
            matches = sum(1 for w in query_words if w in tag_str)
            if matches > 0:
                bonus += min(0.05, matches * 0.02)  # Cap at +0.05

        # Status penalty for deprecated/archived
        status = str(fm.get("status", "")).lower()
        if status in ("deprecated", "archived"):
            bonus -= 0.05
        elif status == "caution":
            bonus -= 0.02

        # Maturity boost for proven entries
        maturity = str(fm.get("maturity", "")).lower()
        if maturity == "evergreen":
            bonus += 0.03
        elif maturity == "seedling":
            bonus -= 0.01

        return bonus

    def _fuse_scores(
        self,
        chunks: list[ContentChunk],
        semantic_scores: np.ndarray,
        keyword_scores: np.ndarray,
        max_results: int,
        file_recency_map: dict[str, float] | None = None,
        query_lower: str = "",
    ) -> list[QueryResult]:
        """Fuse semantic and keyword scores with ranking bonuses and return top results."""
        if len(chunks) == 0:
            return []

        n = len(chunks)
        sem = semantic_scores if len(semantic_scores) == n else np.zeros(n)
        kw = keyword_scores if len(keyword_scores) == n else np.zeros(n)

        # Compute per-chunk bonuses
        bonuses = np.zeros(n)
        for i, chunk in enumerate(chunks):
            file_type = self._classify_file_type(chunk.source_path)
            bonuses[i] = FILE_TYPE_BONUSES.get(file_type, 0.0)
            bonuses[i] += self._compute_recency_bonus(
                chunk.source_path, file_recency_map
            )
            # Metadata boosting for frontmatter-enriched chunks (Reference Library, etc.)
            bonuses[i] += self._compute_metadata_bonus(chunk, query_lower)

        combined = (
            self.semantic_weight * sem + (1 - self.semantic_weight) * kw + bonuses
        )
        combined = np.clip(combined, 0.0, 1.0)

        # Fetch all non-zero candidates; dedup will reduce to max_results
        top_indices = np.argsort(combined)[::-1]

        results = []
        for idx in top_indices:
            if combined[idx] <= 0:
                break
            results.append(
                QueryResult(
                    chunk=chunks[idx],
                    semantic_score=float(min(sem[idx], 1.0)),
                    keyword_score=float(min(kw[idx], 1.0)),
                    combined_score=float(combined[idx]),
                    boost_score=float(np.clip(bonuses[idx], -0.05, 0.05)),
                )
            )

        # Per-file deduplication
        results = self._deduplicate_per_file(results)

        return results[:max_results]

    def _start_watcher(self, project_path: Path, project_id: str) -> None:
        """Start a file watcher for a project."""
        if project_id in self._watchers:
            return

        def on_change(changed_files: list[Path]) -> None:
            # Perform expensive I/O work OUTSIDE the lock so queries aren't blocked.
            # Only acquire the lock briefly to swap in-memory data structures.
            try:
                # Snapshot generation before expensive work — if a manual reindex
                # runs concurrently, it increments the generation and we'll detect
                # the mismatch before committing stale results.
                with self._index_lock:
                    gen = self._index_generations.get(project_id, 0)

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
                    # Check generation — discard if a manual reindex ran while
                    # we were doing expensive work outside the lock
                    if self._index_generations.get(project_id, 0) != gen:
                        logger.info(
                            "Discarding stale watcher result for %s "
                            "(generation changed during re-index)",
                            project_id,
                        )
                        return

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

    def _ensure_watcher(self, project_path: Path, project_id: str) -> None:
        """Ensure a file watcher is running for a realtime project.

        Idempotent: no-op if watcher already running. Restarts stale
        watchers (in dict but not running). Respects circuit breaker.
        Must be called under _index_lock.
        """
        if project_id in self._circuit_broken:
            return
        existing = self._watchers.get(project_id)
        if existing is not None and existing.is_running:
            return
        # Remove stale entry (stopped but still in dict)
        if existing is not None:
            logger.warning(
                "Detected stale watcher for %s (in dict but not running), restarting",
                project_id,
            )
            existing.stop()  # Ensure clean shutdown before restart
            self._watchers.pop(project_id, None)
        self._start_watcher(project_path, project_id)
