"""PDF connector for parsing PDF documents.

Extracts text content by page, preserving document structure.
Handles mixed text/image documents.
"""

import logging
from pathlib import Path

from .base import BaseConnector
from ..models import ContentChunk, FileMetadata

logger = logging.getLogger("ai_governance_mcp.context_engine.connectors.pdf")


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

        try:
            import pymupdf

            doc = pymupdf.open(str(file_path))
            try:
                for page_num in range(len(doc)):
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
        except ImportError:
            try:
                import pdfplumber

                with pdfplumber.open(str(file_path)) as pdf:
                    for page_num, page in enumerate(pdf.pages):
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
                logger.warning(
                    "Failed to parse PDF with pdfplumber %s: %s", file_path, e
                )
                return []
        except Exception as e:
            logger.warning("Failed to parse PDF with pymupdf %s: %s", file_path, e)
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
