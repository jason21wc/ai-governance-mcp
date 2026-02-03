"""Base connector interface for content parsing.

All source connectors implement this interface to parse project content
into indexable chunks. Each connector handles a specific content type
(code, documents, data, images, PDFs) and produces ContentChunk objects.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ContentChunk, FileMetadata


class BaseConnector(ABC):
    """Abstract base class for source connectors.

    Connectors parse project files into indexable content chunks.
    Each chunk should be self-contained enough for standalone comprehension
    while being focused enough for precise retrieval.
    """

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this connector can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if this connector can parse the file.
        """

    @abstractmethod
    def parse(self, file_path: Path) -> list[ContentChunk]:
        """Parse a file into indexable content chunks.

        Args:
            file_path: Path to the file to parse.

        Returns:
            List of content chunks extracted from the file.
        """

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from a file.

        Args:
            file_path: Path to the file.

        Returns:
            File metadata including path, type, size, modification time.
        """

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """File extensions this connector handles (e.g., {'.py', '.js'})."""
