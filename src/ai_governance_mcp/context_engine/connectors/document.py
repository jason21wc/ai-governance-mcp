"""Document connector for parsing text and markdown files.

Parses by document structure (headings, sections, paragraphs).
Extracts YAML frontmatter metadata for structured retrieval.
"""

import re
from pathlib import Path

import yaml  # nosec B506 — safe_load only

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

    @staticmethod
    def _extract_frontmatter(content: str) -> tuple[dict | None, str]:
        """Extract YAML frontmatter from markdown content.

        Returns (frontmatter_dict, content_without_frontmatter).
        Uses yaml.safe_load() exclusively for security.
        Returns (None, original_content) if no valid frontmatter.
        """
        fm_match = re.match(r"^---\n(.*?\n)---\n(.*)", content, re.DOTALL)
        if not fm_match:
            return None, content
        try:
            frontmatter = yaml.safe_load(fm_match.group(1))  # nosec B506
        except yaml.YAMLError:
            return None, content
        if not isinstance(frontmatter, dict):
            return None, content
        return frontmatter, fm_match.group(2)

    @staticmethod
    def _frontmatter_summary(fm: dict) -> str:
        """Create a compact text summary of frontmatter for embedding enrichment.

        Prepended to the first chunk's content before embedding to improve
        metadata-aware retrieval. ~70% of LLM contextual retrieval benefit
        at zero cost (per Anthropic Contextual Retrieval research).
        """
        parts = []
        if "tags" in fm and isinstance(fm["tags"], list):
            parts.append(f"[tags: {', '.join(str(t) for t in fm['tags'][:8])}]")
        if "status" in fm:
            parts.append(f"[status: {fm['status']}]")
        if "maturity" in fm:
            parts.append(f"[maturity: {fm['maturity']}]")
        if "domain" in fm:
            parts.append(f"[domain: {fm['domain']}]")
        if "title" in fm:
            parts.append(f"[title: {fm['title']}]")
        if "entry_type" in fm:
            parts.append(f"[type: {fm['entry_type']}]")
        return " ".join(parts)

    def _parse_markdown(
        self, file_path: Path, content: str, display_path: str
    ) -> list[ContentChunk]:
        """Parse markdown by heading structure with max section size.

        Extracts YAML frontmatter and stores as structured metadata on chunks.
        Prepends frontmatter summary to first chunk for embedding enrichment.
        """
        # Extract frontmatter before chunking
        frontmatter, content_without_fm = self._extract_frontmatter(content)
        fm_summary = self._frontmatter_summary(frontmatter) if frontmatter else ""

        lines = content_without_fm.split("\n")
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
                    # Prepend frontmatter summary to first chunk for embedding enrichment
                    enriched_content = chunk_content
                    if len(chunks) == 0 and fm_summary:
                        enriched_content = fm_summary + "\n" + chunk_content
                    chunks.append(
                        ContentChunk(
                            content=enriched_content,
                            source_path=display_path,
                            start_line=section_start,
                            end_line=section_start + len(batch) - 1,
                            content_type="document",
                            heading=current_heading,
                            frontmatter=frontmatter,
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
