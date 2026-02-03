"""Image connector for extracting image metadata.

Extracts metadata (filename, dimensions, EXIF data, alt text) for
indexing. Image content analysis is handled by the multimodal-RAG
domain at retrieval time; this connector indexes metadata for
discoverability.
"""

import logging
from pathlib import Path

from .base import BaseConnector
from ..models import ContentChunk, FileMetadata

logger = logging.getLogger("ai_governance_mcp.context_engine.connectors.image")


class ImageConnector(BaseConnector):
    """Connector for image files — indexes metadata, not visual content."""

    SUPPORTED = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg"}

    def __init__(self) -> None:
        self._pillow_available = False
        try:
            from PIL import Image  # noqa: F401

            self._pillow_available = True
        except ImportError:
            pass

    @property
    def supported_extensions(self) -> set[str]:
        return self.SUPPORTED

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path) -> list[ContentChunk]:
        """Extract image metadata as an indexable chunk."""
        metadata_lines = [f"Image: {file_path.name}"]

        stat = file_path.stat()
        metadata_lines.append(f"Size: {stat.st_size} bytes")
        metadata_lines.append(f"Path: {file_path}")

        if self._pillow_available and file_path.suffix.lower() != ".svg":
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS

                with Image.open(file_path) as img:
                    metadata_lines.append(f"Dimensions: {img.width}x{img.height}")
                    metadata_lines.append(f"Format: {img.format}")
                    metadata_lines.append(f"Mode: {img.mode}")

                    # Extract EXIF data if available
                    exif_data = img.getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name in {
                                "ImageDescription",
                                "Artist",
                                "Copyright",
                                "DateTime",
                                "Software",
                            }:
                                metadata_lines.append(f"{tag_name}: {value}")
            except Exception as e:
                logger.warning(
                    "Failed to extract image metadata from %s: %s", file_path, e
                )

        metadata_text = "\n".join(metadata_lines)
        return [
            ContentChunk(
                content=metadata_text,
                source_path=str(file_path),
                start_line=0,
                end_line=0,
                content_type="image",
                heading=f"Image metadata: {file_path.name}",
            )
        ]

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        stat = file_path.stat()
        return FileMetadata(
            path=str(file_path),
            content_type="image",
            language=file_path.suffix.lstrip("."),
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
        )
