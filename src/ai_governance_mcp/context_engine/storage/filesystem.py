"""Local filesystem storage backend for context engine indexes.

Stores index data in ~/.context-engine/indexes/{project-hash}/.
Default storage backend for individual developer use.

Security: Uses JSON (not pickle) for serialization. Validates project IDs
are hex-only to prevent path traversal. Checks path containment before
filesystem operations.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional

import numpy as np

from .base import BaseStorage

# Project IDs must be hex characters only (SHA-256 truncation output)
_PROJECT_ID_PATTERN = re.compile(r"^[0-9a-f]{1,64}$")


def _validate_project_id(project_id: str) -> None:
    """Validate project_id is hex-only to prevent path traversal.

    Raises:
        ValueError: If project_id contains non-hex characters.
    """
    if not _PROJECT_ID_PATTERN.match(project_id):
        raise ValueError(
            f"Invalid project_id: must be hex characters only, got {project_id!r}"
        )


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

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """Initialize filesystem storage.

        Args:
            base_path: Root directory for indexes.
                       Defaults to ~/.context-engine/indexes/
        """
        if base_path is None:
            base_path = Path.home() / ".context-engine" / "indexes"
        self.base_path = base_path.resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

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
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_embeddings(self, project_id: str, embeddings: np.ndarray) -> None:
        path = self._ensure_dir(project_id)
        np.save(path / "content_embeddings.npy", embeddings)

    def load_embeddings(self, project_id: str) -> Optional[np.ndarray]:
        path = self.get_index_path(project_id) / "content_embeddings.npy"
        if path.exists():
            return np.load(path, allow_pickle=False)
        return None

    def save_bm25_index(self, project_id: str, index_data: Any) -> None:
        """Save BM25 index as JSON (not pickle — prevents RCE)."""
        path = self._ensure_dir(project_id)
        with open(path / "bm25_index.json", "w") as f:
            json.dump(index_data, f)

    def load_bm25_index(self, project_id: str) -> Optional[Any]:
        """Load BM25 index from JSON."""
        # Check for new JSON format first, fall back to legacy pkl
        json_path = self.get_index_path(project_id) / "bm25_index.json"
        if json_path.exists():
            with open(json_path) as f:
                return json.load(f)
        return None

    def save_metadata(self, project_id: str, metadata: dict) -> None:
        path = self._ensure_dir(project_id)
        with open(path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self, project_id: str) -> Optional[dict]:
        path = self.get_index_path(project_id) / "metadata.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def save_file_manifest(self, project_id: str, manifest: dict) -> None:
        path = self._ensure_dir(project_id)
        with open(path / "file_manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

    def load_file_manifest(self, project_id: str) -> Optional[dict]:
        path = self.get_index_path(project_id) / "file_manifest.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
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
            and _PROJECT_ID_PATTERN.match(d.name)
            and (d / "metadata.json").exists()
        ]

    def delete_project(self, project_id: str) -> None:
        """Delete a project's index from storage.

        Validates project_id and checks path containment before deletion.
        """
        path = self.get_index_path(project_id)  # validates + containment check
        if path.exists():
            shutil.rmtree(path)
