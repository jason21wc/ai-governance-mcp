"""Document connector for parsing text and markdown files.

Parses by document structure (headings, sections, paragraphs).
Extracts YAML frontmatter metadata for structured retrieval.
"""

import re
from datetime import date, datetime
from pathlib import Path

# safe_load only
import yaml  # nosec B506

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
            frontmatter = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError:
            return None, content
        if not isinstance(frontmatter, dict):
            return None, content
        frontmatter = DocumentConnector._normalize_frontmatter_values(frontmatter)
        return frontmatter, fm_match.group(2)

    @staticmethod
    def _normalize_frontmatter_values(obj):
        """Normalize YAML-parsed values to JSON-serializable types.

        yaml.safe_load converts date-like strings (2026-03-26) to
        datetime.date objects, which fail json.dump downstream.
        Normalize at the parse boundary, not the serialization layer.
        """
        if isinstance(obj, dict):
            return {
                k: DocumentConnector._normalize_frontmatter_values(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [DocumentConnector._normalize_frontmatter_values(v) for v in obj]
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        return obj

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

    # Minimum child headings for parent enrichment
    _MIN_CHILDREN_FOR_SUMMARY = 3

    @staticmethod
    def _clean_heading_text(text: str) -> str:
        """Strip markdown formatting and cap length for child heading summaries."""
        cleaned = text
        for delim in (" *(", " /"):
            idx = cleaned.find(delim)
            if idx > 0:
                cleaned = cleaned[:idx]
        cleaned = cleaned.replace("**", "").replace("*", "").replace("`", "")
        cleaned = cleaned.strip()
        if len(cleaned) > 60:
            cleaned = cleaned[:57] + "..."
        return cleaned

    @staticmethod
    def _get_child_headings(
        heading_entries: list[tuple[int, int, str]], parent_index: int
    ) -> list[str]:
        """Return cleaned child heading texts at parent_level+1 before next same-or-shallower heading."""
        parent_line, parent_level, _ = heading_entries[parent_index]
        child_level = parent_level + 1
        children: list[str] = []
        for entry in heading_entries[parent_index + 1 :]:
            _, level, raw_text = entry
            if level <= parent_level:
                break
            if level == child_level:
                children.append(DocumentConnector._clean_heading_text(raw_text))
        return children

    # Minimum section size for overlap (shorter sections get no overlap)
    _MIN_OVERLAP_LINES = 15
    # Number of overlap lines to carry from previous section
    _OVERLAP_LINES = 3

    def _parse_markdown(
        self, file_path: Path, content: str, display_path: str
    ) -> list[ContentChunk]:
        """Parse markdown by heading structure with max section size.

        Extracts YAML frontmatter and stores as structured metadata on chunks.
        Prepends frontmatter summary + heading breadcrumb to first chunk for
        embedding enrichment (~70% of LLM contextual retrieval benefit at zero cost).
        Adds overlap between chunks >15 lines for context continuity.
        """
        # Extract frontmatter before chunking
        frontmatter, content_without_fm = self._extract_frontmatter(content)
        fm_summary = self._frontmatter_summary(frontmatter) if frontmatter else ""

        lines = content_without_fm.split("\n")
        chunks: list[ContentChunk] = []
        section_lines: list[str] = []
        section_start = 1
        current_heading = ""
        parent_heading = ""  # Track parent heading for breadcrumbs
        prev_section_tail: list[str] = []  # Overlap lines from previous section
        heading_entries: list[tuple[int, int, str]] = []  # (line_num, level, text)
        chunk_heading_index: dict[int, int] = {}  # chunk_index -> heading_entries index

        def _build_breadcrumb() -> str:
            """Build heading breadcrumb for embedding enrichment.

            Format: file_path > Parent Heading > Current Heading
            Provides ~70% of LLM contextual retrieval benefit at zero cost.
            """
            parts = [display_path]
            if parent_heading:
                parts.append(parent_heading)
            if current_heading and current_heading != parent_heading:
                parts.append(current_heading)
            return " > ".join(parts)

        def _emit_section() -> None:
            """Emit accumulated section lines as chunk(s), splitting if oversized."""
            nonlocal section_lines, section_start, prev_section_tail
            is_first_batch = True
            while section_lines:
                batch = section_lines[: self._MAX_SECTION_LINES]

                # Add overlap from previous section if this section is long enough
                if prev_section_tail and len(batch) >= self._MIN_OVERLAP_LINES:
                    batch = prev_section_tail + batch
                    # Don't adjust section_start — overlap lines are context, not content

                chunk_content = "\n".join(batch)
                if chunk_content.strip():
                    # Build enrichment prefix for embedding
                    prefix_parts = []
                    if len(chunks) == 0 and fm_summary:
                        prefix_parts.append(fm_summary)
                    breadcrumb = _build_breadcrumb()
                    if breadcrumb:
                        prefix_parts.append(f"[{breadcrumb}]")

                    enriched_content = (
                        "\n".join(prefix_parts) + "\n" + chunk_content
                        if prefix_parts
                        else chunk_content
                    )

                    chunk_idx = len(chunks)
                    if is_first_batch and current_heading_idx >= 0:
                        chunk_heading_index[chunk_idx] = current_heading_idx
                    is_first_batch = False

                    chunks.append(
                        ContentChunk(
                            content=enriched_content,
                            source_path=display_path,
                            start_line=section_start,
                            end_line=section_start
                            + len(section_lines[: self._MAX_SECTION_LINES])
                            - 1,
                            content_type="document",
                            heading=current_heading,
                            frontmatter=frontmatter,
                        )
                    )

                # Save tail lines for next section's overlap
                original_batch = section_lines[: self._MAX_SECTION_LINES]
                if len(original_batch) >= self._MIN_OVERLAP_LINES:
                    prev_section_tail = original_batch[-self._OVERLAP_LINES :]
                else:
                    prev_section_tail = []

                section_start += len(section_lines[: self._MAX_SECTION_LINES])
                section_lines = section_lines[self._MAX_SECTION_LINES :]

        current_heading_idx: int = -1  # index into heading_entries for current section

        for i, line in enumerate(lines, start=1):
            # Detect heading boundaries
            if line.startswith("#") and section_lines:
                _emit_section()
                section_lines = [line]
                section_start = i
                # Track heading hierarchy for breadcrumbs
                heading_level = len(line) - len(line.lstrip("#"))
                new_heading = line.lstrip("#").strip()
                if heading_level <= 2:
                    parent_heading = new_heading
                current_heading = new_heading
                heading_entries.append((i, heading_level, new_heading))
                current_heading_idx = len(heading_entries) - 1
            else:
                if line.startswith("#") and not section_lines:
                    heading_level = len(line) - len(line.lstrip("#"))
                    new_heading = line.lstrip("#").strip()
                    if heading_level <= 2:
                        parent_heading = new_heading
                    current_heading = new_heading
                    heading_entries.append((i, heading_level, new_heading))
                    current_heading_idx = len(heading_entries) - 1
                section_lines.append(line)

        # Final section
        if section_lines:
            _emit_section()

        # Deferred enrichment: add child heading summaries to parent chunks
        # and position indicators to child chunk breadcrumbs
        self._enrich_chunks_with_heading_context(
            chunks, heading_entries, chunk_heading_index
        )

        return chunks

    def _enrich_chunks_with_heading_context(
        self,
        chunks: list[ContentChunk],
        heading_entries: list[tuple[int, int, str]],
        chunk_heading_index: dict[int, int],
    ) -> None:
        """Enrich parent chunks with child heading summaries and child chunks with position indicators."""
        # Relies on ascending chunk_idx order (parents before children) — do not reorder.
        for chunk_idx, heading_idx in chunk_heading_index.items():
            children = self._get_child_headings(heading_entries, heading_idx)
            if len(children) < self._MIN_CHILDREN_FOR_SUMMARY:
                continue

            chunk = chunks[chunk_idx]
            content_lines = chunk.content.split("\n")

            summary = f"[Contains {len(children)} sections: {' | '.join(children)}]"
            heading_text = heading_entries[heading_idx][2]

            # Search for the heading line, skipping prefix lines (breadcrumb/frontmatter)
            # to avoid matching overlap lines from previous section
            insert_pos = None
            for li in range(len(content_lines) - 1, -1, -1):
                stripped = content_lines[li].lstrip("#").strip()
                if stripped == heading_text:
                    insert_pos = li + 1
                    break

            if insert_pos is not None:
                content_lines.insert(insert_pos, summary)
            else:
                content_lines.append(summary)

            chunks[chunk_idx] = chunk.model_copy(
                update={"content": "\n".join(content_lines)}
            )

            # Add position indicators to child chunks
            _, parent_level, _ = heading_entries[heading_idx]
            child_level = parent_level + 1
            child_num = 0
            for entry_idx in range(heading_idx + 1, len(heading_entries)):
                _, level, _ = heading_entries[entry_idx]
                if level <= parent_level:
                    break
                if level == child_level:
                    child_num += 1
                    for ci, hi in chunk_heading_index.items():
                        if hi == entry_idx:
                            child_chunk = chunks[ci]
                            pos_tag = f"(section {child_num} of {len(children)})"
                            c_lines = child_chunk.content.split("\n")
                            # Find breadcrumb line and inject position tag before closing ]
                            for bli, bline in enumerate(c_lines):
                                if (
                                    bline.startswith("[")
                                    and " > " in bline
                                    and bline.rstrip().endswith("]")
                                ):
                                    c_lines[bli] = bline.rstrip()[:-1] + f" {pos_tag}]"
                                    break
                            updated = "\n".join(c_lines)
                            if updated != child_chunk.content:
                                chunks[ci] = child_chunk.model_copy(
                                    update={"content": updated}
                                )
                            break

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
