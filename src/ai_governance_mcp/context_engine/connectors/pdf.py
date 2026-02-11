"""PDF connector for parsing PDF documents.

Extracts text content by page, preserving document structure.
Handles mixed text/image documents.
"""

import logging
from pathlib import Path

from .base import BaseConnector
from ..models import ContentChunk, FileMetadata

logger = logging.getLogger("ai_governance_mcp.context_engine.connectors.pdf")

# Maximum pages to process per PDF — prevents memory exhaustion on huge documents
MAX_PDF_PAGES = 500


class PDFConnector(BaseConnector):
    """Connector for PDF files."""

    def __init__(self) -> None:
        # L2: Track libraries separately for clearer diagnostics
        self._has_pymupdf = False
        self._has_pdfplumber = False
        try:
            import pymupdf  # noqa: F401

            self._has_pymupdf = True
        except ImportError:
            pass
        try:
            import pdfplumber  # noqa: F401

            self._has_pdfplumber = True
        except ImportError:
            pass

    @property
    def _pdf_available(self) -> bool:
        """Check if any PDF library is available."""
        return self._has_pymupdf or self._has_pdfplumber

    @property
    def supported_extensions(self) -> set[str]:
        return {".pdf"}

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf" and self._pdf_available

    def parse(
        self, file_path: Path, project_root: Path | None = None
    ) -> list[ContentChunk]:
        """Parse a PDF into page-based chunks."""
        if not self._pdf_available:
            return []

        # Compute display path (relative to project root when available)
        if project_root and file_path.is_relative_to(project_root):
            display_path = str(file_path.relative_to(project_root))
        else:
            display_path = str(file_path)

        chunks: list[ContentChunk] = []

        # Try pymupdf first, fall back to pdfplumber on any failure
        parsed = False

        if self._has_pymupdf:
            try:
                import pymupdf

                doc = pymupdf.open(str(file_path))
                try:
                    num_pages = min(len(doc), MAX_PDF_PAGES)
                    if len(doc) > MAX_PDF_PAGES:
                        logger.warning(
                            "PDF %s has %d pages, truncating to %d",
                            file_path.name,
                            len(doc),
                            MAX_PDF_PAGES,
                        )
                    for page_num in range(num_pages):
                        page = doc[page_num]
                        text = page.get_text()
                        if text.strip():
                            chunks.append(
                                ContentChunk(
                                    content=text,
                                    source_path=display_path,
                                    start_line=page_num + 1,
                                    end_line=page_num + 1,
                                    content_type="document",
                                    heading=f"Page {page_num + 1}",
                                )
                            )
                finally:
                    doc.close()
                parsed = True
            except Exception as e:
                logger.warning(
                    "pymupdf failed for %s, trying pdfplumber: %s", file_path.name, e
                )

        if not parsed and self._has_pdfplumber:
            try:
                import pdfplumber

                with pdfplumber.open(str(file_path)) as pdf:
                    num_pages = min(len(pdf.pages), MAX_PDF_PAGES)
                    if len(pdf.pages) > MAX_PDF_PAGES:
                        logger.warning(
                            "PDF %s has %d pages, truncating to %d",
                            file_path.name,
                            len(pdf.pages),
                            MAX_PDF_PAGES,
                        )
                    for page_num in range(num_pages):
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        if text and text.strip():
                            chunks.append(
                                ContentChunk(
                                    content=text,
                                    source_path=display_path,
                                    start_line=page_num + 1,
                                    end_line=page_num + 1,
                                    content_type="document",
                                    heading=f"Page {page_num + 1}",
                                )
                            )
            except Exception as e:
                logger.warning("Failed to parse PDF %s: %s", file_path.name, e)
                return []

        return chunks

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        stat = file_path.stat()
        return FileMetadata(
            path=str(file_path),
            content_type="document",
            language="pdf",
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
        )
