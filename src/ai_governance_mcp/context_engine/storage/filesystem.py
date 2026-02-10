"""Local filesystem storage backend for context engine indexes.

Stores index data in ~/.context-engine/indexes/{project-hash}/.
Default storage backend for individual developer use.

Security: Uses JSON (not pickle) for serialization. Validates project IDs
are hex-only to prevent path traversal. Checks path containment before
filesystem operations.
"""

import hashlib
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from .base import BaseStorage

logger = logging.getLogger("ai_governance_mcp.context_engine.storage.filesystem")

# Project IDs must be hex characters only (SHA-256 truncation output)
_PROJECT_ID_PATTERN = re.compile(r"^[0-9a-f]{1,64}$")

# Maximum JSON file size to load — prevents OOM on corrupted/malicious files
MAX_JSON_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


def _atomic_write_json(path: Path, data: Any, indent: int | None = None) -> None:
    """Write JSON atomically using tmp file + rename.

    Prevents corruption if process crashes mid-write.
    Atomic on POSIX (rename is atomic within same filesystem).
    """
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=indent)
        f.flush()
        os.fsync(f.fileno())
    tmp_path.replace(path)  # Atomic on POSIX


def _validate_project_id(project_id: str) -> None:
    """Validate project_id is hex-only to prevent path traversal.

    Raises:
        ValueError: If project_id contains non-hex characters.
    """
    if not _PROJECT_ID_PATTERN.match(project_id):
        raise ValueError("Invalid project_id: must be hex characters only")


