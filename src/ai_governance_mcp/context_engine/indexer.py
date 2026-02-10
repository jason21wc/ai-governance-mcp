"""Core indexing orchestrator for the Context Engine.

Coordinates source connectors to parse project files into content chunks,
generates embeddings, and builds the hybrid search index (BM25 + semantic).
"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pathspec

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

# Vetted embedding models — prevents RCE via malicious HuggingFace pickle payloads.
# Set AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true to bypass (at your own risk).
ALLOWED_EMBEDDING_MODELS = {
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "BAAI/bge-large-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-MiniLM-L12-v2",
    "sentence-transformers/all-mpnet-base-v2",
}

# Default ignore patterns (gitignore syntax via pathspec)
# With pathspec, `foo/` matches the directory and all contents — no need for `foo/**`
DEFAULT_IGNORE_PATTERNS = [
    ".git/",
    "__pycache__/",
    "*.pyc",
    "node_modules/",
    ".venv/",
    "venv/",
    ".env*",
    "*.egg-info/",
    "dist/",
    "build/",
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
        """Lazy-load the embedding model with safety enforcement.

        Uses safetensors format (prevents pickle RCE) and blocks remote code execution.
        Model must be in ALLOWED_EMBEDDING_MODELS unless custom models are explicitly enabled.
        """
        if self._embedding_model is None:
            import os

            from sentence_transformers import SentenceTransformer

            allow_custom = os.environ.get(
                "AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS", ""
            ).lower() in ("true", "1")

            if (
                not allow_custom
                and self.embedding_model_name not in ALLOWED_EMBEDDING_MODELS
            ):
                raise ValueError(
                    f"Model '{self.embedding_model_name}' is not in the allowed list. "
                    f"Allowed models: {sorted(ALLOWED_EMBEDDING_MODELS)}. "
                    "Set AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true to bypass."
                )

            self._embedding_model = SentenceTransformer(
                self.embedding_model_name,
                trust_remote_code=False,
                model_kwargs={"use_safetensors": True},
            )
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
        ignore_patterns = self.load_ignore_patterns(project_path)

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
                chunks = connector.parse(file_path, project_root=project_path)
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
    ) -> ProjectIndex:
        """Update the index in response to file changes.

        Note: Currently performs a full re-index. True incremental update
        (replacing only changed file chunks) is not yet implemented.

        Args:
            project_path: Root directory of the project.
            project_id: Unique identifier for this project.
            changed_files: List of files that changed.

        Returns:
            Updated ProjectIndex (always succeeds via full re-index fallback).
        """
        # Load existing index
        existing = self.storage.load_metadata(project_id)
        if existing is None:
            logger.info("No existing index found, performing full index")
            return self.index_project(project_path, project_id)

        # TODO: Implement true incremental update (replace only changed file chunks).
        # Currently falls back to full re-index for all changes.
        logger.warning(
            "incremental_update performs full re-index (true incremental not yet "
            "implemented). %d files changed.",
            len(changed_files),
        )
        return self.index_project(project_path, project_id)

    def load_ignore_patterns(self, project_path: Path) -> pathspec.GitIgnoreSpec:
        """Load ignore patterns from .contextignore/.gitignore + defaults.

        Returns a compiled GitIgnoreSpec for efficient matching.
        Defaults come first so user patterns (including negation) take precedence.
        """
        # Defaults first — user patterns can override with !pattern negation
        patterns = list(DEFAULT_IGNORE_PATTERNS)

        contextignore = project_path / ".contextignore"
        gitignore = project_path / ".gitignore"

        source = contextignore if contextignore.exists() else gitignore
        if source.exists():
            for line in source.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)

        return pathspec.GitIgnoreSpec.from_lines(patterns)

    def _discover_files(
        self, project_path: Path, ignore_spec: pathspec.GitIgnoreSpec
    ) -> list[Path]:
        """Discover all indexable files in the project.

        Filters out symlinks, files exceeding size limit, and ignored patterns.
        """
        files = []
        # Note: rglob does NOT follow directory symlinks (Python 3.4+, bpo-26012).
        # File symlinks are filtered below. This is safe against symlink traversal attacks.
        for file_path in project_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip symlinks to prevent traversal outside project
            if file_path.is_symlink():
                logger.debug("Skipping symlink: %s", file_path)
                continue

            # Check against ignore patterns (gitignore semantics via pathspec)
            rel_str = str(file_path.relative_to(project_path))

            if ignore_spec.match_file(rel_str):
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

    def _get_connector(self, file_path: Path) -> BaseConnector | None:
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
