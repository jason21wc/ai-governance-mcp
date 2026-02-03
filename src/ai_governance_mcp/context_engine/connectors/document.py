"""Document connector for parsing text and markdown files.

Parses by document structure (headings, sections, paragraphs).
Extracts metadata including title, headers, and front matter.
"""

from pathlib import Path

from .base import BaseConnector
from ..models import ContentChunk, FileMetadata


class DocumentConnector(BaseConnector):
    """Connector for markdown and plain text files."""

    SUPPORTED = {".md", ".markdown", ".txt", ".rst", ".adoc", ".org"}

    @property
    def supported_extensions(self) -> set[str]:
        return self.SUPPORTED

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path) -> list[ContentChunk]:
        """Parse a document into section-based chunks."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        if not content.strip():
            return []

        if file_path.suffix.lower() in {".md", ".markdown"}:
            return self._parse_markdown(file_path, content)
        return self._parse_plain_text(file_path, content)

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        stat = file_path.stat()
        return FileMetadata(
            path=str(file_path),
            content_type="document",
            language=file_path.suffix.lstrip("."),
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
        )

    def _parse_markdown(self, file_path: Path, content: str) -> list[ContentChunk]:
        """Parse markdown by heading structure."""
        lines = content.split("\n")
        chunks: list[ContentChunk] = []
        section_lines: list[str] = []
        section_start = 1
        current_heading = ""

        for i, line in enumerate(lines, start=1):
            # Detect heading boundaries
            if line.startswith("#") and section_lines:
                chunk_content = "\n".join(section_lines)
                if chunk_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=chunk_content,
                            source_path=str(file_path),
                            start_line=section_start,
                            end_line=i - 1,
                            content_type="document",
                            heading=current_heading,
                        )
                    )
                section_lines = [line]
                section_start = i
                current_heading = line.lstrip("#").strip()
            else:
                if line.startswith("#") and not section_lines:
                    current_heading = line.lstrip("#").strip()
                section_lines.append(line)

        # Final section
        if section_lines:
            chunk_content = "\n".join(section_lines)
            if chunk_content.strip():
                chunks.append(
                    ContentChunk(
                        content=chunk_content,
                        source_path=str(file_path),
                        start_line=section_start,
                        end_line=len(lines),
                        content_type="document",
                        heading=current_heading,
                    )
                )

        return chunks

    def _parse_plain_text(self, file_path: Path, content: str) -> list[ContentChunk]:
        """Parse plain text into paragraph-based chunks."""
        lines = content.split("\n")
        chunks: list[ContentChunk] = []
        para_lines: list[str] = []
        para_start = 1
        target_size = 30  # lines per chunk

        for i, line in enumerate(lines, start=1):
            para_lines.append(line)

            is_boundary = (
                len(para_lines) >= target_size and line.strip() == ""
            ) or i == len(lines)

            if is_boundary:
                chunk_content = "\n".join(para_lines)
                if chunk_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=chunk_content,
                            source_path=str(file_path),
                            start_line=para_start,
                            end_line=i,
                            content_type="document",
                        )
                    )
                para_lines = []
                para_start = i + 1

        return chunks
