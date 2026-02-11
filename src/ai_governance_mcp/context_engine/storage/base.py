"""Base storage interface for context engine indexes.

Storage backends handle persistence of index data (embeddings,
BM25 index, metadata, file manifests) for each project.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np


class BaseStorage(ABC):
    """Abstract base class for index storage backends."""

    @abstractmethod
    def save_embeddings(self, project_id: str, embeddings: np.ndarray) -> None:
        """Save content embeddings for a project.

        Args:
            project_id: Unique project identifier (hash of absolute path).
            embeddings: NumPy array of content chunk embeddings.
        """

    @abstractmethod
    def load_embeddings(self, project_id: str) -> np.ndarray | None:
        """Load content embeddings for a project.

        Returns:
            NumPy array of embeddings, or None if not found.
        """

    @abstractmethod
    def save_bm25_index(self, project_id: str, index_data: Any) -> None:
        """Save BM25 keyword index for a project."""

    @abstractmethod
    def load_bm25_index(self, project_id: str) -> Any | None:
        """Load BM25 keyword index for a project."""

    @abstractmethod
    def save_metadata(self, project_id: str, metadata: dict) -> None:
        """Save project metadata (config, stats)."""

    @abstractmethod
    def load_metadata(self, project_id: str) -> dict | None:
        """Load project metadata."""

    @abstractmethod
    def save_chunks(self, project_id: str, chunks: list[dict]) -> None:
        """Save content chunks for a project (separate from metadata)."""

    @abstractmethod
    def load_chunks(self, project_id: str) -> list[dict] | None:
        """Load content chunks for a project.

        Returns:
            List of chunk dicts, or None if not found.
        """

    @abstractmethod
    def save_file_manifest(self, project_id: str, manifest: dict) -> None:
        """Save file manifest (indexed files with hashes for change detection)."""

    @abstractmethod
    def load_file_manifest(self, project_id: str) -> dict | None:
        """Load file manifest."""

    @abstractmethod
    def project_exists(self, project_id: str) -> bool:
        """Check if a project index exists in storage."""

    @abstractmethod
    def list_projects(self) -> list[str]:
        """List all project IDs in storage."""

    @abstractmethod
    def delete_project(self, project_id: str) -> None:
        """Delete a project's index from storage."""

    @abstractmethod
    def get_index_path(self, project_id: str) -> Path:
        """Get the storage path for a project's index."""
