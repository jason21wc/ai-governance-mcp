"""Core indexing orchestrator for the Context Engine.

Coordinates source connectors to parse project files into content chunks,
generates embeddings, and builds the hybrid search index (BM25 + semantic).
"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

import numpy as np

from .connectors.base import BaseConnector
from .connectors.code import CodeConnector
from .connectors.document import DocumentConnector
from .connectors.image import ImageConnector
from .connectors.pdf import PDFConnector
from .connectors.spreadsheet import SpreadsheetConnector
from .models import ContentChunk, FileMetadata, ProjectIndex
from .storage.base import BaseStorage

logger = logging.getLogger("ai_governance_mcp.context_engine.indexer")


# Maximum file size to index (10MB) — prevents memory exhaustion on large binaries
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Maximum number of files to index per project — prevents memory exhaustion
MAX_FILE_COUNT = 10_000

# Maximum content length for embedding input (chars)
# BGE-small handles ~512 tokens (~2048 chars); larger models can handle more
MAX_EMBEDDING_INPUT_CHARS = 2048

# Default ignore patterns when no .contextignore exists
DEFAULT_IGNORE_PATTERNS = [
    ".git/",
    ".git/**",
    "__pycache__/",
    "__pycache__/**",
    "*.pyc",
    "node_modules/",
    "node_modules/**",
    ".venv/",
    ".venv/**",
    "venv/",
    "venv/**",
    ".env*",
    "*.egg-info/",
    "*.egg-info/**",
    "dist/",
    "dist/**",
    "build/",
    "build/**",
    ".DS_Store",
    "*.lock",
]


class Indexer:
    """Core indexing orchestrator.

    Manages the full indexing pipeline:
    1. Discover files (respecting .contextignore)
    2. Route files to appropriate connectors
    3. Parse files into content chunks
    4. Generate embeddings for semantic search
    5. Build BM25 index for keyword search
    6. Persist to storage backend
    """

    def __init__(
        self,
        storage: BaseStorage,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        embedding_dimensions: int = 384,
    ) -> None:
        self.storage = storage
        self.embedding_model_name = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self._embedding_model = None

        # Initialize connectors in priority order
        self.connectors: list[BaseConnector] = [
            CodeConnector(),
            DocumentConnector(),
            PDFConnector(),
            SpreadsheetConnector(),
            ImageConnector(),
        ]

    @property
    def embedding_model(self):
        """Lazy-load the embedding model."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer

            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    def index_project(
        self,
        project_path: Path,
        project_id: str,
        index_mode: str = "realtime",
    ) -> ProjectIndex:
        """Index an entire project.

        Args:
            project_path: Root directory of the project.
            project_id: Unique identifier for this project.
            index_mode: 'realtime' or 'ondemand'.

        Returns:
            Complete ProjectIndex with all chunks and metadata.
        """
        logger.info("Indexing project: %s (id: %s)", project_path, project_id)

        # Load ignore patterns
        ignore_patterns = self._load_ignore_patterns(project_path)

        # Discover files
        files = self._discover_files(project_path, ignore_patterns)
        logger.info("Discovered %d files to index", len(files))

        # Parse files into chunks
        all_chunks: list[ContentChunk] = []
        all_metadata: list[FileMetadata] = []

        for file_path in files:
            connector = self._get_connector(file_path)
            if connector is None:
                continue

            try:
                chunks = connector.parse(file_path)
                metadata = connector.extract_metadata(file_path)

                # Compute content hash for change detection
                content_hash = self._file_hash(file_path)
                metadata.content_hash = content_hash
                metadata.chunk_count = len(chunks)

                all_chunks.extend(chunks)
                all_metadata.append(metadata)
            except Exception as e:
                logger.warning("Failed to parse %s: %s", file_path, e)
                continue

        logger.info(
            "Extracted %d chunks from %d files", len(all_chunks), len(all_metadata)
        )

        # Assign embedding IDs
        for i, chunk in enumerate(all_chunks):
            chunk.embedding_id = i

        # Generate embeddings
        embeddings = self._generate_embeddings(all_chunks)

        # Build BM25 index
        bm25_data = self._build_bm25_index(all_chunks)

        # Create project index
        now = datetime.now(timezone.utc).isoformat()
        project_index = ProjectIndex(
            project_id=project_id,
            project_path=str(project_path),
            chunks=all_chunks,
            files=all_metadata,
            created_at=now,
            updated_at=now,
            embedding_model=self.embedding_model_name,
            total_chunks=len(all_chunks),
            total_files=len(all_metadata),
            index_mode=index_mode,
        )

        # Persist to storage
        self.storage.save_embeddings(project_id, embeddings)
        self.storage.save_bm25_index(project_id, bm25_data)
        self.storage.save_metadata(project_id, project_index.model_dump())
        self.storage.save_file_manifest(
            project_id,
            {fm.path: fm.model_dump() for fm in all_metadata},
        )

        logger.info(
            "Project indexed successfully: %d chunks, %d files",
            len(all_chunks),
            len(all_metadata),
        )
        return project_index

    def incremental_update(
        self,
        project_path: Path,
        project_id: str,
        changed_files: list[Path],
    ) -> Optional[ProjectIndex]:
        """Incrementally update the index for changed files.

        Args:
            project_path: Root directory of the project.
            project_id: Unique identifier for this project.
            changed_files: List of files that changed.

        Returns:
            Updated ProjectIndex, or None if full re-index is needed.
        """
        # Load existing index
        existing = self.storage.load_metadata(project_id)
        if existing is None:
            logger.info("No existing index found, performing full index")
            return self.index_project(project_path, project_id)

        # For now, perform full re-index on any change
        # TODO: Implement true incremental update (replace only changed file chunks)
        logger.info(
            "Incremental update for %d changed files (full re-index for now)",
            len(changed_files),
        )
        return self.index_project(project_path, project_id)

    def _load_ignore_patterns(self, project_path: Path) -> list[str]:
        """Load ignore patterns from .contextignore, falling back to defaults."""
        contextignore = project_path / ".contextignore"
        if contextignore.exists():
            patterns = []
            for line in contextignore.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
            return patterns + DEFAULT_IGNORE_PATTERNS

        # Fall back to .gitignore + defaults
        gitignore = project_path / ".gitignore"
        if gitignore.exists():
            patterns = []
            for line in gitignore.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
            return patterns + DEFAULT_IGNORE_PATTERNS

        return DEFAULT_IGNORE_PATTERNS

    def _discover_files(
        self, project_path: Path, ignore_patterns: list[str]
    ) -> list[Path]:
        """Discover all indexable files in the project.

        Filters out symlinks, files exceeding size limit, and ignored patterns.
        """
        files = []
        for file_path in project_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip symlinks to prevent traversal outside project
            if file_path.is_symlink():
                logger.debug("Skipping symlink: %s", file_path)
                continue

            # Check against ignore patterns
            relative = file_path.relative_to(project_path)
            rel_str = str(relative)

            if self._is_ignored(rel_str, ignore_patterns):
                continue

            # Skip files exceeding size limit
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                    logger.info(
                        "Skipping file exceeding %d byte limit: %s",
                        MAX_FILE_SIZE_BYTES,
                        rel_str,
                    )
                    continue
            except OSError:
                continue

            # Check if any connector can handle this file
            if self._get_connector(file_path) is not None:
                files.append(file_path)

            # Enforce file count limit
            if len(files) >= MAX_FILE_COUNT:
                logger.warning(
                    "File count limit reached (%d). Remaining files skipped.",
                    MAX_FILE_COUNT,
                )
                break

        return sorted(files)

    def _is_ignored(self, relative_path: str, patterns: list[str]) -> bool:
        """Check if a file matches any ignore pattern."""
        for pattern in patterns:
            if fnmatch(relative_path, pattern):
                return True
            # Also check each path component for directory patterns
            parts = relative_path.split("/")
            for i, part in enumerate(parts):
                if fnmatch(part, pattern):
                    return True
                # Check partial paths
                partial = "/".join(parts[: i + 1])
                if fnmatch(partial, pattern) or fnmatch(partial + "/", pattern):
                    return True
        return False

    def _get_connector(self, file_path: Path) -> Optional[BaseConnector]:
        """Find the appropriate connector for a file."""
        for connector in self.connectors:
            if connector.can_handle(file_path):
                return connector
        return None

    def _file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        except OSError:
            return ""
        return hasher.hexdigest()

    def _generate_embeddings(self, chunks: list[ContentChunk]) -> np.ndarray:
        """Generate embeddings for all content chunks."""
        if not chunks:
            return np.zeros((0, self.embedding_dimensions))

        texts = [chunk.content[:MAX_EMBEDDING_INPUT_CHARS] for chunk in chunks]
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(embeddings)

    def _build_bm25_index(self, chunks: list[ContentChunk]) -> dict:
        """Build BM25 index data from content chunks.

        Returns serializable data that can be used to reconstruct
        the BM25 index at query time.
        """
        tokenized = [re.findall(r"\w+", chunk.content.lower()) for chunk in chunks]
        return {
            "tokenized_corpus": tokenized,
            "chunk_count": len(chunks),
        }