class FilesystemStorage(BaseStorage):
    """Local filesystem storage for project indexes.

    Directory structure:
        {base_path}/
            {project_hash}/
                content_embeddings.npy
                bm25_index.json
                metadata.json
                file_manifest.json

    Security:
        - Project IDs validated as hex-only (prevents path traversal)
        - Path containment checked before write/delete operations
        - JSON serialization only (no pickle — prevents RCE)
        - NumPy loaded with allow_pickle=False
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize filesystem storage.

        Args:
            base_path: Root directory for indexes.
                       Defaults to ~/.context-engine/indexes/
        """
        if base_path is None:
            base_path = Path.home() / ".context-engine" / "indexes"
        self.base_path = base_path.resolve()
        self.base_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Ensure permissions even if directory pre-existed with weaker mode
        os.chmod(self.base_path, 0o700)
        # Clean up orphaned .tmp files from previous crashes
        self._cleanup_tmp_files()

    def _cleanup_tmp_files(self) -> None:
        """Remove orphaned .tmp files from previous crashes.

        Atomic write patterns (JSON and .npy) use tmp+rename. If the process
        is killed between write and rename, .tmp files are left behind.
        """
        try:
            for project_dir in self.base_path.iterdir():
                if not project_dir.is_dir() or project_dir.is_symlink():
                    continue
                for tmp_file in project_dir.glob("*.tmp*"):
                    try:
                        tmp_file.unlink()
                        logger.info("Cleaned up orphaned tmp file: %s", tmp_file.name)
                    except OSError:
                        pass
        except OSError:
            pass

    @staticmethod
    def project_id_from_path(project_path: Path) -> str:
        """Generate a project ID from an absolute path.

        Uses SHA-256 hash of the absolute path, truncated to 16 chars.
        Output is guaranteed hex-only.
        """
        abs_path = str(project_path.resolve())
        return hashlib.sha256(abs_path.encode()).hexdigest()[:16]

    def get_index_path(self, project_id: str) -> Path:
        """Get the storage path for a project's index.

        Validates project_id and checks path containment.
        """
        _validate_project_id(project_id)
        path = (self.base_path / project_id).resolve()
        if not path.is_relative_to(self.base_path):
            raise ValueError("Path traversal detected")
        return path

    def _ensure_dir(self, project_id: str) -> Path:
        path = self.get_index_path(project_id)
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Ensure permissions even if directory pre-existed with weaker mode
        os.chmod(path, 0o700)
        return path

    def save_embeddings(self, project_id: str, embeddings: np.ndarray) -> None:
        """Save embeddings atomically using tmp file + rename.

        Mirrors _atomic_write_json pattern to prevent corruption
        if the process is killed mid-write (e.g., Ctrl+C during indexing).
        """
        path = self._ensure_dir(project_id)
        final_path = path / "content_embeddings.npy"
        # np.save auto-appends .npy if missing, so use a .tmp base name
        tmp_path = path / "content_embeddings.tmp"
        np.save(tmp_path, embeddings)
        # np.save creates content_embeddings.tmp.npy — rename to final path
        actual_tmp = tmp_path.with_suffix(".tmp.npy")
        actual_tmp.replace(final_path)  # Atomic on POSIX

    def load_embeddings(self, project_id: str) -> np.ndarray | None:
        """Load embeddings with corrupt-file recovery.

        If the .npy file is corrupted (e.g., partial write from a crash),
        logs a warning and returns None so the caller can fall back to
        keyword-only search or trigger a re-index.
        """
        path = self.get_index_path(project_id) / "content_embeddings.npy"
        if path.exists():
            try:
                return np.load(path, allow_pickle=False)
            except Exception as e:
                logger.warning(
                    "Corrupt embeddings file for project %s, removing: %s",
                    project_id,
                    e,
                )
                try:
                    path.unlink()
                except OSError:
                    pass
                return None
        return None

    def save_bm25_index(self, project_id: str, index_data: Any) -> None:
        """Save BM25 index as JSON (not pickle — prevents RCE)."""
        path = self._ensure_dir(project_id)
        _atomic_write_json(path / "bm25_index.json", index_data)

    def load_bm25_index(self, project_id: str) -> Any | None:
        """Load BM25 index from JSON with corrupt-file recovery."""
        json_path = self.get_index_path(project_id) / "bm25_index.json"
        if json_path.exists():
            if json_path.stat().st_size > MAX_JSON_FILE_SIZE_BYTES:
                logger.warning(
                    "BM25 index exceeds %d byte limit, skipping: %s",
                    MAX_JSON_FILE_SIZE_BYTES,
                    project_id,
                )
                return None
            try:
                with open(json_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "Corrupt BM25 index for project %s, removing: %s",
                    project_id,
                    e,
                )
                try:
                    json_path.unlink()
                except OSError:
                    pass
                return None
        return None

    def save_metadata(self, project_id: str, metadata: dict) -> None:
        path = self._ensure_dir(project_id)
        _atomic_write_json(path / "metadata.json", metadata, indent=2)

    def load_metadata(self, project_id: str) -> dict | None:
        """Load metadata with corrupt-file recovery."""
        path = self.get_index_path(project_id) / "metadata.json"
        if path.exists():
            if path.stat().st_size > MAX_JSON_FILE_SIZE_BYTES:
                logger.warning(
                    "Metadata exceeds %d byte limit, skipping: %s",
                    MAX_JSON_FILE_SIZE_BYTES,
                    project_id,
                )
                return None
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "Corrupt metadata for project %s, removing: %s",
                    project_id,
                    e,
                )
                try:
                    path.unlink()
                except OSError:
                    pass
                return None
        return None

    def save_file_manifest(self, project_id: str, manifest: dict) -> None:
        path = self._ensure_dir(project_id)
        _atomic_write_json(path / "file_manifest.json", manifest, indent=2)

    def load_file_manifest(self, project_id: str) -> dict | None:
        """Load file manifest with corrupt-file recovery."""
        path = self.get_index_path(project_id) / "file_manifest.json"
        if path.exists():
            if path.stat().st_size > MAX_JSON_FILE_SIZE_BYTES:
                logger.warning(
                    "File manifest exceeds %d byte limit, skipping: %s",
                    MAX_JSON_FILE_SIZE_BYTES,
                    project_id,
                )
                return None
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "Corrupt file manifest for project %s, removing: %s",
                    project_id,
                    e,
                )
                try:
                    path.unlink()
                except OSError:
                    pass
                return None
        return None

    def project_exists(self, project_id: str) -> bool:
        _validate_project_id(project_id)
        path = self.get_index_path(project_id)
        return path.exists() and (path / "metadata.json").exists()

    def list_projects(self) -> list[str]:
        if not self.base_path.exists():
            return []
        return [
            d.name
            for d in self.base_path.iterdir()
            if d.is_dir()
            and not d.is_symlink()
            and _PROJECT_ID_PATTERN.match(d.name)
            and (d / "metadata.json").exists()
        ]

    def delete_project(self, project_id: str) -> None:
        """Delete a project's index from storage.

        Validates project_id and checks path containment before deletion.
        Refuses to follow symlinks to prevent deleting outside storage.
        """
        path = self.get_index_path(project_id)  # validates + containment check
        if path.exists():
            if path.is_symlink():
                # Remove the symlink itself, not its target
                path.unlink()
            else:
                shutil.rmtree(path)
