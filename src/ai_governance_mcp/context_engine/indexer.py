"""Core indexing orchestrator for the Context Engine.

Coordinates source connectors to parse project files into content chunks,
generates embeddings, and builds the hybrid search index (BM25 + semantic).
"""

import hashlib
import logging
import re
import threading
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

# Maximum total chunks across all files — prevents OOM during embedding
MAX_TOTAL_CHUNKS = 100_000

# Maximum content per chunk (chars) — prevents memory amplification
# Chunks exceeding this are truncated (content is preserved in source files)
MAX_CHUNK_CONTENT_CHARS = 10_000

# Maximum content length for embedding input (chars)
# BGE-small handles ~512 tokens (~2048 chars); larger models can handle more
MAX_EMBEDDING_INPUT_CHARS = 2048

# Batch size for embedding generation — limits peak memory
EMBEDDING_BATCH_SIZE = 1000

# Vetted embedding models — prevents RCE via malicious HuggingFace pickle payloads.
# Set AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true to bypass (at your own risk).
ALLOWED_EMBEDDING_MODELS = {
    "BAAI/bge-small-en-v1.5",
    "BAAI/bge-base-en-v1.5",
    "BAAI/bge-large-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-MiniLM-L12-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "jinaai/jina-embeddings-v2-small-en",
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
    # Secret/credential files — prevent accidental indexing
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    ".netrc",
    "credentials.json",
    "service_account.json",
    "id_rsa*",
    "id_ed25519*",
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
        self._model_lock = threading.Lock()  # Thread-safe lazy model loading

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

        Thread-safe: uses a lock to prevent duplicate model loading when
        concurrent queries race on a cold start. Uses safetensors format
        (prevents pickle RCE) and blocks remote code execution.
        """
        if self._embedding_model is not None:
            return self._embedding_model

        with self._model_lock:
            # Double-check after acquiring lock
            if self._embedding_model is not None:
                return self._embedding_model

            import os

            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install 'ai-governance-mcp[context-engine]'"
                )

            allow_custom = os.environ.get(
                "AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS", ""
            ).lower() in ("true", "1")

            if (
                not allow_custom
                and self.embedding_model_name not in ALLOWED_EMBEDDING_MODELS
            ):
                raise ValueError(
                    f"Model '{self.embedding_model_name}' is not in the allowed list. "
                    f"Allowed models: {sorted(ALLOWED_EMBEDDING_MODELS)}."
                )

            if allow_custom:
                logger.error(
                    "SECURITY: Embedding model allowlist bypassed via "
                    "AI_CONTEXT_ENGINE_ALLOW_CUSTOM_MODELS=true. "
                    "Model '%s' not verified for safety. "
                    "This may enable remote code execution if the model "
                    "contains malicious payloads. Only use trusted models.",
                    self.embedding_model_name,
                )

            logger.info(
                "Loading embedding model: %s (this may take a moment on first use)",
                self.embedding_model_name,
            )
            self._embedding_model = SentenceTransformer(
                self.embedding_model_name,
                trust_remote_code=False,
                model_kwargs={"use_safetensors": True},
            )
            logger.info("Embedding model loaded successfully")
        return self._embedding_model

    def index_project(
        self,
        project_path: Path,
        project_id: str,
        index_mode: str = "ondemand",
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

                # Truncate oversized chunk content to prevent memory amplification
                for chunk in chunks:
                    if len(chunk.content) > MAX_CHUNK_CONTENT_CHARS:
                        chunk.content = chunk.content[:MAX_CHUNK_CONTENT_CHARS]

                all_chunks.extend(chunks)
                all_metadata.append(metadata)

                # Enforce total chunk limit
                if len(all_chunks) >= MAX_TOTAL_CHUNKS:
                    logger.warning(
                        "Chunk limit reached (%d). Remaining files skipped.",
                        MAX_TOTAL_CHUNKS,
                    )
                    break
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
            schema_version=1,
            chunking_version=self._get_chunking_version(),
        )

        # Persist to storage — ordered for crash safety:
        # chunks → embeddings → bm25 → metadata → manifest LAST
        # Manifest is the "commit record": if crash occurs before manifest
        # write, next load sees old manifest and triggers full re-index.
        self.storage.save_chunks(
            project_id,
            project_index.model_dump()["chunks"],
        )
        self.storage.save_embeddings(project_id, embeddings)
        self.storage.save_bm25_index(project_id, bm25_data)

        full_dump = project_index.model_dump()
        full_dump.pop("chunks", None)
        full_dump.pop("files", None)  # Already stored in file_manifest.json
        self.storage.save_metadata(project_id, full_dump)

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
        """Update the index incrementally in response to file changes.

        Only re-parses and re-embeds changed/added files. Reuses existing
        chunks and embeddings for unchanged files. Falls back to full
        re-index when incremental state is unavailable.

        Concurrency note: Called from two contexts:
        (a) directly via reindex_project — caller is responsible for locking
        (b) via watcher callback in on_change — expensive work runs OUTSIDE
            _index_lock, then brief atomic swap INSIDE the lock with
            generation tracking (see project_manager.py)

        Args:
            project_path: Root directory of the project.
            project_id: Unique identifier for this project.
            changed_files: List of files that changed (hint, not exclusive).

        Returns:
            Updated ProjectIndex.
        """
        # Load existing state
        existing_metadata = self.storage.load_metadata(project_id)
        if existing_metadata is None:
            logger.info("No existing index found, performing full index")
            return self.index_project(project_path, project_id)

        index_mode = existing_metadata.get("index_mode", "ondemand")

        # Check chunking_version — mismatch means parser strategy changed
        # (e.g., line-based → tree-sitter); must full re-index to avoid
        # mixed chunking strategies degrading search quality.
        stored_chunking_version = existing_metadata.get(
            "chunking_version", "line-based-v1"
        )
        current_chunking_version = self._get_chunking_version()
        if stored_chunking_version != current_chunking_version:
            logger.info(
                "Chunking version changed (%s → %s), performing full re-index",
                stored_chunking_version,
                current_chunking_version,
            )
            return self.index_project(project_path, project_id, index_mode)

        # Load manifest, chunks, and embeddings
        manifest = self.storage.load_file_manifest(project_id)
        if manifest is None:
            logger.info("No file manifest found, falling back to full re-index")
            return self.index_project(project_path, project_id, index_mode)

        chunks_data = self.storage.load_chunks(project_id)
        if chunks_data is None:
            logger.info("No chunks found, falling back to full re-index")
            return self.index_project(project_path, project_id, index_mode)

        old_embeddings = self.storage.load_embeddings(project_id)
        if old_embeddings is None:
            logger.info("No embeddings found, falling back to full re-index")
            return self.index_project(project_path, project_id, index_mode)

        # Discover current files
        ignore_patterns = self.load_ignore_patterns(project_path)
        current_files = self._discover_files(project_path, ignore_patterns)
        current_hashes = {}
        for f in current_files:
            current_hashes[str(f)] = self._file_hash(f)

        # Classify files
        unchanged, modified, added, deleted = self._classify_files(
            manifest, current_hashes, current_files
        )

        # No-change fast path
        if not modified and not added and not deleted:
            logger.info("No file changes detected, reusing existing index")
            # Reconstruct index from stored data
            return self._reconstruct_index(
                project_id,
                project_path,
                existing_metadata,
                chunks_data,
                index_mode,
            )

        logger.info(
            "Incremental update: %d unchanged, %d modified, %d added, %d deleted",
            len(unchanged),
            len(modified),
            len(added),
            len(deleted),
        )

        # Collect unchanged chunks and their old embedding vectors (aligned lists)
        unchanged_chunks, unchanged_vectors = self._collect_unchanged_chunks(
            chunks_data, unchanged, old_embeddings
        )

        # Parse changed files (MODIFIED + ADDED only)
        new_chunks: list[ContentChunk] = []
        new_metadata: list[FileMetadata] = []
        files_to_parse = modified + added

        for file_path in files_to_parse:
            connector = self._get_connector(file_path)
            if connector is None:
                continue
            try:
                chunks = connector.parse(file_path, project_root=project_path)
                fm = connector.extract_metadata(file_path)
                fm.content_hash = current_hashes.get(str(file_path), "")
                fm.chunk_count = len(chunks)
                for chunk in chunks:
                    if len(chunk.content) > MAX_CHUNK_CONTENT_CHARS:
                        chunk.content = chunk.content[:MAX_CHUNK_CONTENT_CHARS]
                new_chunks.extend(chunks)
                new_metadata.append(fm)
            except Exception as e:
                logger.warning("Failed to parse %s: %s", file_path, e)
                continue

        # Combine: unchanged first, then new
        all_chunks = unchanged_chunks + new_chunks
        n_unchanged = len(unchanged_chunks)

        # Reassign sequential embedding IDs
        for i, chunk in enumerate(all_chunks):
            chunk.embedding_id = i

        # Build embedding matrix — reuse old vectors for unchanged chunks
        embeddings = self._build_incremental_embeddings(
            all_chunks, n_unchanged, unchanged_vectors
        )

        # Post-save validation
        if len(embeddings) != len(all_chunks):
            logger.warning(
                "Embedding/chunk count mismatch (%d vs %d) after incremental build. "
                "Falling back to full re-index.",
                len(embeddings),
                len(all_chunks),
            )
            return self.index_project(project_path, project_id, index_mode)

        # Rebuild BM25 from scratch (fast, <100ms)
        bm25_data = self._build_bm25_index(all_chunks)

        # Build full file metadata list for manifest
        all_file_metadata = []
        # Unchanged files: keep original metadata
        for file_path_str in unchanged:
            if file_path_str in manifest:
                fm_data = manifest[file_path_str]
                all_file_metadata.append(FileMetadata(**fm_data))
        # New/modified files
        all_file_metadata.extend(new_metadata)

        # Create updated index
        now = datetime.now(timezone.utc).isoformat()
        project_index = ProjectIndex(
            project_id=project_id,
            project_path=str(project_path),
            chunks=all_chunks,
            files=all_file_metadata,
            created_at=existing_metadata.get("created_at", now),
            updated_at=now,
            embedding_model=self.embedding_model_name,
            total_chunks=len(all_chunks),
            total_files=len(all_file_metadata),
            index_mode=index_mode,
            schema_version=1,
            chunking_version=current_chunking_version,
        )

        # Atomic save — ordered: chunks → embeddings → bm25 → metadata → manifest LAST
        self.storage.save_chunks(project_id, project_index.model_dump()["chunks"])
        self.storage.save_embeddings(project_id, embeddings)
        self.storage.save_bm25_index(project_id, bm25_data)

        full_dump = project_index.model_dump()
        full_dump.pop("chunks", None)
        full_dump.pop("files", None)
        self.storage.save_metadata(project_id, full_dump)

        # Manifest LAST — serves as the "commit record"
        self.storage.save_file_manifest(
            project_id,
            {fm.path: fm.model_dump() for fm in all_file_metadata},
        )

        logger.info(
            "Incremental update complete: %d total chunks (%d reused, %d new)",
            len(all_chunks),
            n_unchanged,
            len(new_chunks),
        )
        return project_index

    def _get_chunking_version(self) -> str:
        """Return current chunking strategy identifier.

        Changes when the parser strategy changes (e.g., line-based → tree-sitter).
        Incremental indexer detects mismatch and forces full re-index.
        """
        # Check if tree-sitter is available via the code connector
        code_connector = next(
            (c for c in self.connectors if isinstance(c, CodeConnector)), None
        )
        if code_connector and code_connector._tree_sitter_available:
            return "tree-sitter-v2"
        return "line-based-v1"

    def _classify_files(
        self,
        manifest: dict,
        current_hashes: dict[str, str],
        current_files: list[Path],
    ) -> tuple[list[str], list[Path], list[Path], list[str]]:
        """Classify files as UNCHANGED, MODIFIED, ADDED, or DELETED.

        Args:
            manifest: Stored file manifest {abs_path: metadata_dict}.
            current_hashes: {abs_path_str: sha256_hash} for current files.
            current_files: List of currently discovered file paths.

        Returns:
            (unchanged_paths, modified_paths, added_paths, deleted_paths)
            unchanged and deleted are string paths, modified and added are Path objects.
        """
        current_path_strs = {str(f) for f in current_files}
        manifest_paths = set(manifest.keys())

        unchanged = []
        modified = []
        added = []

        for file_path in current_files:
            path_str = str(file_path)
            if path_str in manifest_paths:
                stored_hash = manifest[path_str].get("content_hash")
                current_hash = current_hashes.get(path_str, "")
                # content_hash=None means legacy index — treat as MODIFIED
                if stored_hash is not None and stored_hash == current_hash:
                    unchanged.append(path_str)
                else:
                    modified.append(file_path)
            else:
                added.append(file_path)

        deleted = [p for p in manifest_paths if p not in current_path_strs]

        return unchanged, modified, added, deleted

    def _collect_unchanged_chunks(
        self,
        chunks_data: list[dict],
        unchanged_files: list[str],
        old_embeddings: np.ndarray,
    ) -> tuple[list[ContentChunk], list[np.ndarray]]:
        """Collect chunks from unchanged files with their embedding vectors.

        Returns chunks and vectors as aligned lists (same order).
        Vector at index i corresponds to chunk at index i.

        Args:
            chunks_data: Raw chunk dicts from storage.
            unchanged_files: List of unchanged file absolute paths.
            old_embeddings: Full embedding matrix from previous index.

        Returns:
            (chunks, vectors) — aligned lists of unchanged chunks and their vectors.
        """
        unchanged_set = set(unchanged_files)
        chunks = []
        vectors: list[np.ndarray] = []

        for chunk_dict in chunks_data:
            source = chunk_dict.get("source_path", "")
            # Match by source_path — chunks use relative paths while manifest
            # uses absolute paths. Try both matching strategies.
            is_unchanged = False
            for uf in unchanged_set:
                if uf.endswith(source) or source == uf:
                    is_unchanged = True
                    break

            if is_unchanged:
                chunk = ContentChunk(**chunk_dict)
                old_id = chunk.embedding_id
                if (
                    old_id is not None
                    and old_embeddings is not None
                    and 0 <= old_id < len(old_embeddings)
                ):
                    vectors.append(old_embeddings[old_id].copy())
                    chunks.append(chunk)
                # Skip chunks without valid embedding (shouldn't happen, but safe)

        return chunks, vectors

    def _build_incremental_embeddings(
        self,
        all_chunks: list[ContentChunk],
        n_unchanged: int,
        unchanged_vectors: list[np.ndarray],
    ) -> np.ndarray:
        """Build embedding matrix reusing old vectors for unchanged chunks.

        Unchanged vectors are placed at the start (positions 0..n_unchanged-1),
        new embeddings are generated for the rest.

        Args:
            all_chunks: Combined chunk list (unchanged first, then new).
            n_unchanged: Number of unchanged chunks at start of all_chunks.
            unchanged_vectors: Pre-extracted vectors aligned with unchanged chunks.

        Returns:
            New embedding matrix with shape (len(all_chunks), dimensions).
        """
        if not all_chunks:
            return np.zeros((0, self.embedding_dimensions))

        total = len(all_chunks)
        result = np.zeros((total, self.embedding_dimensions), dtype=np.float32)

        # Reuse old vectors for unchanged chunks (positions 0..n_unchanged-1)
        for i, vec in enumerate(unchanged_vectors):
            if i < n_unchanged:
                result[i] = vec

        # Generate new embeddings only for new/modified chunks
        if n_unchanged < total:
            new_chunks = all_chunks[n_unchanged:]
            new_embeddings = self._generate_embeddings(new_chunks)
            result[n_unchanged:] = new_embeddings

        logger.info(
            "Embeddings: %d reused, %d generated",
            len(unchanged_vectors),
            total - n_unchanged,
        )
        return result

    def _reconstruct_index(
        self,
        project_id: str,
        project_path: Path,
        metadata: dict,
        chunks_data: list[dict],
        index_mode: str,
    ) -> ProjectIndex:
        """Reconstruct a ProjectIndex from stored data without re-indexing."""
        return ProjectIndex(
            project_id=project_id,
            project_path=str(project_path),
            chunks=[ContentChunk(**cd) for cd in chunks_data],
            created_at=metadata.get("created_at", ""),
            updated_at=metadata.get("updated_at", ""),
            embedding_model=metadata.get("embedding_model", self.embedding_model_name),
            total_chunks=metadata.get("total_chunks", len(chunks_data)),
            total_files=metadata.get("total_files", 0),
            index_mode=index_mode,
            schema_version=metadata.get("schema_version", 1),
            chunking_version=metadata.get("chunking_version", "line-based-v1"),
        )

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
            try:
                # Guard against oversized ignore files (1MB limit)
                if source.stat().st_size > 1_048_576:
                    logger.warning(
                        "Ignore file %s exceeds 1MB, using defaults only",
                        source.name,
                    )
                else:
                    for line in source.read_text().splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except OSError as e:
                logger.warning("Failed to read %s: %s", source.name, e)

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
        """Generate embeddings in batches to limit peak memory.

        Instead of passing all texts to encode() at once (which can spike
        memory for large projects), processes in batches of EMBEDDING_BATCH_SIZE.
        """
        if not chunks:
            return np.zeros((0, self.embedding_dimensions))

        texts = []
        for chunk in chunks:
            if chunk.import_context:
                text = chunk.import_context + "\n" + chunk.content
            else:
                text = chunk.content
            texts.append(text[:MAX_EMBEDDING_INPUT_CHARS])

        # Batch to limit peak memory
        all_embeddings = []
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            batch_embeddings = self.embedding_model.encode(
                batch,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            all_embeddings.append(np.array(batch_embeddings))

        return (
            np.vstack(all_embeddings)
            if all_embeddings
            else np.zeros((0, self.embedding_dimensions))
        )

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
