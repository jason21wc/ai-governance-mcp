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

    def parse(
        self, file_path: Path, project_root: Path | None = None
    ) -> list[ContentChunk]:
        """Parse a document into section-based chunks."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        if not content.strip():
            return []

        # Compute display path (relative to project root when available)
        if project_root and file_path.is_relative_to(project_root):
            display_path = str(file_path.relative_to(project_root))
        else:
            display_path = str(file_path)

        if file_path.suffix.lower() in {".md", ".markdown"}:
            return self._parse_markdown(file_path, content, display_path)
        return self._parse_plain_text(file_path, content, display_path)

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        stat = file_path.stat()
        return FileMetadata(
            path=str(file_path),
            content_type="document",
            language=file_path.suffix.lstrip("."),
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
        )

    # Maximum lines per markdown section before force-splitting
    _MAX_SECTION_LINES = 200

    def _parse_markdown(
        self, file_path: Path, content: str, display_path: str
    ) -> list[ContentChunk]:
        """Parse markdown by heading structure with max section size."""
        lines = content.split("\n")
        chunks: list[ContentChunk] = []
        section_lines: list[str] = []
        section_start = 1
        current_heading = ""

        def _emit_section() -> None:
            """Emit accumulated section lines as chunk(s), splitting if oversized."""
            nonlocal section_lines, section_start
            while section_lines:
                batch = section_lines[: self._MAX_SECTION_LINES]
                chunk_content = "\n".join(batch)
                if chunk_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=chunk_content,
                            source_path=display_path,
                            start_line=section_start,
                            end_line=section_start + len(batch) - 1,
                            content_type="document",
                            heading=current_heading,
                        )
                    )
                section_start += len(batch)
                section_lines = section_lines[len(batch) :]

        for i, line in enumerate(lines, start=1):
            # Detect heading boundaries
            if line.startswith("#") and section_lines:
                _emit_section()
                section_lines = [line]
                section_start = i
                current_heading = line.lstrip("#").strip()
            else:
                if line.startswith("#") and not section_lines:
                    current_heading = line.lstrip("#").strip()
                section_lines.append(line)

        # Final section
        if section_lines:
            _emit_section()

        return chunks

    def _parse_plain_text(
        self, file_path: Path, content: str, display_path: str
    ) -> list[ContentChunk]:
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

            # Hard split at max section size to prevent single massive chunks
            force_split = len(para_lines) >= self._MAX_SECTION_LINES

            if is_boundary or force_split:
                chunk_content = "\n".join(para_lines)
                if chunk_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=chunk_content,
                            source_path=display_path,
                            start_line=para_start,
                            end_line=i,
                            content_type="document",
                        )
                    )
                para_lines = []
                para_start = i + 1

        return chunks
